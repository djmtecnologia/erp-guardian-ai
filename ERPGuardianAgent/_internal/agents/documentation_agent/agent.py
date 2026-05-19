import os
from typing import Any, Dict, List
from shared.base_agent import BaseAgent, AgentStatus, AgentReport
import google.generativeai as genai
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
try:
    from models import ERPMapping
except ImportError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from models import ERPMapping
from dotenv import load_dotenv

load_dotenv()

class DocumentationAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__("documentation-agent")
        genai.configure(api_key=api_key)
        self.model_priorities = [
            'gemini-2.0-flash-lite',
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro-latest',
            'gemini-2.0-flash',
            'gemini-flash-latest',
            'gemini-pro-latest',
            'gemini-3.1-flash-lite'
        ]
        self.embedding_model = "models/gemini-embedding-2"
        self.findings = []
        
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            self.engine = create_engine(db_url)
            self.Session = sessionmaker(bind=self.engine)
            self.db_available = True
        else:
            # Modo offline: sem banco de dados (execução local na empresa)
            self.engine = None
            self.Session = None
            self.db_available = False
            print("[DocumentationAgent] ⚠️ DATABASE_URL não configurada — operando em modo offline (sem persistência no Neon).")

    async def execute(self, context: Dict[str, Any]) -> AgentReport:
        self.status = AgentStatus.RUNNING
        project_path = context.get("project_path", "./agent/samples")
        session = self.Session() if self.db_available else None
        
        try:
            target_extensions = ['.pas', '.dfm', '.sql']
            for root, _, files in os.walk(project_path):
                for file in files:
                    if any(file.endswith(ext) for ext in target_extensions):
                        await self._process_with_fallback(os.path.join(root, file), session)

            if session:
                session.commit()
            self.status = AgentStatus.COMPLETED
        except Exception as e:
            print(f"[DocumentationAgent] Erro crítico: {e}")
            if session:
                session.rollback()
            self.status = AgentStatus.FAILED
        finally:
            if session:
                session.close()

        return self.generate_report()

    async def _process_with_fallback(self, file_path: str, session):
        """Tenta processar o arquivo usando a lista de modelos de fallback."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            summary = None
            for model_name in self.model_priorities:
                try:
                    model = genai.GenerativeModel(model_name)
                    prompt = f"Analise o arquivo ERP: {file_path}. Gere um resumo técnico conciso."
                    response = model.generate_content(prompt)
                    summary = response.text
                    break
                except Exception as e:
                    if "429" in str(e):
                        continue
                    raise e
            
            if not summary:
                raise Exception("Todos os modelos de fallback falharam por cota.")

            # Persistência no Neon (apenas quando banco disponível)
            if session:
                embedding_resp = genai.embed_content(model=self.embedding_model, content=summary, task_type="retrieval_document")
                vector = embedding_resp['embedding']

                mapping = session.query(ERPMapping).filter_by(file_path=file_path).first()
                if not mapping:
                    mapping = ERPMapping(file_path=file_path)
                    session.add(mapping)
                
                mapping.content_summary = summary
                mapping.embedding = vector
                mapping.module_name = os.path.basename(file_path)

            self.findings.append({"file": file_path, "status": "analyzed", "summary": summary})

        except Exception as e:
            print(f"[DocumentationAgent] Falha em {file_path}: {e}")

    async def validate(self, result: Any) -> bool:
        return self.status == AgentStatus.COMPLETED

    async def rollback(self) -> bool:
        return True

    def generate_report(self) -> AgentReport:
        return AgentReport(agent_id=self.agent_id, status=self.status, findings=self.findings, recommendations=[], metadata={})
