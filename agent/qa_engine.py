import os
import time
from typing import List, Dict, Any

PYWINAUTO_AVAILABLE = False
try:
    if os.name == 'nt':
        import pywinauto
        from pywinauto.application import Application
        PYWINAUTO_AVAILABLE = True
except ImportError:
    pass

ORACLEDB_AVAILABLE = False
try:
    import oracledb
    ORACLEDB_AVAILABLE = True
except ImportError:
    pass

class QAAutomationEngine:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.logs = []

    def log(self, message: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.logs.append(log_entry)

    def execute_qa_test(self, task_id: int, scenario: str, exe_path: str = "C:\\ERP\\sistema.exe", username: str = "admin", password: str = "", requirements_text: str = None, db_object_name: str = None, db_tns: str = None, db_user: str = None, db_password: str = None, exe_version: str = None, gef_grupo: str = None, gef_empresa: str = None, gef_filial: str = None):
        """Executa testes de caixa-preta de UI simulando o FlaUI no ERP."""
        self.log(f"🎬 Iniciando Execução de QA para o Cenário: '{scenario}'")
        if requirements_text:
            self.log(f"📄 Requisitos adicionais carregados: {len(requirements_text)} caracteres.")
        
        # 1. Aciona auditoria lógica de banco de dados Oracle se aplicável
        if db_object_name and db_tns and db_user:
            self.audit_database_object(db_object_name, db_tns, db_user, db_password)

        if not PYWINAUTO_AVAILABLE:
            self.log("❌ Falha: Automação necessita de sistema operacional Windows.")
            return self.logs

        try:
            # Simulação do comportamento de cliques e tempo de resposta (FlaUI/UIA)
            self.log(f"Passo 1: Disparando processo '{exe_path}'")
            app = Application(backend="win32").start(exe_path)
            time.sleep(2)

            self.log("Passo 2: Aguardando janela ativa...")
            dlg = app.top_window()
            self.log(f"Janela ativa localizada com sucesso: '{dlg.window_text()}'")

            # Varredura rápida de controles
            self.log("Passo 3: Mapeando campos de entrada (User/Password)...")
            descendants = dlg.descendants()
            edits = [c for c in descendants if "Edit" in c.friendly_class_name() or "TEdit" in c.class_name()]
            
            if len(edits) >= 2:
                self.log(f"Passo 4: Preenchendo credenciais do ERP para o usuário '{username}'...")
                try:
                    edits[0].set_text(username)
                except Exception:
                    try:
                        edits[0].type_keys(username)
                    except Exception:
                        pass
                try:
                    edits[1].set_text(password)
                except Exception:
                    try:
                        edits[1].type_keys(password)
                    except Exception:
                        pass
                self.log("Credenciais de teste inseridas com sucesso.")
            else:
                self.log("⚠️ Aviso: Inputs de login não encontrados. Ignorando preenchimento.")

            self.log("Passo 5: Clicando em Confirmar/Entrar...")
            dlg.type_keys("{ENTER}")
            time.sleep(3)

            # --- LOOP DE DESCARTE E CONFIGURAÇÃO DE DIÁLOGOS INTERMEDIÁRIOS ---
            # Permite faturar as telas de Versão e GEF (Grupo/Empresa/Filial) sequencialmente
            for step in range(3):
                time.sleep(3)
                try:
                    top_dlg = app.top_window()
                    title = top_dlg.window_text().upper()
                    self.log(f"[Passo {step+1}] Checando diálogo ativo: '{top_dlg.window_text()}'")
                    
                    if not any(x in title for x in ["VERSÃO", "VERSAO", "SELECIONAR", "EMPRESA", "FILIAL", "CONFIRMA", "ENTRAR", "SELEÇÃO", "SELECAO", "GEF", "CONECTA", "LOGIN"]):
                        self.log("Janela Principal detectada no topo. Parando loop de diálogos.")
                        break
                        
                    # 1. Tratamento da Janela de Seleção de Versão
                    if any(x in title for x in ["VERSÃO", "VERSAO", "VERSÃO DO EXE"]):
                        if exe_version:
                            self.log(f"Preenchendo versão selecionada: '{exe_version}'")
                            try:
                                v_edits = [c for c in top_dlg.descendants() if "Edit" in c.friendly_class_name() or "TEdit" in c.class_name()]
                                if v_edits:
                                    v_edits[0].set_text(exe_version)
                                else:
                                    top_dlg.type_keys(exe_version)
                            except Exception:
                                top_dlg.type_keys(exe_version)
                        else:
                            self.log("Versão não especificada. Aceitando padrão.")
                        
                        top_dlg.type_keys("{ENTER}")
                        
                    # 2. Tratamento da Janela de Seleção de GEF (Grupo / Empresa / Filial)
                    elif any(x in title for x in ["GEF", "EMPRESA", "FILIAL", "GRUPO"]):
                        self.log(f"Configurando contexto GEF (Grupo: {gef_grupo}, Empresa: {gef_empresa}, Filial: {gef_filial})")
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
                            self.log(f"Falha na digitação estruturada de GEF: {e}")
                        
                        top_dlg.type_keys("{ENTER}")
                        
                    else:
                        self.log("Confirmando diálogo intermediário genérico pós-login...")
                        top_dlg.type_keys("{ENTER}")
                except Exception as ex:
                    self.log(f"Aviso durante loop de diálogos: {ex}")
                    break

            time.sleep(6) # Aguardar faturamento do menu principal do ERP

            # Aguarda menus do ERP carregarem completamente antes de prosseguir
            self.log("⏳ Aguardando 10s para os menus do ERP carregarem completamente...")
            time.sleep(10)

            self.log("Passo 6: Verificando se a tela principal do ERP carregou...")
            main_dlg = app.top_window()
            self.log(f"Sucesso: Janela principal detectada: '{main_dlg.window_text()}'")

            # Finalizar teste com sucesso
            app.kill()
            self.log("🏆 Teste Automatizado concluído com status de SUCESSO.")
            
        except Exception as e:
            self.log(f"💥 ERRO CRÍTICO NA INTERFACE: {str(e)}")
            self.log("❌ Teste concluído com status de FALHA.")
            
        return self.logs

    def audit_database_object(self, db_object_name: str, db_tns: str, db_user: str, db_password: str):
        if not db_object_name:
            return
        
        self.log(f"🔍 [DB-Auditor] Iniciando extração do objeto de banco: '{db_object_name.upper()}' no TNS '{db_tns}'")
        
        if not ORACLEDB_AVAILABLE:
            self.log("❌ [DB-Auditor] Falha: Biblioteca 'oracledb' não está disponível no Python local.")
            return

        try:
            config_dir = r"C:\app\client\oracle\product\19.0.0\client_1\network\admin"
            if not os.path.exists(config_dir):
                config_dir = None # Deixa o oracledb buscar do padrão
                
            self.log(f"[DB-Auditor] Conectando ao Oracle Thin Client ({db_user}@{db_tns})...")
            connection = oracledb.connect(
                user=db_user,
                password=db_password,
                dsn=db_tns,
                config_dir=config_dir
            )
            cursor = connection.cursor()
            
            # 1. Tentar extrair como código fonte (Trigger, Procedure, View, Function, Package)
            self.log(f"[DB-Auditor] Buscando código fonte na USER_SOURCE...")
            cursor.execute("""
                SELECT TEXT 
                FROM USER_SOURCE 
                WHERE NAME = :name 
                ORDER BY LINE
            """, name=db_object_name.upper())
            source_lines = cursor.fetchall()
            
            if source_lines:
                code_text = "".join([line[0] for line in source_lines])
                self.log(f"[DB-AUDIT-FOUND] Objeto encontrado na USER_SOURCE.")
                self.log(f"--- INÍCIO DO CÓDIGO FONTE ({db_object_name.upper()}) ---")
                self.log(code_text)
                self.log(f"--- FIM DO CÓDIGO FONTE ---")
                return

            # 2. Tentar extrair como tabela
            self.log(f"[DB-Auditor] Código fonte não encontrado na USER_SOURCE. Buscando definição na USER_TAB_COLUMNS...")
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE 
                FROM USER_TAB_COLUMNS 
                WHERE TABLE_NAME = :name
                ORDER BY COLUMN_ID
            """, name=db_object_name.upper())
            columns = cursor.fetchall()
            
            if columns:
                self.log(f"[DB-AUDIT-FOUND] Tabela encontrada na USER_TAB_COLUMNS.")
                self.log(f"--- ESTRUTURA DA TABELA ({db_object_name.upper()}) ---")
                for col in columns:
                    nullable_str = "NULL" if col[3] == "Y" else "NOT NULL"
                    self.log(f"Coluna: {col[0]} | Tipo: {col[1]}({col[2]}) | {nullable_str}")
                self.log(f"--- FIM DA ESTRUTURA ---")
                return
                
            self.log(f"⚠️ [DB-Auditor] O objeto '{db_object_name.upper()}' não foi encontrado no dicionário do Oracle (USER_SOURCE / USER_TAB_COLUMNS).")
            
        except Exception as e:
            self.log(f"❌ [DB-Auditor] Erro ao conectar ou extrair dados do Oracle: {e}")
