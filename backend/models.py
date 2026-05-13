from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AgentMachine(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String, unique=True, index=True)
    hostname = Column(String)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String) # 'online', 'offline', 'busy'

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    vcs_type = Column(String, default="JEDI")
    vcs_path = Column(String)
    oracle_connection_string = Column(String) # Encrypted or partial
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AnalysisReport(Base):
    __tablename__ = "analysis_reports"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    agent_id = Column(Integer, ForeignKey("agents.id"))
    commit_hash = Column(String)
    impacted_modules = Column(JSON) # List of modules
    risk_score = Column(Integer)
    findings = Column(JSON) # AI Review findings
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class QAExecution(Base):
    __tablename__ = "qa_executions"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("analysis_reports.id"))
    workflow_name = Column(String) # 'Order', 'Invoice', etc.
    status = Column(String) # 'success', 'failed', 'running'
    logs = Column(Text)
    screenshots = Column(JSON) # List of S3/Cloudinary URLs
    oracle_validation = Column(JSON) # Comparison results
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime)
