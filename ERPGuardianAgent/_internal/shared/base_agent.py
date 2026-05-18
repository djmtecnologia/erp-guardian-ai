from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK = "rollback"

class AgentReport(BaseModel):
    agent_id: str
    status: AgentStatus
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    metadata: Dict[str, Any] = {}

class BaseAgent(ABC):
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.status = AgentStatus.IDLE

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> AgentReport:
        """Main execution logic for the agent."""
        pass

    @abstractmethod
    async def validate(self, result: Any) -> bool:
        """Validate the output of the execution."""
        pass

    @abstractmethod
    async def rollback(self) -> bool:
        """Revert changes if validation fails."""
        pass

    @abstractmethod
    def generate_report(self) -> AgentReport:
        """Generate a structured report of the agent findings."""
        pass

    def get_status(self) -> AgentStatus:
        """Return the current status of the agent."""
        return self.status
