from external_agent_adapter import (
    AgentJobLifecycle,
    ExternalAgentAdapter,
    ExternalAgentOrchestrator,
)
from itertools import count


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
    assert job["error"] == "upstream unavailable"


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