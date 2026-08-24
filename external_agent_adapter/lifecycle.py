"""In-memory lifecycle tracking for jobs submitted through an agent adapter."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from uuid import uuid4

from .client import ExternalAgentAdapter


class AgentJobLifecycle:
    """Track an external agent job without owning execution or persistence."""

    def __init__(
        self,
        adapter: ExternalAgentAdapter,
        *,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.adapter = adapter
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._id_factory = id_factory or (lambda: str(uuid4()))
        self._jobs: dict[str, dict[str, Any]] = {}

    def submit(self, payload: Any, *, job_id: Optional[str] = None) -> dict[str, Any]:
        resolved_job_id = job_id or self._id_factory()
        if resolved_job_id in self._jobs:
            raise ValueError(f"Job already exists: {resolved_job_id}")

        timestamp = self._timestamp()
        self._jobs[resolved_job_id] = {
            "job_id": resolved_job_id,
            "status": "submitted",
            "payload": deepcopy(payload),
            "result": None,
            "error": None,
            "submitted_at": timestamp,
            "completed_at": None,
            "updated_at": timestamp,
        }
        return self._snapshot(resolved_job_id)

    def status(self, job_id: str) -> dict[str, Any]:
        return self._snapshot(job_id)

    def result(self, job_id: str) -> Any:
        job = self._job(job_id)
        return deepcopy(job["result"])

    def success(self, job_id: str, result: Any = None) -> dict[str, Any]:
        return self._complete(job_id, status="succeeded", result=result)

    def failure(self, job_id: str, error: Any) -> dict[str, Any]:
        return self._complete(job_id, status="failed", error=str(error))

    def _complete(
        self,
        job_id: str,
        *,
        status: str,
        result: Any = None,
        error: Optional[str] = None,
    ) -> dict[str, Any]:
        job = self._job(job_id)
        if job["status"] in {"succeeded", "failed"}:
            raise ValueError(f"Job is already complete: {job_id}")

        timestamp = self._timestamp()
        job.update(
            {
                "status": status,
                "result": deepcopy(result),
                "error": error,
                "completed_at": timestamp,
                "updated_at": timestamp,
            }
        )
        return self._snapshot(job_id)

    def _job(self, job_id: str) -> dict[str, Any]:
        try:
            return self._jobs[job_id]
        except KeyError as error:
            raise KeyError(f"Unknown job: {job_id}") from error

    def _snapshot(self, job_id: str) -> dict[str, Any]:
        return deepcopy(self._job(job_id))

    def _timestamp(self) -> str:
        timestamp = self._clock()
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")