from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
import shutil
from sqlalchemy.orm import Session
from typing import List
import os
import sys

# Adiciona o caminho para encontrar os modelos na raiz se necessário
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importação relativa dependendo da estrutura
try:
    from backend.models import ERPMapping, AgentExecution, Base
except ImportError:
    from models import ERPMapping, AgentExecution, Base

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
@app.post("/api/support")
async def solve_support_ticket(
    description: str = Form(...),
    files: List[UploadFile] = File(...)
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
            "files": saved_files
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
