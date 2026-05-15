from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
from .models import ERPMapping, AgentExecution, Base
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

@app.get("/")
def read_root():
    return {"status": "ERP Guardian AI API is online"}

@app.get("/mappings")
def get_mappings(db: Session = Depends(get_db)):
    """Retorna o mapeamento de todos os arquivos do ERP."""
    return db.query(ERPMapping).order_by(ERPMapping.updated_at.desc()).all()

@app.get("/executions")
def get_executions(db: Session = Depends(get_db)):
    """Retorna o histórico de análises dos agentes."""
    return db.query(AgentExecution).order_by(AgentExecution.created_at.desc()).limit(20).all()

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Estatísticas rápidas para o Dashboard."""
    total_files = db.query(ERPMapping).count()
    total_executions = db.query(AgentExecution).count()
    return {
        "total_files": total_files,
        "total_executions": total_executions,
        "health_score": 85 # Exemplo estático por enquanto
    }

@app.post("/api/telemetria")
def post_telemetria(data: dict, db: Session = Depends(get_db)):
    """Recebe telemetria e relatórios dos agentes e salva no histórico."""
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
