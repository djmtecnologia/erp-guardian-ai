import os
from typing import Any, Dict, List
from shared.base_agent import BaseAgent, AgentStatus, AgentReport
import google.generativeai as genai

class SupportResolutionAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__("support-resolution-agent")
        genai.configure(api_key=api_key)
        self.model_priorities = [
            'gemini-2.0-flash', 
            'gemini-pro-latest',
            'gemini-1.5-pro-latest',
            'gemini-1.5-flash'
        ]
        self.findings = []

    async def execute(self, context: Dict[str, Any]) -> AgentReport:
        self.status = AgentStatus.RUNNING
        ticket_description = context.get("description", "Nenhuma descrição fornecida.")
        files = context.get("files", []) # Lista de caminhos de arquivos

        prompt_parts = [
            f"Você é um Desenvolvedor Sênior de Delphi e Especialista em Suporte Técnico Nível 3.\n",
            f"Temos o seguinte chamado de suporte relatado pelo usuário/cliente:\n",
            f"--- DESCRIÇÃO DO CHAMADO ---\n{ticket_description}\n---------------------------\n\n",
            "Sua tarefa é analisar as evidências e o código fornecido, e então apresentar:\n",
            "1. A Causa Raiz provável do problema.\n",
            "2. A Solução Técnica exata (o que precisa ser alterado no código ou no banco).\n",
            "3. Um trecho de código corrigido, se aplicável.\n\n",
            "Abaixo estão os anexos e códigos fornecidos:\n"
        ]

        uploaded_files = []
        try:
            for file_path in files:
                if not os.path.exists(file_path):
                    continue
                
                ext = file_path.lower().split('.')[-1]
                # Se for imagem, faz upload para o Gemini
                if ext in ['png', 'jpg', 'jpeg', 'webp']:
                    print(f"[SupportAgent] Fazendo upload da imagem: {file_path}")
                    uploaded_file = genai.upload_file(path=file_path)
                    uploaded_files.append(uploaded_file)
                    prompt_parts.append(uploaded_file)
                    prompt_parts.append(f"Evidência: {os.path.basename(file_path)}\n")
                
                # Se for código ou texto, lê e insere no prompt
                elif ext in ['pas', 'dfm', 'sql', 'txt', 'log']:
                    print(f"[SupportAgent] Lendo código-fonte: {file_path}")
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        prompt_parts.append(f"--- ARQUIVO: {os.path.basename(file_path)} ---\n{content}\n----------------\n")
            
            # Executa com fallback de modelos
            for model_name in self.model_priorities:
                try:
                    print(f"[SupportAgent] Analisando com {model_name}...")
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt_parts)
                    self.findings = [{"type": "support_resolution", "content": response.text}]
                    self.status = AgentStatus.COMPLETED
                    break
                except Exception as e:
                    if "429" in str(e):
                        continue
                    raise e
            
            if self.status != AgentStatus.COMPLETED:
                raise Exception("Todos os modelos de IA falharam (possível falta de cota).")

        except Exception as e:
            print(f"[SupportAgent] Erro crítico: {e}")
            self.status = AgentStatus.FAILED
            self.findings = [{"error": str(e)}]
        finally:
            # Limpa arquivos enviados para o Google (boa prática de segurança)
            for uf in uploaded_files:
                try:
                    genai.delete_file(uf.name)
                except:
                    pass

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
            recommendations=["Teste a solução em ambiente de homologação."],
            metadata={"ticket_analyzed": True}
        )
