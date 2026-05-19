from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
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
    embedding = Column(JSON)       # Mapeia para JSONB no Postgres / JSON no SQLite
    metadata_info = Column(JSON)   # Associações de workflow, dependências, etc.
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
    context = Column(JSON)
    report = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RiskAnalysis(Base):
    """
    Análise de risco gerada pelo Risk Engine para o ERP.
    """
    __tablename__ = "risk_analyses"

    id = Column(Integer, primary_key=True)
    file_path = Column(String, index=True)
    risk_level = Column(String)  # LOW, MEDIUM, HIGH, CRITICAL
    vulnerabilities = Column(JSON)
    recommendations = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ERPScanTask(Base):
    """
    Fila de tarefas de varredura de UI a serem executadas pelo agente local Windows.
    """
    __tablename__ = "erp_scan_tasks"

    id = Column(Integer, primary_key=True)
    exe_path = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ERPUIKnowledge(Base):
    """
    Base de conhecimento gerada a partir da varredura de interface do ERP.
    """
    __tablename__ = "erp_ui_knowledge"

    id = Column(Integer, primary_key=True)
    screen_name = Column(String, index=True)
    controls = Column(JSON)  # Árvore de botões, inputs, menus mapeados
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class QATask(Base):
    """
    Fila de tarefas de automação de testes de interface (QA) a serem executadas localmente no Windows.
    """
    __tablename__ = "qa_tasks"

    id = Column(Integer, primary_key=True)
    scenario = Column(Text, nullable=False)  # Descrição do cenário a ser testado
    exe_path = Column(Text, nullable=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    requirements_file_name = Column(String, nullable=True)
    requirements_file_content = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class QAReport(Base):
    """
    Relatórios de testes de QA e Manuais de Usuário gerados pela IA.
    """
    __tablename__ = "qa_reports"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("qa_tasks.id"))
    test_logs = Column(JSON)            # Logs brutos da automação de UI
    test_report_md = Column(Text)       # Relatório de Teste estruturado em Markdown
    user_manual_md = Column(Text)       # Manual do Usuário Final em Markdown
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SupportTask(Base):
    """
    Fila de chamados de suporte N3 a serem resolvidos localmente com conexão Oracle corporativa.
    """
    __tablename__ = "support_tasks"

    id = Column(Integer, primary_key=True)
    description = Column(Text, nullable=False)
    files = Column(JSON, nullable=True) # Lista de caminhos ou conteúdos dos anexos
    oracle_user = Column(String, nullable=True)
    oracle_password = Column(String, nullable=True)
    oracle_tns = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, running, completed, failed
    solution = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LocalConfig(Base):
    """
    Configurações locais sincronizadas do ambiente Windows do cliente (ex: tnsnames.ora).
    """
    __tablename__ = "local_configs"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)
    value = Column(JSON)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
