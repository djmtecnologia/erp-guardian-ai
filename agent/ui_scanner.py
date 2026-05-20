import os
import sys
import time
import requests
from typing import Dict, Any

# Carregamento seguro da biblioteca de Windows
PYWINAUTO_AVAILABLE = False
try:
    if os.name == 'nt':
        import pywinauto
        from pywinauto.application import Application
        PYWINAUTO_AVAILABLE = True
except ImportError:
    pass

class ERPUIWatcher:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url

    def run_scan_workflow(self, task_id: int, exe_path: str, username: str, password: str, exe_version: str = None, gef_grupo: str = None, gef_empresa: str = None, gef_filial: str = None):
        """Executa a automação local no Windows usando pywinauto."""
        if not PYWINAUTO_AVAILABLE:
            print("[UI-Scanner] ❌ ERRO: pywinauto não instalado ou não executado em sistema Windows.")
            self._update_status(task_id, "failed")
            return

        print(f"\n[UI-Scanner] 🚀 Iniciando Varredura para Tarefa #{task_id}")
        print(f"[UI-Scanner] Executável: {exe_path}")

        try:
            self._update_status(task_id, "running")

            # 1. Iniciar o ERP
            print("[UI-Scanner] Abrindo aplicação...")
            app = Application(backend="win32").start(exe_path)
            time.sleep(3) # Tempo para a tela de login abrir

            # 2. Conectar com a tela de login (janela ativa no topo)
            dlg = app.top_window()
            print(f"[UI-Scanner] Conectado à janela de Login: '{dlg.window_text()}'")

            # 3. Mapear controles de input de Delphi clássico
            descendants = dlg.descendants()
            edits = [c for c in descendants if "Edit" in c.friendly_class_name() or "TEdit" in c.class_name()]
            buttons = [
                c for c in descendants 
                if "Button" in c.friendly_class_name() 
                or c.class_name() in ["TButton", "TBitBtn", "TSpeedButton", "TPanel", "TLabel"]
                or any(x in c.window_text().upper() for x in ["LOGIN", "ENTRAR", "CONFIRMA", "ACESSAR"])
            ]

            print(f"[UI-Scanner] Encontrados {len(edits)} campos de texto e {len(buttons)} botões.")

            # Digitar credenciais nos inputs correspondentes com tratamento de exceção
            if len(edits) >= 2:
                print(f"[UI-Scanner] Preenchendo usuário: {username}")
                try:
                    edits[0].set_text(username)
                except Exception:
                    try:
                        edits[0].type_keys(username)
                    except Exception:
                        pass
                print("[UI-Scanner] Preenchendo senha...")
                try:
                    edits[1].set_text(password)
                except Exception:
                    try:
                        edits[1].type_keys(password)
                    except Exception:
                        pass
            elif len(edits) == 1:
                # Caso haja apenas um campo visível ou focado
                try:
                    edits[0].set_text(username)
                except Exception:
                    try:
                        edits[0].type_keys(username)
                    except Exception:
                        pass
                dlg.type_keys("{TAB}")
                time.sleep(0.5)
                print(f"[UI-Scanner] Preenchendo senha...")
                try:
                    edits[1].set_text(password)
                except Exception:
                    try:
                        edits[1].type_keys(password)
                    except Exception:
                        pass

            # Localizar botão de confirmação (OK / Entrar / Confirmar / Acessar)
            btn_login = None
            for b in buttons:
                txt = b.window_text().upper()
                if any(x in txt for x in ["OK", "ENTRAR", "LOGIN", "CONFIRMAR", "GRAVAR", "ACESSAR", "CONECTAR", "VALIDAR", "CONFIRMA", "SIM", "PROSSEGUIR"]):
                    btn_login = b
                    break

            if btn_login:
                print(f"[UI-Scanner] Clicando no botão de Login identificado: '{btn_login.window_text()}'")
                btn_login.click()
            else:
                print("[UI-Scanner] Botão de login não identificado por texto. Pressionando ENTER para efetuar o login...")
                dlg.type_keys("{ENTER}")

            # --- LOOP DE DESCARTE E CONFIGURAÇÃO DE DIÁLOGOS INTERMEDIÁRIOS ---
            # Permite faturar as telas de Versão e GEF (Grupo/Empresa/Filial) sequencialmente
            for step in range(3):
                time.sleep(3)
                try:
                    top_dlg = app.top_window()
                    title = top_dlg.window_text().upper()
                    print(f"[UI-Scanner] [Passo {step+1}] Checando diálogo ativo: '{top_dlg.window_text()}'")
                    
                    if not any(x in title for x in ["VERSÃO", "VERSAO", "SELECIONAR", "EMPRESA", "FILIAL", "CONFIRMA", "ENTRAR", "SELEÇÃO", "SELECAO", "GEF", "CONECTA", "LOGIN"]):
                        print("[UI-Scanner] Janela Principal detectada no topo. Parando loop de diálogos.")
                        break
                        
                    # 1. Tratamento da Janela de Seleção de Versão
                    if any(x in title for x in ["VERSÃO", "VERSAO", "VERSÃO DO EXE"]):
                        if exe_version:
                            print(f"[UI-Scanner] Preenchendo versão selecionada: '{exe_version}'")
                            try:
                                v_edits = [c for c in top_dlg.descendants() if "Edit" in c.friendly_class_name() or "TEdit" in c.class_name()]
                                if v_edits:
                                    v_edits[0].set_text(exe_version)
                                else:
                                    top_dlg.type_keys(exe_version)
                            except Exception:
                                top_dlg.type_keys(exe_version)
                        else:
                            print("[UI-Scanner] Versão não especificada. Aceitando padrão.")
                        
                        top_dlg.type_keys("{ENTER}")
                        
                    # 2. Tratamento da Janela de Seleção de GEF (Grupo / Empresa / Filial)
                    elif any(x in title for x in ["GEF", "EMPRESA", "FILIAL", "GRUPO"]):
                        print(f"[UI-Scanner] Configurando contexto GEF (Grupo: {gef_grupo}, Empresa: {gef_empresa}, Filial: {gef_filial})")
                        try:
                            g_edits = [c for c in top_dlg.descendants() if "Edit" in c.friendly_class_name() or "TEdit" in c.class_name()]
                            if g_edits and len(g_edits) >= 3:
                                if gef_grupo: g_edits[0].set_text(gef_grupo)
                                if gef_empresa: g_edits[1].set_text(gef_empresa)
                                if gef_filial: g_edits[2].set_text(gef_filial)
                            else:
                                if gef_grupo:
                                    top_dlg.type_keys(gef_grupo)
                                    time.sleep(0.3)
                                    top_dlg.type_keys("{TAB}")
                                if gef_empresa:
                                    top_dlg.type_keys(gef_empresa)
                                    time.sleep(0.3)
                                    top_dlg.type_keys("{TAB}")
                                if gef_filial:
                                    top_dlg.type_keys(gef_filial)
                                    time.sleep(0.3)
                        except Exception as e:
                            print(f"[UI-Scanner] Falha na digitação estruturada de GEF: {e}")
                        
                        top_dlg.type_keys("{ENTER}")
                        
                    else:
                        print("[UI-Scanner] Confirmando diálogo intermediário genérico pós-login...")
                        top_dlg.type_keys("{ENTER}")
                except Exception as ex:
                    print(f"[UI-Scanner] Aviso durante loop de diálogos: {ex}")
                    break

            time.sleep(6) # Aguardar faturamento do menu principal do ERP

            # 4. Mapear Menu Principal e Telas
            main_dlg = app.top_window()
            screen_title = main_dlg.window_text()
            print(f"[UI-Scanner] 🎉 Login efetuado! Conectado na Janela Principal: '{screen_title}'")

            # Varredura completa da árvore de menus/botões
            print("[UI-Scanner] Iniciando engenharia reversa de controles do ERP...")
            main_controls = main_dlg.descendants()
            
            ui_tree = []
            for c in main_controls:
                try:
                    ui_tree.append({
                        "class_name": c.class_name(),
                        "friendly_class": c.friendly_class_name(),
                        "text": c.window_text(),
                        "rectangle": f"L{c.rectangle().left},T{c.rectangle().top},R{c.rectangle().right},B{c.rectangle().bottom}",
                        "enabled": c.is_enabled(),
                        "visible": c.is_visible()
                    })
                except Exception:
                    continue

            # 5. Enviar árvore de controle para a base de conhecimento na nuvem com o respectivo ID da tarefa
            print("[UI-Scanner] Enviando árvore de interface mapeada para a Vercel...")
            payload = {
                "task_id": task_id,
                "screen_name": screen_title or "ERP Main Window",
                "controls": ui_tree
            }
            requests.post(f"{self.backend_url}/api/ui-scan/result", json=payload)

            # Fechar aplicação
            print("[UI-Scanner] Fechando aplicação...")
            app.kill()

            self._update_status(task_id, "completed")
            print(f"[UI-Scanner] ✅ Varredura finalizada com sucesso!")

        except Exception as e:
            print(f"[UI-Scanner] ❌ Falha catastrófica na varredura: {e}")
            self._update_status(task_id, "failed")

    def _update_status(self, task_id: int, status: str):
        try:
            requests.post(f"{self.backend_url}/api/ui-scan/update", json={
                "task_id": task_id,
                "status": status
            })
        except Exception as err:
            print(f"[UI-Scanner] Erro ao reportar status para nuvem: {err}")
