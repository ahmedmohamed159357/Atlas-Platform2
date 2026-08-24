"""Transport-independent orchestration over the external agent adapter."""

from __future__ import annotations

from typing import Any, Callable, Optional

from .client import ExternalAgentAdapter
from .lifecycle import AgentJobLifecycle


class ExternalAgentOrchestrator:
    """Run explicit adapter operations and record their job lifecycle."""

    def __init__(
        self,
        adapter: ExternalAgentAdapter,
        lifecycle: AgentJobLifecycle,
    ) -> None:
        self.adapter = adapter
        self.lifecycle = lifecycle

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self.lifecycle.status(job_id)

    def run_status(self) -> dict[str, Any]:
        return self._run("status", {}, self.adapter.status)

    def run_dashboard(self) -> dict[str, Any]:
        return self._run("dashboard", {}, self.adapter.dashboard)

    def run_list_investigations(
        self, *, status: Optional[str] = None, query: Optional[str] = None
    ) -> dict[str, Any]:
        arguments = {key: value for key, value in (("status", status), ("query", query)) if value is not None}
        return self._run(
            "list_investigations",
            arguments,
            lambda: self.adapter.list_investigations(status=status, query=query),
        )

    def run_create_investigation(self, title: str, *, status: str = "open") -> dict[str, Any]:
        return self._run(
            "create_investigation",
            {"title": title, "status": status},
            lambda: self.adapter.create_investigation(title, status=status),
        )

    def run_update_investigation(
        self,
        investigation_id: str,
        *,
        title: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict[str, Any]:
        arguments = {
            key: value
            for key, value in (
                ("investigation_id", investigation_id),
                ("title", title),
                ("status", status),
            )
            if value is not None
        }
        return self._run(
            "update_investigation",
            arguments,
            lambda: self.adapter.update_investigation(
                investigation_id, title=title, status=status
            ),
        )

    def run_investigation_timeline(self, investigation_id: str) -> dict[str, Any]:
        return self._run(
            "investigation_timeline",
            {"investigation_id": investigation_id},
            lambda: self.adapter.investigation_timeline(investigation_id),
        )

    def run_investigation_evidence(self, investigation_id: str) -> dict[str, Any]:
        return self._run(
            "investigation_evidence",
            {"investigation_id": investigation_id},
            lambda: self.adapter.investigation_evidence(investigation_id),
        )

    def run_get_storage(self, key: str) -> dict[str, Any]:
        return self._run(
            "get_storage",
            {"key": key},
            lambda: self.adapter.get_storage(key),
        )

    def run_set_storage(self, key: str, value: Any) -> dict[str, Any]:
        return self._run(
            "set_storage",
            {"key": key, "value": value},
            lambda: self.adapter.set_storage(key, value),
        )

    def run_delete_storage(self, key: str) -> dict[str, Any]:
        return self._run(
            "delete_storage",
            {"key": key},
            lambda: self._delete_storage(key),
        )

    def _delete_storage(self, key: str) -> Any:
        delete_storage = getattr(self.adapter, "delete_storage", None)
        if delete_storage is None:
            raise NotImplementedError("The adapter does not support storage deletion")
        return delete_storage(key)

    def _run(
        self,
        operation: str,
        arguments: dict[str, Any],
        action: Callable[[], Any],
    ) -> dict[str, Any]:
        job = self.lifecycle.submit({"operation": operation, "arguments": arguments})
        job_id = job["job_id"]
        try:
            return self.lifecycle.success(job_id, action())
        except Exception as error:
            return self.lifecycle.failure(job_id, error)