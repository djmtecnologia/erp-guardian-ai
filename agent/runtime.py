import time
import os
import sys
import asyncio

# Adiciona a raiz do projeto ao sys.path para permitir importações modulares
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from orchestrator.engine import OrchestrationEngine
from agents.delphi_review_agent.agent import DelphiReviewAgent
from agents.documentation_agent.agent import DocumentationAgent
from workflow_engine.engine import HybridWorkflow
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

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
            backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            telemetry_data = {
                "agent_id": "local-runtime-monitor",
                "status": "completed",
                "context": {"file": os.path.basename(file_path)},
                "report": {"workflow_results": [r.model_dump(mode='json') for r in results["execution_history"]]}
            }
            requests.post(f"{backend_url}/api/telemetria", json=telemetry_data)
            
        except Exception as e:
            print(f"❌ Erro ao processar mudança: {e}")

def run_monitor():
    path_to_watch = os.getenv("LOCAL_VCS_PATH", "./agent/samples")
    print(f"🛡️ ERP Guardian AI - Monitor Ativo")
    print(f"👀 Vigiando diretório: {os.path.abspath(path_to_watch)}")
    
    loop = asyncio.new_event_loop()
    
    # Thread separada para o loop de eventos assíncronos
    from threading import Thread
    thread = Thread(target=loop.run_forever, daemon=True)
    thread.start()

    event_handler = ERPFileHandler(loop)
    observer = Observer()
    observer.schedule(event_handler, path_to_watch, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        loop.call_soon_threadsafe(loop.stop)
    
    observer.join()

if __name__ == "__main__":
    run_monitor()
