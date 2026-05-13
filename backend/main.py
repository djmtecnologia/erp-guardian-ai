from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

app = FastAPI(title="ERP Guardian AI API", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "ERP Guardian AI Backend is running"}

# --- AGENT ENDPOINTS ---

@app.post("/agent/register")
async def register_agent(data: dict):
    """Register a local agent machine"""
    return {"status": "registered", "agent_id": "agent_123"}

@app.post("/agent/heartbeat")
async def heartbeat(agent_id: str):
    """Keep track of agent status"""
    return {"status": "alive"}

@app.post("/agent/submit-analysis")
async def submit_analysis(data: dict):
    """Receive metadata and findings from local agent"""
    # 1. Process VCS changes
    # 2. Trigger AI Review if not done locally
    # 3. Store report
    return {"status": "received", "report_id": 1}

# --- DASHBOARD ENDPOINTS ---

@app.get("/reports")
async def get_reports():
    """Get all analysis reports for the dashboard"""
    return []

@app.get("/reports/{report_id}")
async def get_report_detail(report_id: int):
    return {"id": report_id, "findings": []}

@app.get("/qa/executions")
async def get_qa_executions():
    return []

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
