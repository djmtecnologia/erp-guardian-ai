from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class ERPMapping(Base):
    __tablename__ = "erp_mappings"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, unique=True, index=True)
    module_name = Column(String)
    content_summary = Column(Text)
    embedding = Column(JSON)  # Armazena o vetor como JSON para compatibilidade simples
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String)
    status = Column(String)
    context = Column(JSON)
    report = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class RiskAnalysis(Base):
    __tablename__ = "risk_analyses"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String)
    risk_level = Column(String)  # Low, Medium, High, Critical
    vulnerabilities = Column(JSON)
    recommendations = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
