import os
import sys
import time
import requests
from typing import Dict, Any, List

# Carregamento seguro da biblioteca de Windows
PYWINAUTO_AVAILABLE = False
try:
    if os.name == 'nt':
        import pywinauto
        from pywinauto.application import Application
        from pywinauto import findwindows
        PYWINAUTO_AVAILABLE = True
except ImportError:
    pass

# Limite máximo de telas a mapear por execução (evita loops infinitos em ERPs muito grandes)
MAX_SCREENS = 150

class ERPUIWatcher:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url

    # ------------------------------------------------------------------
    # PONTO DE ENTRADA PRINCIPAL
    # ------------------------------------------------------------------
    def run_scan_workflow(self, task_id: int, exe_path: str, username: str, password: str,
                          exe_version: str = None, gef_grupo: str = None,
                          gef_empresa: str = None, gef_filial: str = None):
        """Executa a automação completa de varredura de telas no Windows."""
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
            time.sleep(3)

            # 2. Conectar com a tela de login
            dlg = app.top_window()
            print(f"[UI-Scanner] Conectado à janela de Login: '{dlg.window_text()}'")

            # 3. Mapear e preencher credenciais
            self._do_login(app, dlg, username, password)

            # 4. Loop de diálogos intermediários (Versão, GEF, etc.)
            self._handle_post_login_dialogs(app, exe_version, gef_grupo, gef_empresa, gef_filial)

            time.sleep(5)

            # 5. Janela principal obtida
            main_dlg = app.top_window()
            screen_title = main_dlg.window_text() or "ERP Main Window"
            print(f"[UI-Scanner] 🎉 Login efetuado! Janela Principal: '{screen_title}'")

            # 5.1 Aguarda menus do ERP carregarem completamente antes da engenharia reversa
            print("[UI-Scanner] ⏳ Aguardando 10s para os menus do ERP carregarem completamente...")
            time.sleep(10)

            # 6. Mapear e salvar a janela principal
            self._capture_and_send(task_id, app, main_dlg, screen_title)

            # 7. Enumerar e navegar pelos menus
            print("[UI-Scanner] 🔍 Iniciando varredura completa dos módulos via menu principal...")
            screens_mapped = 1
            menu_items = self._enumerate_menu_items(app, main_dlg)
            print(f"[UI-Scanner] {len(menu_items)} itens de menu encontrados para exploração.")

            for item_info in menu_items:
                if screens_mapped >= MAX_SCREENS:
                    print(f"[UI-Scanner] ⚠️ Limite de {MAX_SCREENS} telas atingido. Encerrando varredura.")
                    break

                item_name = item_info.get("text", "?")
                print(f"[UI-Scanner] ▶ Clicando no menu: '{item_name}'")

                try:
                    opened = self._click_menu_and_capture(
                        task_id, app, main_dlg, item_info
                    )
                    if opened:
                        screens_mapped += 1
                        print(f"[UI-Scanner] ✔ Tela '{item_name}' mapeada. Total: {screens_mapped}")
                except Exception as e:
                    print(f"[UI-Scanner] ⚠ Erro ao processar menu '{item_name}': {e}")
                    # Recuperar foco na janela principal
                    try:
                        main_dlg.set_focus()
                    except Exception:
                        pass
                    time.sleep(1)

            print(f"\n[UI-Scanner] 📊 Varredura completa: {screens_mapped} telas mapeadas.")
            app.kill()
            self._update_status(task_id, "completed")
            print("[UI-Scanner] ✅ Varredura finalizada com sucesso!")

        except Exception as e:
            print(f"[UI-Scanner] ❌ Falha catastrófica na varredura: {e}")
            import traceback; traceback.print_exc()
            self._update_status(task_id, "failed")

    # ------------------------------------------------------------------
    # LOGIN
    # ------------------------------------------------------------------
    def _do_login(self, app, dlg, username: str, password: str):
        descendants = dlg.descendants()
        edits = [c for c in descendants if "Edit" in c.friendly_class_name() or "TEdit" in c.class_name()]
        buttons = [
            c for c in descendants
            if "Button" in c.friendly_class_name()
            or c.class_name() in ["TButton", "TBitBtn", "TSpeedButton"]
            or any(x in c.window_text().upper() for x in ["LOGIN", "ENTRAR", "CONFIRMA", "ACESSAR"])
        ]
        print(f"[UI-Scanner] Encontrados {len(edits)} campos de texto e {len(buttons)} botões.")

        def _type(ctrl, text):
            try:
                ctrl.set_text(text)
            except Exception:
                try:
                    ctrl.type_keys(text, with_spaces=True)
                except Exception:
                    pass

        if len(edits) >= 2:
            print(f"[UI-Scanner] Preenchendo usuário: {username}")
            _type(edits[0], username)
            print("[UI-Scanner] Preenchendo senha...")
            _type(edits[1], password)
        elif len(edits) == 1:
            _type(edits[0], username)
            dlg.type_keys("{TAB}")
            time.sleep(0.5)
            print("[UI-Scanner] Preenchendo senha...")
            dlg.type_keys(password, with_spaces=True)

        btn_login = None
        for b in buttons:
            txt = b.window_text().upper()
            if any(x in txt for x in ["OK", "ENTRAR", "LOGIN", "CONFIRMAR", "GRAVAR",
                                        "ACESSAR", "CONECTAR", "VALIDAR", "CONFIRMA", "SIM", "PROSSEGUIR"]):
                btn_login = b
                break

        if btn_login:
            print(f"[UI-Scanner] Clicando no botão: '{btn_login.window_text()}'")
            btn_login.click()
        else:
            print("[UI-Scanner] Botão de login não identificado. Pressionando ENTER...")
            dlg.type_keys("{ENTER}")

    # ------------------------------------------------------------------
    # LOOP DE DIÁLOGOS PÓS-LOGIN (Versão, GEF, etc.)
    # ------------------------------------------------------------------
    def _handle_post_login_dialogs(self, app, exe_version, gef_grupo, gef_empresa, gef_filial):
        for step in range(5):
            time.sleep(3)
            try:
                top_dlg = app.top_window()
                title = top_dlg.window_text().upper()
                print(f"[UI-Scanner] [Passo {step+1}] Checando diálogo ativo: '{top_dlg.window_text()}'")

                if not any(x in title for x in ["VERSÃO", "VERSAO", "SELECIONAR", "EMPRESA",
                                                  "FILIAL", "CONFIRMA", "ENTRAR", "SELEÇÃO",
                                                  "SELECAO", "GEF", "CONECTA", "LOGIN"]):
                    print("[UI-Scanner] Janela Principal detectada no topo. Parando loop de diálogos.")
                    break

                if any(x in title for x in ["VERSÃO", "VERSAO"]):
                    if exe_version:
                        v_edits = [c for c in top_dlg.descendants()
                                   if "Edit" in c.friendly_class_name() or "TEdit" in c.class_name()]
                        if v_edits:
                            v_edits[0].set_text(exe_version)
                    top_dlg.type_keys("{ENTER}")

                elif any(x in title for x in ["GEF", "EMPRESA", "FILIAL", "GRUPO"]):
                    try:
                        g_edits = [c for c in top_dlg.descendants()
                                   if "Edit" in c.friendly_class_name() or "TEdit" in c.class_name()]
                        if len(g_edits) >= 3:
                            if gef_grupo:   g_edits[0].set_text(gef_grupo)
                            if gef_empresa: g_edits[1].set_text(gef_empresa)
                            if gef_filial:  g_edits[2].set_text(gef_filial)
                    except Exception as e:
                        print(f"[UI-Scanner] Falha na digitação de GEF: {e}")
                    top_dlg.type_keys("{ENTER}")

                else:
                    print("[UI-Scanner] Confirmando diálogo intermediário genérico...")
                    top_dlg.type_keys("{ENTER}")

            except Exception as ex:
                print(f"[UI-Scanner] Aviso no loop de diálogos: {ex}")
                break

    # ------------------------------------------------------------------
    # ENUMERAÇÃO DE ITENS DE MENU
    # ------------------------------------------------------------------
    def _enumerate_menu_items(self, app, main_dlg) -> List[Dict]:
        """
        Enumeração dos itens clicáveis do menu principal do ERP.
        Tenta 3 estratégias em ordem:
          1. pywinauto MenuWrapper (mais preciso)
          2. Descendentes com classes TMenuItem / TMainMenu
          3. Descendentes do tipo "MenuItem" genérico
        """
        items = []
        seen_texts = set()

        # Estratégia 1: MenuWrapper nativo do pywinauto
        try:
            menu = main_dlg.menu()
            if menu:
                for i, item in enumerate(menu.items()):
                    try:
                        txt = item.text().strip().replace("&", "")
                        if txt and txt not in seen_texts and txt not in ("-", ""):
                            seen_texts.add(txt)
                            # Sub-itens (segundo nível – itens folha que abrem telas)
                            try:
                                sub_items = item.sub_menu().items()
                                for j, sub in enumerate(sub_items):
                                    sub_txt = sub.text().strip().replace("&", "")
                                    if sub_txt and sub_txt not in ("-", "") and sub_txt not in seen_texts:
                                        seen_texts.add(sub_txt)
                                        items.append({
                                            "strategy": "menu_wrapper",
                                            "level": 2,
                                            "parent_index": i,
                                            "index": j,
                                            "text": sub_txt,
                                            "parent_text": txt
                                        })
                            except Exception:
                                # Item sem sub-menu = folha direta
                                items.append({
                                    "strategy": "menu_wrapper",
                                    "level": 1,
                                    "parent_index": i,
                                    "index": -1,
                                    "text": txt,
                                    "parent_text": None
                                })
                    except Exception:
                        continue
                if items:
                    return items
        except Exception as e:
            print(f"[UI-Scanner] MenuWrapper indisponível: {e}")

        # Estratégia 2: Descendentes com classes Delphi de menu
        try:
            descendants = main_dlg.descendants()
            menu_classes = {"TMenuItem", "TMainMenu", "TPopupMenu", "TMenuBar"}
            for c in descendants:
                try:
                    cls = c.class_name()
                    txt = c.window_text().strip().replace("&", "")
                    if cls in menu_classes and txt and txt not in seen_texts and txt not in ("-",):
                        seen_texts.add(txt)
                        items.append({
                            "strategy": "descendant_class",
                            "level": 1,
                            "text": txt,
                            "ctrl": c
                        })
                except Exception:
                    continue
            if items:
                return items
        except Exception as e:
            print(f"[UI-Scanner] Estratégia de descendentes de classe falhou: {e}")

        # Estratégia 3: Qualquer descendente do tipo MenuItem
        try:
            descendants = main_dlg.descendants()
            for c in descendants:
                try:
                    if "MenuItem" in c.friendly_class_name() or "MenuItem" in c.class_name():
                        txt = c.window_text().strip().replace("&", "")
                        if txt and txt not in seen_texts and txt not in ("-",):
                            seen_texts.add(txt)
                            items.append({
                                "strategy": "friendly_class",
                                "level": 1,
                                "text": txt,
                                "ctrl": c
                            })
                except Exception:
                    continue
        except Exception as e:
            print(f"[UI-Scanner] Estratégia friendly_class falhou: {e}")

        return items

    # ------------------------------------------------------------------
    # CLICAR NO MENU E CAPTURAR TELA
    # ------------------------------------------------------------------
    def _click_menu_and_capture(self, task_id: int, app, main_dlg, item_info: Dict) -> bool:
        """
        Clica num item de menu, aguarda abertura de nova janela e captura os controles.
        Retorna True se uma nova tela foi aberta e enviada ao backend.
        """
        windows_before = set(w.handle for w in app.windows())

        strategy = item_info.get("strategy")
        item_text = item_info.get("text", "")

        # --- Click via MenuWrapper ---
        if strategy == "menu_wrapper":
            try:
                menu = main_dlg.menu()
                if item_info["level"] == 1:
                    menu.item_by_index(item_info["parent_index"]).click()
                else:
                    # Abre sub-menu pai e clica no sub-item
                    parent = menu.item_by_index(item_info["parent_index"])
                    parent.click()
                    time.sleep(0.5)
                    sub = parent.sub_menu().item_by_index(item_info["index"])
                    sub.click()
            except Exception as e:
                print(f"[UI-Scanner]   MenuWrapper click falhou: {e}")
                return False

        # --- Click direto no controle ---
        elif "ctrl" in item_info:
            try:
                item_info["ctrl"].click()
            except Exception:
                try:
                    item_info["ctrl"].double_click()
                except Exception as e:
                    print(f"[UI-Scanner]   Clique no controle falhou: {e}")
                    return False
        else:
            return False

        # Aguardar nova janela abrir
        time.sleep(2)

        # Verificar se nova janela apareceu
        windows_after = set(w.handle for w in app.windows())
        new_handles = windows_after - windows_before

        if not new_handles:
            # Sem nova janela – menu pode ter aberto sub-menu em vez de tela
            return False

        # Capturar a nova tela
        for handle in new_handles:
            try:
                new_dlg = app.window(handle=handle)
                title = new_dlg.window_text() or item_text
                print(f"[UI-Scanner]   📋 Nova tela detectada: '{title}'")
                self._capture_and_send(task_id, app, new_dlg, title)

                # Fechar a tela para voltar ao menu principal
                try:
                    new_dlg.type_keys("{ESC}")
                    time.sleep(0.5)
                    if new_dlg.exists():
                        new_dlg.close()
                except Exception:
                    try:
                        new_dlg.close()
                    except Exception:
                        pass

                time.sleep(1)
                # Restaurar foco na janela principal
                try:
                    main_dlg.set_focus()
                except Exception:
                    pass
            except Exception as e:
                print(f"[UI-Scanner]   Erro ao capturar nova janela: {e}")

        return len(new_handles) > 0

    # ------------------------------------------------------------------
    # CAPTURAR ÁRVORE DE CONTROLES E ENVIAR
    # ------------------------------------------------------------------
    def _find_local_source_code(self, screen_name: str) -> str:
        """
        Busca recursivamente no diretório de código local (configurado via LOCAL_VCS_PATH)
        por arquivos Delphi (.pas, .dfm) correspondentes à tela mapeada.
        """
        import os
        import re
        
        local_path = os.getenv("LOCAL_VCS_PATH", "./")
        if not os.path.exists(local_path):
            return ""
            
        # Normaliza palavras-chave da tela para buscar arquivos
        screen_slug = re.sub(r'[^a-zA-Z0-9]', '', screen_name.lower())
        screen_words = [w for w in re.findall(r'[a-zA-Z]{3,}', screen_slug) if w not in ('tela', 'form', 'frm', 'unit', 'main', 'window')]
        
        if not screen_words:
            # Caso o título seja genérico (ex: "Geral"), tenta pegar o slug inteiro
            screen_words = [screen_slug] if len(screen_slug) > 2 else []
            
        if not screen_words:
            return ""
            
        print(f"[UI-Scanner] 🔍 Buscando código fonte local pareado em '{local_path}' para a tela '{screen_name}' (Palavras: {screen_words})...")
        
        matched_content = []
        
        # Faz uma busca de arquivos na pasta de fontes (.pas, .dfm)
        for root, _, files in os.walk(local_path):
            for file in files:
                if file.lower().endswith(('.pas', '.dfm')):
                    file_lower = file.lower()
                    
                    # Match 1: O nome do arquivo contém o termo chave da tela (ex: uconfirm.pas para "Confirm")
                    is_match = any(w in file_lower for w in screen_words)
                    
                    # Match 2: Caso o nome da tela ou das palavras-chave estejam declarados dentro do arquivo
                    if not is_match and len(matched_content) < 3: # limite para não sobrecarregar
                        try:
                            file_path = os.path.join(root, file)
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                head = f.read(2000)
                                if any(w in head.lower() for w in screen_words):
                                    is_match = True
                        except Exception:
                            pass
                            
                    if is_match:
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                matched_content.append(f"--- ARQUIVO FONTE: {file} ---\n{content}")
                                print(f"[UI-Scanner] 🎯 Fonte local pareado com sucesso: {file} ({len(content)} bytes)")
                        except Exception as e:
                            print(f"[UI-Scanner] Erro ao ler fonte local {file}: {e}")
                            
            if len(matched_content) >= 3: # Limita a até 3 fontes por tela
                break
                
        return "\n\n".join(matched_content)

    def _capture_and_send(self, task_id: int, app, dlg, screen_name: str):
        """Coleta a árvore de controles da janela e envia para o backend."""
        try:
            descendants = dlg.descendants()
            ui_tree = []
            for c in descendants:
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

            # Tenta buscar os arquivos Delphi correspondentes localmente para enviar de forma híbrida
            local_code = ""
            try:
                local_code = self._find_local_source_code(screen_name)
            except Exception as le:
                print(f"[UI-Scanner] ⚠️ Falha na busca de código fonte local: {le}")

            payload = {
                "task_id": task_id,
                "screen_name": screen_name,
                "controls": ui_tree
            }
            
            if local_code:
                payload["local_source_code"] = local_code

            resp = requests.post(f"{self.backend_url}/api/ui-scan/result", json=payload, timeout=30)
            if resp.status_code == 200:
                print(f"[UI-Scanner]   ✅ '{screen_name}' enviada ({len(ui_tree)} controles). Código pareado: {len(local_code) > 0}")
            else:
                print(f"[UI-Scanner]   ⚠ Erro ao enviar '{screen_name}': HTTP {resp.status_code}")
        except Exception as e:
            print(f"[UI-Scanner]   ❌ Falha ao capturar '{screen_name}': {e}")

    # ------------------------------------------------------------------
    # ATUALIZAR STATUS
    # ------------------------------------------------------------------
    def _update_status(self, task_id: int, status: str):
        try:
            requests.post(f"{self.backend_url}/api/ui-scan/update", json={
                "task_id": task_id,
                "status": status
            }, timeout=10)
        except Exception as err:
            print(f"[UI-Scanner] Erro ao reportar status: {err}")
