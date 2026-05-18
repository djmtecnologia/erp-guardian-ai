from typing import List, Dict, Any, Callable, Union
from shared.base_agent import BaseAgent, AgentStatus, AgentReport
import asyncio
import logging

# Configuração básica de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WorkflowEngine")

class WorkflowTask(BaseAgent):
    """
    Representa uma tarefa determinística repetitiva (sem IA).
    Herda de BaseAgent para manter a compatibilidade de interface.
    """
    def __init__(self, task_id: str, action: Callable[[Dict[str, Any]], Any]):
        super().__init__(task_id)
        self.action = action

    async def execute(self, context: Dict[str, Any]) -> AgentReport:
        self.status = AgentStatus.RUNNING
        try:
            logger.info(f"[Task] Executando tarefa determinística: {self.agent_id}")
            result = await asyncio.to_thread(self.action, context)
            self.status = AgentStatus.COMPLETED
            return AgentReport(
                agent_id=self.agent_id,
                status=self.status,
                findings=[{"result": result}],
                recommendations=[],
                metadata={"type": "deterministic"}
            )
        except Exception as e:
            logger.error(f"[Task] Erro na tarefa {self.agent_id}: {e}")
            self.status = AgentStatus.FAILED
            return AgentReport(agent_id=self.agent_id, status=self.status, findings=[{"error": str(e)}], recommendations=[])

    async def validate(self, result: Any) -> bool:
        return True

    async def rollback(self) -> bool:
        return True

    def generate_report(self) -> AgentReport:
        return AgentReport(agent_id=self.agent_id, status=self.status, findings=[], recommendations=[])

class HybridWorkflow:
    """
    Orquestrador Híbrido: Combina tarefas determinísticas (repetitivas) 
    com agentes de IA (dinâmicos).
    """
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.steps: List[Union[BaseAgent, WorkflowTask]] = []
        self.context: Dict[str, Any] = {}

    def add_deterministic_step(self, task_id: str, action: Callable[[Dict[str, Any]], Any]):
        """Adiciona uma tarefa repetitiva que não usa IA."""
        task = WorkflowTask(task_id, action)
        self.steps.append(task)
        return self

    def add_agent_step(self, agent: BaseAgent):
        """Adiciona um agente de IA para tarefas dinâmicas."""
        self.steps.append(agent)
        return self

    async def run(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[Workflow] Iniciando workflow híbrido: {self.workflow_id}")
        self.context = initial_context.copy()
        
        execution_results = []
        
        for step in self.steps:
            logger.info(f"[Workflow] Executando Passo: {step.agent_id}")
            
            report = await step.execute(self.context)
            execution_results.append(report)
            
            # Atualiza o contexto global do workflow com os resultados deste passo
            self.context[f"result_{step.agent_id}"] = report.findings
            
            if report.status == AgentStatus.FAILED:
                logger.error(f"[Workflow] Falha crítica no passo {step.agent_id}. Interrompendo.")
                break
        
        self.context["workflow_status"] = "finished"
        self.context["execution_history"] = execution_results
        return self.context
