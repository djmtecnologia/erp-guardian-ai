import google.generativeai as genai
from typing import Any, Dict, List
from shared.base_agent import BaseAgent, AgentStatus, AgentReport

class DelphiReviewAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__("delphi-review-agent")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro') # Pro é melhor para Code Review
        self.findings = []

    async def execute(self, context: Dict[str, Any]) -> AgentReport:
        """
        Executa revisão de código Delphi focada em ERP (VCL, Memory Leaks, SQL).
        """
        self.status = AgentStatus.RUNNING
        code_content = context.get("code", "")
        file_name = context.get("file_name", "unknown.pas")

        prompt = f"""
        Você é um Especialista em Delphi e Arquiteto de ERP.
        Revise o seguinte código Delphi (.pas):
        Arquivo: {file_name}

        Código:
        {code_content}

        Foque em:
        1. Memory Leaks (Try-Finally blocks ausentes).
        2. SQL Injection em queries dinâmicas.
        3. Validação de Transações (Commit/Rollback).
        4. Performance em loops e acesso a banco.
        5. Violações de arquitetura ERP legada.

        Retorne um JSON com a lista de problemas encontrados:
        {{ "issues": [ {{ "line": int, "severity": "LOW|MEDIUM|HIGH|CRITICAL", "description": str, "fix": str }} ] }}
        """

        try:
            response = self.model.generate_content(prompt)
            # Em uma implementação real, faríamos o parse do JSON aqui
            self.findings.append({
                "file": file_name,
                "review": response.text
            })
            self.status = AgentStatus.COMPLETED
        except Exception as e:
            self.findings.append({"error": str(e)})
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
            recommendations=["Sempre use try..finally ao instanciar objetos.", "Use parâmetros em queries SQL."],
            metadata={"model": "gemini-1.5-pro"}
        )
