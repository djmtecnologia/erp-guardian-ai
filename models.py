from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class ERPMapping(Base):
    """
    Tabela para armazenar o mapeamento do ERP (Vetorizada para busca semântica).
    """
    __tablename__ = "erp_mappings"

    id = Column(Integer, primary_key=True)
    file_path = Column(String, unique=True, index=True)
    module_name = Column(String, index=True)
    content_summary = Column(Text)
    embedding = Column(JSONB)       # Armazena o vetor como JSONB no Neon
    metadata_info = Column(JSONB)   # Associações de workflow, dependências, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AgentExecution(Base):
    """
    Histórico de execução de agentes da fábrica de software.
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
    Análise de risco gerada pelo Risk Engine para o ERP.
    """
    __tablename__ = "risk_analyses"

    id = Column(Integer, primary_key=True)
    file_path = Column(String, index=True)
    risk_level = Column(String)  # LOW, MEDIUM, HIGH, CRITICAL
    vulnerabilities = Column(JSONB)
    recommendations = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
