from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
import shutil
from sqlalchemy.orm import Session
from typing import List
import os
import sys

# Adiciona o caminho para encontrar os modelos na raiz se necessário
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ERPMapping, AgentExecution, Base, ERPScanTask, ERPUIKnowledge, QATask, QAReport

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ERP Guardian AI - API")

# DB Setup
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api")
def read_root():
    return {"status": "ERP Guardian AI API is online"}

@app.get("/api/mappings")
def get_mappings(db: Session = Depends(get_db)):
    return db.query(ERPMapping).order_by(ERPMapping.updated_at.desc()).all()

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total_files = db.query(ERPMapping).count()
    total_executions = db.query(AgentExecution).count()
    return {
        "total_files": total_files,
        "total_executions": total_executions,
        "health_score": 85
    }

@app.post("/api/telemetria")
def post_telemetria(data: dict, db: Session = Depends(get_db)):
    execution = AgentExecution(
        agent_id=data.get("agent_id", "unknown"),
        status=data.get("status", "completed"),
        context=data.get("context", {}),
        report=data.get("report", {})
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return {"status": "success", "id": execution.id}
@app.post("/api/support")
async def solve_support_ticket(
    description: str = Form(...),
    files: List[UploadFile] = File(...),
    oracle_user: str = Form(None),
    oracle_password: str = Form(None),
    oracle_tns: str = Form(None)
):
    try:
        from agents.support_agent.agent import SupportResolutionAgent
        
        # O Vercel permite salvar em /tmp (Lambda)
        tmp_dir = "/tmp/erp_support_uploads"
        os.makedirs(tmp_dir, exist_ok=True)
        
        saved_files = []
        for file in files:
            file_path = os.path.join(tmp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file_path)
            
        agent = SupportResolutionAgent(api_key=os.getenv("GEMINI_API_KEY"))
        context = {
            "description": description,
            "files": saved_files,
            "oracle_user": oracle_user,
            "oracle_password": oracle_password,
            "oracle_tns": oracle_tns
        }
        
        report = await agent.execute(context)
        
        # Limpeza
        for f in saved_files:
            try:
                os.remove(f)
            except:
                pass
                
        if report.status.value == "completed":
            return {"status": "success", "solution": report.findings[0].get("content")}
        else:
            return {"status": "error", "message": "A IA não conseguiu processar a análise."}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- ENDPOINTS DO UI SCANNER (VARREDURA WINDOWS) ---

@app.post("/api/ui-scan/trigger")
def trigger_scan(data: dict, db: Session = Depends(get_db)):
    """Cria uma tarefa de varredura na nuvem para ser capturada pelo Windows."""
    task = ERPScanTask(
        exe_path=data.get("exe_path"),
        username=data.get("username"),
        password=data.get("password"),
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"status": "success", "task_id": task.id}

@app.get("/api/ui-scan/pending")
def get_pending_scan(db: Session = Depends(get_db)):
    """O Agente Windows consome esta rota para verificar se há tarefas."""
    task = db.query(ERPScanTask).filter_by(status="pending").first()
    if not task:
        return {"status": "no_tasks"}
    return {
        "status": "task_found",
        "task_id": task.id,
        "exe_path": task.exe_path,
        "username": task.username,
        "password": task.password
    }

@app.post("/api/ui-scan/update")
def update_scan_status(data: dict, db: Session = Depends(get_db)):
    """Atualiza o status da varredura executada localmente."""
    task = db.query(ERPScanTask).filter_by(id=data.get("task_id")).first()
    if task:
        task.status = data.get("status")
        db.commit()
        return {"status": "updated"}
    raise HTTPException(status_code=404, detail="Tarefa não encontrada")

@app.post("/api/ui-scan/result")
def post_scan_result(data: dict, db: Session = Depends(get_db)):
    """O Agente Windows envia a árvore de telas do ERP mapeada por pywinauto."""
    knowledge = ERPUIKnowledge(
        screen_name=data.get("screen_name"),
        controls=data.get("controls")
    )
    db.add(knowledge)
    db.commit()
    return {"status": "success"}

@app.get("/api/ui-scan/knowledge")
def get_ui_knowledge(db: Session = Depends(get_db)):
    """Carrega toda a base de conhecimento de interface gerada."""
    return db.query(ERPUIKnowledge).order_by(ERPUIKnowledge.created_at.desc()).all()

# --- ENDPOINTS DO WORKFLOW DE QA (TESTES E MANUAIS AUTOMÁTICOS) ---

@app.post("/api/qa/trigger")
def trigger_qa_task(data: dict, db: Session = Depends(get_db)):
    """Dispara um cenário de teste a ser executado pelo Windows."""
    task = QATask(
        scenario=data.get("scenario"),
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"status": "success", "task_id": task.id}

@app.get("/api/qa/pending")
def get_pending_qa_task(db: Session = Depends(get_db)):
    """O Agente Windows busca cenários de testes de interface pendentes."""
    task = db.query(QATask).filter_by(status="pending").first()
    if not task:
        return {"status": "no_tasks"}
    return {
        "status": "task_found",
        "task_id": task.id,
        "scenario": task.scenario
    }

@app.post("/api/qa/update")
def update_qa_status(data: dict, db: Session = Depends(get_db)):
    """Atualiza o status do teste de QA local."""
    task = db.query(QATask).filter_by(id=data.get("task_id")).first()
    if task:
        task.status = data.get("status")
        db.commit()
        return {"status": "updated"}
    raise HTTPException(status_code=404, detail="Tarefa não encontrada")

@app.post("/api/qa/result")
def post_qa_result(data: dict, db: Session = Depends(get_db)):
    """O Agente Windows envia os logs brutos da execução da automação UI."""
    task_id = data.get("task_id")
    test_logs = data.get("test_logs")
    
    # 1. Salvar resultado temporário ou direto
    # 2. Chamar a IA para gerar os documentos (Pipeline QA -> Documentador)
    task = db.query(QATask).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
        
    task.status = "completed"
    
    # Buscar conhecimento da tela mais recente para enriquecer o manual
    # Para o MVP, pegamos a última tela mapeada ou fazemos busca genérica
    ui_info = db.query(ERPUIKnowledge).order_by(ERPUIKnowledge.created_at.desc()).first()
    ui_controls_str = ""
    if ui_info and ui_info.controls:
        ui_controls_str = str(ui_info.controls[:40]) # Limita escopo de tokens
        
    # Acionar a inteligência para documentação
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Padrão robusto de fallback de modelos
        models = [
            'gemini-2.0-flash-lite',
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro-latest',
            'gemini-2.0-flash',
            'gemini-flash-latest',
            'gemini-pro-latest',
            'gemini-3.1-flash-lite'
        ]
        generated_text = ""
        
        prompt = f"""
        Você é um Engenheiro de QA Sênior e Escritor Técnico de Manuais de ERP.
        Com base no cenário testado e no log da automação de UI abaixo, gere dois documentos.
        
        IMPORTANTE: Separe estritamente os dois documentos usando a tag [DIVIDER] no meio!
        
        CENÁRIO TESTADO: {task.scenario}
        LOGS DE EXECUÇÃO: {test_logs}
        COMPONENTES DE INTERFACE CONHECIDOS: {ui_controls_str}
        
        Estrutura esperada:
        
        --- INÍCIO DO RELATÓRIO ---
        # 📋 Relatório de Teste de QA
        Apresente uma análise técnica do teste, se passou ou falhou, tempos de resposta e estabilidade.
        
        [DIVIDER]
        
        # 📖 Manual do Usuário: Funcionalidade ERP
        Crie um guia passo a passo amigável em Markdown explicando ao usuário final como navegar e executar essa rotina testada.
        --- FIM ---
        """
        
        for m in models:
            try:
                print(f"[QA-Pipeline] Tentando modelo: {m}")
                model = genai.GenerativeModel(m)
                response = model.generate_content(prompt)
                generated_text = response.text
                print(f"[QA-Pipeline] Sucesso com o modelo: {m}")
                break
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    print(f"[QA-Pipeline] Cota excedida no modelo {m}. Tentando próximo...")
                    continue
                else:
                    print(f"[QA-Pipeline] Erro no modelo {m}: {e}")
                    continue
                
        if not generated_text:
            raise Exception("IA falhou no processamento de escrita técnica.")
            
        parts = generated_text.split("[DIVIDER]")
        report_md = parts[0].strip()
        manual_md = parts[1].strip() if len(parts) > 1 else "Manual em geração..."
        
        qa_report = QAReport(
            task_id=task_id,
            test_logs=test_logs,
            test_report_md=report_md,
            user_manual_md=manual_md
        )
        db.add(qa_report)
        db.commit()
        
    except Exception as e:
        print(f"[QA-Pipeline] Erro na geração automática de documentação: {e}")
        # Cria relatório com erro para não perder logs
        qa_report = QAReport(
            task_id=task_id,
            test_logs=test_logs,
            test_report_md=f"# ❌ Falha na geração da IA\n{str(e)}",
            user_manual_md="Não foi possível gerar o manual do usuário devido a um erro de IA."
        )
        db.add(qa_report)
        db.commit()
        
    return {"status": "success"}

@app.get("/api/qa/reports")
def get_qa_reports(db: Session = Depends(get_db)):
    """Busca a lista de relatórios de QA e manuais gerados."""
    return db.query(QAReport).order_by(QAReport.created_at.desc()).all()
