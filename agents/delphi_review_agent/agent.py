import os
from typing import Any, Dict, List
from shared.base_agent import BaseAgent, AgentStatus, AgentReport
import google.generativeai as genai

class DelphiReviewAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__("delphi-review-agent")
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
        self.findings = []

    async def execute(self, context: Dict[str, Any]) -> AgentReport:
        self.status = AgentStatus.RUNNING
        code = context.get("code", "")
        file_name = context.get("file_name", "Unknown")

        prompt = f"""
        Você é um Arquiteto de Software Sênior especialista em Delphi e Oracle.
        Analise o código abaixo do arquivo {file_name} buscando por:
        1. Memory Leaks (objetos não destruídos)
        2. SQL Injection e falta de uso de Parameters
        3. Falta de controle transacional (Commit/Rollback)
        4. Problemas de performance e concorrência

        Código:
        {code}
        """

        for model_name in self.model_priorities:
            try:
                print(f"[DelphiReviewAgent] Tentando modelo: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                self.findings = [{"type": "code_review", "content": response.text}]
                self.status = AgentStatus.COMPLETED
                return self.generate_report()
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    print(f"[DelphiReviewAgent] Cota excedida no modelo {model_name}. Tentando próximo...")
                    continue
                else:
                    print(f"[DelphiReviewAgent] Erro na API ({model_name}): {e}")
                    break
        
        self.status = AgentStatus.FAILED
        return self.generate_report()

    async def validate(self, result: Any) -> bool:
        return self.status == AgentStatus.COMPLETED

    async def rollback(self) -> bool:
        return True

    def generate_report(self) -> AgentReport:
        return AgentReport(
            agent_id=self.agent_id,
            status=self.status,
            findings=self.findings,
            recommendations=["Considere as refatorações sugeridas pela IA."],
            metadata={"model_used": "multiple-fallback"}
        )
