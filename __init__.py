"""
AgentOps - A minimal orchestration runtime for multi-agent workflows.
"""

__version__ = "0.1.0"
__author__ = "Girish Verma"

try:
    from .main import main
    from .orchestrator import execute_workflow
    from .models import AgentSpec, WorkflowSpec, AgentRun
except ImportError:
    from main import main
    from orchestrator import execute_workflow
    from models import AgentSpec, WorkflowSpec, AgentRun

__all__ = [
    "main",
    "execute_workflow", 
    "AgentSpec",
    "WorkflowSpec",
    "AgentRun",
]
