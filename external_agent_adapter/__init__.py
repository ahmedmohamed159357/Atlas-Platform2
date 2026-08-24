"""Standalone Red King REST adapter for external orchestrators."""

from .client import AdapterError, ExternalAgentAdapter
from .lifecycle import AgentJobLifecycle

__all__ = ["AdapterError", "AgentJobLifecycle", "ExternalAgentAdapter"]
