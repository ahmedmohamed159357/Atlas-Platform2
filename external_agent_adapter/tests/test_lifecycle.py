from datetime import datetime, timezone

import pytest

from external_agent_adapter import AgentJobLifecycle, ExternalAgentAdapter


def test_job_lifecycle_tracks_submission_success_result_and_timestamps():
    timestamps = iter(
        (
            datetime(2026, 8, 24, 8, 0, tzinfo=timezone.utc),
            datetime(2026, 8, 24, 8, 1, tzinfo=timezone.utc),
        )
    )
    lifecycle = AgentJobLifecycle(
        ExternalAgentAdapter("http://red-king.local"),
        clock=lambda: next(timestamps),
        id_factory=lambda: "job-1",
    )

    submitted = lifecycle.submit({"prompt": "inspect"})
    assert submitted["job_id"] == "job-1"
    assert submitted["status"] == "submitted"
    assert submitted["submitted_at"] == "2026-08-24T08:00:00Z"
    assert submitted["completed_at"] is None

    completed = lifecycle.success("job-1", {"answer": "complete"})
    assert completed["status"] == "succeeded"
    assert lifecycle.status("job-1")["status"] == "succeeded"
    assert lifecycle.result("job-1") == {"answer": "complete"}
    assert completed["completed_at"] == "2026-08-24T08:01:00Z"
    assert completed["updated_at"] == completed["completed_at"]


def test_job_lifecycle_tracks_failure_and_rejects_terminal_updates():
    lifecycle = AgentJobLifecycle(
        ExternalAgentAdapter("http://red-king.local"), id_factory=lambda: "job-2"
    )

    lifecycle.submit({"task": "inspect"})
    failed = lifecycle.failure("job-2", RuntimeError("upstream unavailable"))

    assert failed["status"] == "failed"
    assert failed["error"] == "upstream unavailable"
    assert lifecycle.result("job-2") is None
    with pytest.raises(ValueError, match="already complete"):
        lifecycle.success("job-2", "late result")


def test_job_lifecycle_rejects_unknown_and_duplicate_jobs():
    lifecycle = AgentJobLifecycle(
        ExternalAgentAdapter("http://red-king.local"), id_factory=lambda: "job-3"
    )

    with pytest.raises(KeyError, match="Unknown job"):
        lifecycle.status("missing")

    lifecycle.submit({})
    with pytest.raises(ValueError, match="already exists"):
        lifecycle.submit({}, job_id="job-3")