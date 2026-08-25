from pathlib import Path

from external_agent_adapter import (
    AdapterError,
    AgentJobLifecycle,
    AgentExecutionPolicy,
    ExternalAgentAdapter,
    ExternalAgentOrchestrator,
)
from itertools import count

import pytest


class FakeAdapter:
    def __init__(self, result=None, error=None):
        self.result = result or {"status": "OK"}
        self.error = error
        self.calls = []

    def status(self):
        self.calls.append(("status",))
        if self.error:
            raise self.error
        return self.result


def make_orchestrator(adapter):
    lifecycle = AgentJobLifecycle(adapter, id_factory=iter(("job-1", "job-2")).__next__)
    return ExternalAgentOrchestrator(adapter, lifecycle)


def test_orchestrator_records_success_and_captures_result_with_injected_adapter():
    adapter = FakeAdapter({"system": "ONLINE"})
    orchestrator = make_orchestrator(adapter)

    job = orchestrator.run_status()

    assert adapter.calls == [("status",)]
    assert job["job_id"] == "job-1"
    assert job["status"] == "succeeded"
    assert job["result"] == {"system": "ONLINE"}
    assert job["payload"] == {"operation": "status", "arguments": {}}
    assert orchestrator.get_job("job-1") == job


def test_orchestrator_records_failure_and_captures_error():
    adapter = FakeAdapter(error=RuntimeError("upstream unavailable"))
    orchestrator = make_orchestrator(adapter)

    job = orchestrator.run_status()

    assert job["status"] == "failed"
    assert job["result"] is None
    assert job["error"] == {
        "type": "operation_error",
        "message": "upstream unavailable",
    }


def test_orchestrator_captures_public_structured_adapter_error():
    adapter = FakeAdapter(
        error=AdapterError(404, "Investigation not found", {"detail": "missing"})
    )
    orchestrator = make_orchestrator(adapter)

    job = orchestrator.run_status()

    assert job["status"] == "failed"
    assert job["error"] == {
        "type": "adapter_error",
        "message": "Investigation not found",
        "status": 404,
        "details": {"detail": "missing"},
    }
    assert orchestrator.get_job(job["job_id"])["error"] == job["error"]


def test_invalid_arguments_are_rejected_before_adapter_invocation():
    adapter = FakeAdapter()
    orchestrator = make_orchestrator(adapter)

    for operation in (
        lambda: orchestrator.run_create_investigation("  "),
        lambda: orchestrator.run_update_investigation("inv-1"),
        lambda: orchestrator.run_investigation_timeline(""),
        lambda: orchestrator.run_get_storage(" "),
        lambda: orchestrator.run_list_investigations(status=42),
    ):
        with pytest.raises(ValueError):
            operation()

    assert adapter.calls == []


def test_orchestrator_allows_only_one_terminal_transition():
    adapter = FakeAdapter(error=RuntimeError("upstream unavailable"))
    orchestrator = make_orchestrator(adapter)

    job = orchestrator.run_status()

    assert job["status"] == "failed"
    with pytest.raises(ValueError, match="already complete"):
        orchestrator.lifecycle.success(job["job_id"], {"late": True})


def test_orchestrator_has_no_core_or_ranking_imports():
    source = (Path(__file__).parents[1] / "orchestrator.py").read_text()

    assert "import core" not in source
    assert "import ranking" not in source
    assert "from core" not in source
    assert "from ranking" not in source


def test_compatibility_policy_preserves_existing_default_behavior():
    adapter = FakeAdapter()
    orchestrator = make_orchestrator(adapter)

    assert orchestrator.run_status()["status"] == "succeeded"
    assert orchestrator.policy.allowed_operations == AgentExecutionPolicy.KNOWN_OPERATIONS


def test_explicit_policy_rejects_before_adapter_invocation():
    adapter = FakeAdapter()
    lifecycle = AgentJobLifecycle(adapter, id_factory=lambda: "job-policy")
    orchestrator = ExternalAgentOrchestrator(
        adapter, lifecycle, policy=AgentExecutionPolicy.read_only()
    )

    with pytest.raises(PermissionError, match="not permitted"):
        orchestrator.run_create_investigation("Review login")

    assert adapter.calls == []
    with pytest.raises(KeyError, match="Unknown job"):
        orchestrator.get_job("job-policy")


def test_orchestrator_generates_unique_job_ids():
    adapter = FakeAdapter()
    orchestrator = make_orchestrator(adapter)

    first = orchestrator.run_status()
    second = orchestrator.run_status()

    assert first["job_id"] != second["job_id"]


def test_orchestrator_delegates_explicit_supported_operations():
    adapter = ExternalAgentAdapter("http://red-king.local")
    ids = count(3)
    lifecycle = AgentJobLifecycle(adapter, id_factory=lambda: f"job-{next(ids)}")
    orchestrator = ExternalAgentOrchestrator(adapter, lifecycle)
    calls = []

    adapter.status = lambda: calls.append("status") or {"status": "OK"}
    adapter.dashboard = lambda: calls.append("dashboard") or {"status": "OK"}
    adapter.list_investigations = lambda **kwargs: calls.append(("list", kwargs)) or {}
    adapter.create_investigation = lambda title, status="open": calls.append(("create", title, status)) or {}
    adapter.update_investigation = lambda investigation_id, **kwargs: calls.append(("update", investigation_id, kwargs)) or {}
    adapter.investigation_timeline = lambda investigation_id: calls.append(("timeline", investigation_id)) or {}
    adapter.investigation_evidence = lambda investigation_id: calls.append(("evidence", investigation_id)) or {}
    adapter.get_storage = lambda key: calls.append(("get", key)) or {}
    adapter.set_storage = lambda key, value: calls.append(("set", key, value)) or {}
    adapter.delete_storage = lambda key: calls.append(("delete_storage", key)) or {}

    orchestrator.run_status()
    orchestrator.run_dashboard()
    orchestrator.run_list_investigations(status="open", query="login")
    orchestrator.run_create_investigation("Review login")
    orchestrator.run_update_investigation("inv-1", status="closed")
    orchestrator.run_investigation_timeline("inv-1")
    orchestrator.run_investigation_evidence("inv-1")
    orchestrator.run_get_storage("workflow/key")
    orchestrator.run_set_storage("workflow/key", {"ready": True})
    orchestrator.run_delete_storage("workflow/key")

    assert calls == [
        "status",
        "dashboard",
        ("list", {"status": "open", "query": "login"}),
        ("create", "Review login", "open"),
        ("update", "inv-1", {"title": None, "status": "closed"}),
        ("timeline", "inv-1"),
        ("evidence", "inv-1"),
        ("get", "workflow/key"),
        ("set", "workflow/key", {"ready": True}),
        ("delete_storage", "workflow/key"),
    ]