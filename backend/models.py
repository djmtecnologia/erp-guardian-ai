from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class ERPMapping(Base):
    """
    Tabela para armazenar o mapeamento do ERP (Vetorizada para busca semântica).
    """
    __tablename__ = "erp_mappings"

    id = Column(Integer, primary_key=True)
    file_path = Column(String, index=True)
    module_name = Column(String, index=True)
    content_summary = Column(Text)
    # No Neon/PostgreSQL real, usaríamos o tipo 'vector' do pgvector
    # Para este boilerplate, usaremos JSONB para simular o armazenamento do embedding
    embedding = Column(JSONB) 
    metadata_info = Column(JSONB) # Workflow associations, dependencies, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AgentExecution(Base):
    """
    Histórico de execução de agentes.
    """
    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True)
    agent_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    context = Column(JSONB)
    report = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RiskAnalysis(Base):
    """
    Análise de risco gerada pelo Risk Engine.
    """
    __tablename__ = "risk_analyses"

    id = Column(Integer, primary_key=True)
    execution_id = Column(Integer, ForeignKey("agent_executions.id"))
    risk_level = Column(String) # LOW, MEDIUM, HIGH, CRITICAL
    affected_workflows = Column(JSONB)
    score = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
