"""Standalone Red King REST adapter for external orchestrators."""

from .client import AdapterError, ExternalAgentAdapter
from .lifecycle import AgentJobLifecycle
from .orchestrator import ExternalAgentOrchestrator

__all__ = [
	"AdapterError",
	"AgentJobLifecycle",
	"ExternalAgentAdapter",
	"ExternalAgentOrchestrator",
]
