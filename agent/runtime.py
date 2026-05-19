import time
import os
import sys
import asyncio
import traceback
import logging

# -----------------------------------------------------------------------
# SISTEMA DE LOG PERSISTENTE EM ARQUIVO
# Captura QUALQUER erro (mesmo antes da janela abrir completamente)
# e salva no mesmo diretório do executável para análise posterior.
# -----------------------------------------------------------------------

# Descobre o diretório real do executável (funciona tanto .py quanto .exe)
if getattr(sys, 'frozen', False):
    # Rodando como executável PyInstaller
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Rodando como script Python normal
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_FILE = os.path.join(BASE_DIR, "erp_guardian_agent.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ERPGuardian")

def handle_exception(exc_type, exc_value, exc_tb):
    """Captura exceções não tratadas e salva no log antes de fechar."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical(f"ERRO FATAL NÃO TRATADO:\n{error_msg}")

sys.excepthook = handle_exception

logger.info("=" * 60)
logger.info("ERP Guardian AI - Iniciando...")
logger.info(f"BASE_DIR do executável: {BASE_DIR}")
logger.info(f"Arquivo de log: {LOG_FILE}")
logger.info("=" * 60)

# Adiciona a raiz do projeto ao sys.path para permitir importações modulares
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
logger.info("Importando módulos do agente...")

import models

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from orchestrator.engine import OrchestrationEngine
from agents.delphi_review_agent.agent import DelphiReviewAgent
from agents.documentation_agent.agent import DocumentationAgent
from workflow_engine.engine import HybridWorkflow
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# URL da Vercel como padrão — funciona sem .env na máquina da empresa
# Pode ser sobrescrito via variável de ambiente LOCAL_BACKEND_URL no .env
BACKEND_URL = os.getenv("BACKEND_URL", "https://erp-guardian-ai.vercel.app").rstrip("/")
logger.info(f"Backend URL configurado: {BACKEND_URL}")

import hashlib

class ERPFileHandler(FileSystemEventHandler):
    def __init__(self, loop):
        self.loop = loop
        self.engine = OrchestrationEngine()
        self.last_processed_hash = {} # Cache de conteúdo: {file_path: hash}
        self.engine.register_agent(DelphiReviewAgent(api_key=API_KEY))
        self.engine.register_agent(DocumentationAgent(api_key=API_KEY))

    def on_modified(self, event):
        if event.is_directory:
            return
        
        filename = event.src_path
        if filename.endswith(('.pas', '.sql')):
            # Calcula o hash do arquivo para ver se mudou mesmo
            try:
                with open(filename, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                
                if self.last_processed_hash.get(filename) == file_hash:
                    return # Conteúdo idêntico, ignorar
                
                self.last_processed_hash[filename] = file_hash
                print(f"\n[Monitor] Mudança detectada (conteúdo novo) em: {filename}")
                asyncio.run_coroutine_threadsafe(self.process_change(filename), self.loop)
            except Exception as e:
                print(f"[Monitor] Erro ao ler arquivo para hash: {e}")

    async def process_change(self, file_path):
        print(f"[Monitor] Iniciando análise híbrida para {os.path.basename(file_path)}...")
        
        # Criar contexto de execução
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code_content = f.read()

        context = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "code": code_content,
            "project_path": os.path.dirname(file_path)
        }

        # Criar e rodar o Workflow Híbrido que validamos
        workflow = HybridWorkflow(f"auto-analysis-{os.path.basename(file_path)}")
        
        # Definir passos (Exemplo: Documentar -> Revisar)
        workflow.add_agent_step(self.engine.agents["documentation-agent"]) \
                .add_agent_step(self.engine.agents["delphi-review-agent"])

        try:
            results = await workflow.run(context)
            print(f"✅ Análise concluída para {os.path.basename(file_path)}")
            
            # Enviar para o Backend via Telemetria
            import requests
            backend_url = BACKEND_URL
            telemetry_data = {
                "agent_id": "local-runtime-monitor",
                "status": "completed",
                "context": {"file": os.path.basename(file_path)},
                "report": {"workflow_results": [r.model_dump(mode='json') for r in results["execution_history"]]}
            }
            requests.post(f"{backend_url}/api/telemetria", json=telemetry_data)
            
        except Exception as e:
            print(f"❌ Erro ao processar mudança: {e}")

async def poll_ui_scan_tasks():
    backend_url = BACKEND_URL
    
    from agent.ui_scanner import ERPUIWatcher
    watcher = ERPUIWatcher(backend_url)
    
    import requests
    
    while True:
        try:
            response = await asyncio.to_thread(requests.get, f"{backend_url}/api/ui-scan/pending")
            data = response.json()
            if data.get("status") == "task_found":
                task_id = data.get("task_id")
                exe_path = data.get("exe_path")
                username = data.get("username")
                password = data.get("password")
                
                print(f"\n[Monitor] 📥 Nova tarefa de Varredura de UI detectada! ID: {task_id}")
                # Executa a varredura em uma thread separada para não congelar o monitoramento de arquivos
                await asyncio.to_thread(
                    watcher.run_scan_workflow,
                    task_id, exe_path, username, password
                )
        except Exception:
            pass
        await asyncio.sleep(10)

async def poll_qa_tasks():
    backend_url = BACKEND_URL
    
    from agent.qa_engine import QAAutomationEngine
    qa_engine = QAAutomationEngine(backend_url)
    
    import requests
    
    while True:
        try:
            response = await asyncio.to_thread(requests.get, f"{backend_url}/api/qa/pending")
            data = response.json()
            if data.get("status") == "task_found":
                task_id = data.get("task_id")
                scenario = data.get("scenario")
                exe_path = data.get("exe_path") or "C:\\ERP\\sistema.exe"
                username = data.get("username") or "admin"
                password = data.get("password") or ""
                req_content = data.get("requirements_file_content")
                
                full_scenario = scenario
                if req_content:
                    full_scenario = f"{scenario}\n\n[Requisitos do Arquivo Anexo]:\n{req_content}"
                
                print(f"\n[Monitor] 📥 Nova tarefa de QA detectada! ID: {task_id} - Executável: {exe_path}")
                
                # Executa o fluxo de testes simulado (FlaUI/pywinauto)
                logs = await asyncio.to_thread(
                    qa_engine.execute_qa_test,
                    task_id, full_scenario, exe_path, username, password, req_content
                )
                
                # Envia o log gerado de volta para a nuvem processar a documentação
                payload = {
                    "task_id": task_id,
                    "test_logs": logs
                }
                await asyncio.to_thread(
                    requests.post,
                    f"{backend_url}/api/qa/result",
                    json=payload
                )
        except Exception:
            pass
        await asyncio.sleep(10)

def sync_tnsnames():
    tnsnames_path = r"C:\app\client\oracle\product\19.0.0\client_1\network\admin\tnsnames.ora"
    tns_names = []
    backend_url = BACKEND_URL
    if os.path.exists(tnsnames_path):
        try:
            import re
            with open(tnsnames_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            content = re.sub(r'#.*', '', content)
            lines = [line.strip() for line in content.splitlines()]
            clean_content = "".join([l for l in lines if l])
            matches = re.findall(r'([a-zA-Z0-9_\-\.]+)\s*=\s*(\((?:[^\(\)]*|\((?:[^\(\)]*|\((?:[^\(\)]*|\([^\(\)]*\))*\))*\))*\))', clean_content)
            tns_names = [m[0].upper().strip() for m in matches]
            print(f"[Monitor] 🔌 Encontrados {len(tns_names)} perfis no tnsnames.ora local: {tns_names}")
        except Exception as e:
            print(f"[Monitor] Erro ao parsear tnsnames.ora: {e}")
            
    try:
        import requests
        requests.post(f"{backend_url}/api/support/tnsnames", json={"tns_names": tns_names})
        print(f"[Monitor] 🌐 Perfis TNS sincronizados com a nuvem Vercel!")
    except Exception as e:
        print(f"[Monitor] Erro ao sincronizar TNS com a nuvem: {e}")

async def poll_support_tasks():
    backend_url = BACKEND_URL
    
    import requests
    
    while True:
        try:
            response = await asyncio.to_thread(requests.get, f"{backend_url}/api/support/pending")
            data = response.json()
            if data.get("status") == "task_found":
                task_id = data.get("task_id")
                description = data.get("description")
                oracle_user = data.get("oracle_user")
                oracle_password = data.get("oracle_password")
                oracle_tns = data.get("oracle_tns")
                files_list = data.get("files", [])
                
                print(f"\n[Monitor] 📥 Novo chamado N3 recebido para resolver localmente! ID: {task_id}")
                
                # Reconstruir arquivos anexados localmente na pasta temporária
                import tempfile
                import base64
                import shutil
                
                temp_dir = tempfile.mkdtemp(prefix="erp_support_")
                reconstructed_paths = []
                
                for f_dict in files_list:
                    filename = f_dict.get("filename")
                    content = f_dict.get("content", "")
                    is_binary = f_dict.get("is_binary", False)
                    
                    file_path = os.path.join(temp_dir, filename)
                    try:
                        if is_binary:
                            with open(file_path, "wb") as f_out:
                                f_out.write(base64.b64decode(content))
                        else:
                            with open(file_path, "w", encoding="utf-8", errors="ignore") as f_out:
                                f_out.write(content)
                        reconstructed_paths.append(file_path)
                    except Exception as fe:
                        print(f"[Monitor] Erro ao reconstruir arquivo {filename}: {fe}")
                
                from agents.support_agent.agent import SupportResolutionAgent
                agent = SupportResolutionAgent(api_key=API_KEY)
                
                context = {
                    "description": description,
                    "files": reconstructed_paths,
                    "oracle_user": oracle_user,
                    "oracle_password": oracle_password,
                    "oracle_tns": oracle_tns
                }
                
                report = await agent.execute(context)
                
                solution_text = ""
                if report.status.value == "completed":
                    solution_text = report.findings[0].get("content", "")
                else:
                    solution_text = f"Erro na análise técnica do suporte local: {report.findings}"
                    
                payload = {
                    "task_id": task_id,
                    "status": report.status.value,
                    "solution": solution_text
                }
                
                await asyncio.to_thread(
                    requests.post,
                    f"{backend_url}/api/support/result",
                    json=payload
                )
                print(f"[Monitor] ✅ Chamado N3 ID {task_id} resolvido e enviado à nuvem!")
                
                # Limpeza da pasta temporária
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
        await asyncio.sleep(10)

def run_monitor():
    try:
        # Resolve o diretório de samples SEMPRE relativo ao executável
        # independentemente de onde o exe foi copiado ou executado
        default_samples = os.path.join(BASE_DIR, "agent", "samples")
        path_to_watch = os.getenv("LOCAL_VCS_PATH", default_samples)
        
        logger.info(f"Diretório de monitoramento configurado: {path_to_watch}")
        
        # Auto-cura: Garante que a pasta de monitoramento existe
        os.makedirs(path_to_watch, exist_ok=True)
        logger.info(f"✅ Pasta de monitoramento verificada/criada: {path_to_watch}")
        
        # Sincroniza TNSnames local com a Vercel
        logger.info("Sincronizando perfis Oracle (tnsnames.ora)...")
        sync_tnsnames()
        
        logger.info(f"🛡️ ERP Guardian AI - Monitor Ativo")
        logger.info(f"👀 Vigiando diretório: {os.path.abspath(path_to_watch)}")
        print(f"\n🛡️ ERP Guardian AI - Monitor Ativo")
        print(f"👀 Vigiando diretório: {os.path.abspath(path_to_watch)}")
        print(f"📋 Log salvo em: {LOG_FILE}\n")
        
        loop = asyncio.new_event_loop()
        
        # Thread separada para o loop de eventos assíncronos
        from threading import Thread
        thread = Thread(target=loop.run_forever, daemon=True)
        thread.start()
        logger.info("Loop de eventos assíncronos iniciado.")

        # Registra os ouvintes contínuos de tarefas da Vercel
        asyncio.run_coroutine_threadsafe(poll_ui_scan_tasks(), loop)
        asyncio.run_coroutine_threadsafe(poll_qa_tasks(), loop)
        asyncio.run_coroutine_threadsafe(poll_support_tasks(), loop)
        logger.info("Polling de tarefas da nuvem ativado.")

        event_handler = ERPFileHandler(loop)
        observer = Observer()
        observer.schedule(event_handler, path_to_watch, recursive=True)
        observer.start()
        logger.info("Watchdog de arquivos iniciado com sucesso!")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Encerrando por solicitação do usuário (KeyboardInterrupt)...")
            observer.stop()
            loop.call_soon_threadsafe(loop.stop)
        
        observer.join()
        logger.info("ERP Guardian AI encerrado.")
        
    except Exception as e:
        logger.critical(f"ERRO FATAL ao iniciar o monitor:\n{traceback.format_exc()}")
        # Mantém a janela aberta por 30 segundos para o usuário ler o erro
        print(f"\n\n❌ ERRO FATAL: {e}")
        print(f"📋 Detalhes completos salvos em: {LOG_FILE}")
        print("\nA janela fechará em 30 segundos...")
        time.sleep(30)

if __name__ == "__main__":
    run_monitor()
