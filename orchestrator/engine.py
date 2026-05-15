from typing import List, Dict, Any
from shared.base_agent import BaseAgent, AgentReport
import asyncio

class OrchestrationEngine:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.execution_history: List[AgentReport] = []

    def register_agent(self, agent: BaseAgent):
        self.agents[agent.agent_id] = agent
        print(f"[Orchestrator] Agente registrado: {agent.agent_id}")

    async def run_standalone(self, agent_id: str, context: Dict[str, Any]) -> AgentReport:
        """Executa um único agente isoladamente."""
        if agent_id not in self.agents:
            raise ValueError(f"Agente {agent_id} não encontrado.")
        
        print(f"[Orchestrator] Iniciando execução standalone: {agent_id}")
        report = await self.agents[agent_id].execute(context)
        self.execution_history.append(report)
        return report

    async def run_pipeline(self, pipeline: List[str], initial_context: Dict[str, Any]) -> List[AgentReport]:
        """Executa uma sequência de agentes em pipeline."""
        print(f"[Orchestrator] Iniciando pipeline: {' -> '.join(pipeline)}")
        context = initial_context.copy()
        reports = []

        for agent_id in pipeline:
            report = await self.run_standalone(agent_id, context)
            reports.append(report)
            
            # Atualiza o contexto com as descobertas do agente anterior para o próximo
            context[f"last_findings_{agent_id}"] = report.findings
            
            if report.status.value == "failed":
                print(f"[Orchestrator] Pipeline interrompido: Falha no agente {agent_id}")
                break

        return reports
