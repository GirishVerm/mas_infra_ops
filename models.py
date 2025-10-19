from __future__ import annotations

from typing import Dict, List, Optional, Union

from pydantic import BaseModel


class AgentSpec(BaseModel):
    name: str
    model: str
    task: str
    # Accept string or list of strings (AND semantics if list)
    depends_on: Optional[Union[str, List[str]]] = None


class WorkflowSpec(BaseModel):
    name: str
    description: Optional[str] = None
    policies: Dict[str, float] = {}
    agents: List[AgentSpec]


class AgentRun(BaseModel):
    name: str
    status: str
    cost: float
    output: Optional[str] = None
    error: Optional[str] = None
    retries: int = 0


