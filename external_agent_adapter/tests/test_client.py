import json
from io import BytesIO
from urllib.error import HTTPError

import pytest

from external_agent_adapter import AdapterError, ExternalAgentAdapter


class FakeResponse:
    def __init__(self, payload, status=200):
        self.status = status
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self._body


class FakeOpener:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        if isinstance(self.response, HTTPError):
            raise self.response
        return self.response


def test_adapter_builds_existing_rest_requests():
    opener = FakeOpener(FakeResponse({"investigations": []}))
    adapter = ExternalAgentAdapter(
        "http://red-king.local/",
        timeout=4.5,
        allowed_storage_keys={"red_king.workflow.v1"},
        opener=opener,
    )

    adapter.list_investigations(status="open", query="login")
    request, timeout = opener.requests[-1]
    assert request.full_url == "http://red-king.local/api/investigations?status=open&q=login"
    assert request.get_method() == "GET"
    assert timeout == 4.5

    opener.response = FakeResponse({"investigation": {"id": "inv-1"}})
    adapter.create_investigation("Review login", status="open")
    request, _ = opener.requests[-1]
    assert request.get_method() == "POST"
    assert json.loads(request.data) == {"title": "Review login", "status": "open"}


def test_adapter_exposes_context_and_controlled_storage():
    opener = FakeOpener(FakeResponse({"status": "OK"}))
    adapter = ExternalAgentAdapter(
        "http://red-king.local",
        allowed_storage_keys={"workflow/key"},
        opener=opener,
    )

    adapter.status()
    assert opener.requests[-1][0].full_url.endswith("/api/status")
    adapter.dashboard()
    assert opener.requests[-1][0].full_url.endswith("/api/dashboard")
    adapter.investigation_timeline("inv/1")
    assert opener.requests[-1][0].full_url.endswith("/api/investigations/inv%2F1/timeline")
    adapter.investigation_evidence("inv-1")
    assert opener.requests[-1][0].full_url.endswith("/api/investigations/inv-1/evidence")
    adapter.get_storage("workflow/key")
    assert opener.requests[-1][0].full_url.endswith("/api/storage/workflow%2Fkey")

    with pytest.raises(PermissionError):
        adapter.get_storage("unapproved")
    with pytest.raises(PermissionError):
        adapter.set_storage("unapproved", {"value": True})


def test_adapter_preserves_api_errors():
    error = HTTPError(
        "http://red-king.local/api/investigations",
        404,
        "missing",
        {},
        BytesIO(b'{"detail":"Investigation not found"}'),
    )
    adapter = ExternalAgentAdapter("http://red-king.local", opener=FakeOpener(error))

    with pytest.raises(AdapterError) as caught:
        adapter.update_investigation("missing", status="closed")

    assert caught.value.status == 404
    assert caught.value.message == "Investigation not found"
    assert caught.value.payload == {"detail": "Investigation not found"}
