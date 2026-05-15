import os
from typing import Any, Dict, List
from shared.base_agent import BaseAgent, AgentStatus, AgentReport
import google.generativeai as genai

class DocumentationAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__("documentation-agent")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.findings = []

    async def execute(self, context: Dict[str, Any]) -> AgentReport:
        """
        Mapeia os arquivos do ERP e gera documentação técnica vetorizada.
        """
        self.status = AgentStatus.RUNNING
        project_path = context.get("project_path", ".")
        
        # Simula o mapeamento de arquivos Delphi (.pas, .dfm) e SQL
        target_extensions = ['.pas', '.dfm', '.sql']
        
        for root, _, files in os.walk(project_path):
            for file in files:
                if any(file.endswith(ext) for ext in target_extensions):
                    file_path = os.path.join(root, file)
                    await self._process_file(file_path)

        self.status = AgentStatus.COMPLETED
        return self.generate_report()

    async def _process_file(self, file_path: str):
        """Processa um arquivo individual para gerar sua documentação."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Prompt para mapeamento técnico
            prompt = f"""
            Analise o seguinte arquivo de um sistema ERP Delphi:
            Caminho: {file_path}
            Conteúdo:
            {content[:5000]} 

            Gere um resumo técnico conciso incluindo:
            1. Propósito do módulo.
            2. Principais dependências (outras units ou tabelas SQL).
            3. Fluxos de negócio afetados (ex: Pedido, NF-e, Estoque).
            4. Nível de risco para modificação.
            """
            
            response = self.model.generate_content(prompt)
            summary = response.text

            self.findings.append({
                "file": file_path,
                "summary": summary,
                "type": "mapping"
            })
            
            # Aqui o agente salvaria no banco de dados vetorizado (ERPMapping)
            print(f"[DocAgent] Mapeado: {file_path}")

        except Exception as e:
            print(f"[DocAgent] Erro ao processar {file_path}: {e}")

    async def validate(self, result: Any) -> bool:
        return len(self.findings) > 0

    async def rollback(self) -> bool:
        self.findings = []
        return True

    def generate_report(self) -> AgentReport:
        return AgentReport(
            agent_id=self.agent_id,
            status=self.status,
            findings=self.findings,
            recommendations=["Atualizar o índice vetorial regularmente.", "Validar fluxos de NF-e após mudanças em units de impostos."],
            metadata={"files_processed": len(self.findings)}
        )
