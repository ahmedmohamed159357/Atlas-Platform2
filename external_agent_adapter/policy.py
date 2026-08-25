"""Explicit, side-effect-free execution capabilities for orchestration."""

from __future__ import annotations

from typing import Iterable, FrozenSet


class PolicyError(PermissionError):
    """Raised when an operation is not permitted by an execution policy."""


class AgentExecutionPolicy:
    """Immutable allowlist for the operations an orchestrator may execute."""

    KNOWN_OPERATIONS = frozenset(
        {
            "status",
            "dashboard",
            "list_investigations",
            "create_investigation",
            "update_investigation",
            "investigation_timeline",
            "investigation_evidence",
            "get_storage",
            "set_storage",
            "delete_storage",
        }
    )
    READ_OPERATIONS = frozenset(
        {
            "status",
            "dashboard",
            "list_investigations",
            "investigation_timeline",
            "investigation_evidence",
            "get_storage",
        }
    )
    MUTATING_OPERATIONS = frozenset(
        {"create_investigation", "update_investigation", "set_storage", "delete_storage"}
    )

    def __init__(self, allowed_operations: Iterable[str] = ()) -> None:
        operations = frozenset(allowed_operations)
        unknown = operations - self.KNOWN_OPERATIONS
        if unknown:
            names = ", ".join(sorted(unknown))
            raise ValueError(f"Unknown orchestrator operation(s): {names}")
        self._allowed_operations: FrozenSet[str] = operations

    @property
    def allowed_operations(self) -> FrozenSet[str]:
        return self._allowed_operations

    def permits(self, operation: str) -> bool:
        self._validate_known(operation)
        return operation in self._allowed_operations

    def require(self, operation: str) -> None:
        self._validate_known(operation)
        if operation not in self._allowed_operations:
            raise PolicyError(f"Operation is not permitted: {operation}")

    @classmethod
    def read_only(cls) -> AgentExecutionPolicy:
        return cls(cls.READ_OPERATIONS)

    @classmethod
    def compatibility(cls) -> AgentExecutionPolicy:
        """Preserve Phase 24/25 default behavior for existing callers."""
        return cls(cls.KNOWN_OPERATIONS)

    @classmethod
    def explicit(cls, operations: Iterable[str]) -> AgentExecutionPolicy:
        return cls(operations)

    @classmethod
    def _validate_known(cls, operation: str) -> None:
        if operation not in cls.KNOWN_OPERATIONS:
            raise ValueError(f"Unknown orchestrator operation: {operation}")