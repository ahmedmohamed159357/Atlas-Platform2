"""Minimal, independently replaceable client for the Red King REST contract."""

from __future__ import annotations

import json
from typing import Any, Callable, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import OpenerDirector, Request, build_opener


class AdapterError(RuntimeError):
    """A failed Red King request with its HTTP status and decoded payload."""

    def __init__(self, status: int, message: str, payload: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.payload = payload


class ExternalAgentAdapter:
    """Small REST client exposing only non-destructive orchestration operations."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 10.0,
        allowed_storage_keys: Optional[set[str]] = None,
        opener: Optional[OpenerDirector] = None,
    ) -> None:
        normalized_url = base_url.strip().rstrip("/")
        if not normalized_url:
            raise ValueError("base_url is required")
        self.base_url = normalized_url
        self.timeout = timeout
        self.allowed_storage_keys = frozenset(allowed_storage_keys or set())
        self._opener = opener or build_opener()

    def status(self) -> dict[str, Any]:
        return self._request("GET", "/api/status")

    def dashboard(self) -> dict[str, Any]:
        return self._request("GET", "/api/dashboard")

    def list_investigations(
        self, *, status: Optional[str] = None, query: Optional[str] = None
    ) -> dict[str, Any]:
        params = {key: value for key, value in (("status", status), ("q", query)) if value is not None}
        return self._request("GET", "/api/investigations", params=params)

    def create_investigation(self, title: str, *, status: str = "open") -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/investigations",
            payload={"title": title, "status": status},
        )

    def update_investigation(
        self,
        investigation_id: str,
        *,
        title: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict[str, Any]:
        payload = {key: value for key, value in (("title", title), ("status", status)) if value is not None}
        return self._request("PUT", self._investigation_path(investigation_id), payload=payload)

    def investigation_timeline(self, investigation_id: str) -> dict[str, Any]:
        return self._request("GET", f"{self._investigation_path(investigation_id)}/timeline")

    def investigation_evidence(self, investigation_id: str) -> dict[str, Any]:
        return self._request("GET", f"{self._investigation_path(investigation_id)}/evidence")

    def get_storage(self, key: str) -> dict[str, Any]:
        self._require_storage_key(key)
        return self._request("GET", f"/api/storage/{quote(key, safe='')}")

    def set_storage(self, key: str, value: Any) -> dict[str, Any]:
        self._require_storage_key(key)
        return self._request("POST", f"/api/storage/{quote(key, safe='')}", payload={"value": value})

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, str]] = None,
        payload: Any = None,
    ) -> dict[str, Any]:
        query = f"?{urlencode(params)}" if params else ""
        request = Request(
            f"{self.base_url}{path}{query}",
            method=method,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        if payload is not None:
            request.data = json.dumps(payload).encode("utf-8")

        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                return self._decode_response(response.read(), response.status)
        except HTTPError as error:
            response_payload = self._decode_response_body(error.read())
            message = response_payload.get("detail", "Request failed") if isinstance(response_payload, dict) else "Request failed"
            raise AdapterError(error.code, str(message), response_payload) from error
        except URLError as error:
            raise AdapterError(0, f"Unable to reach Red King: {error.reason}") from error

    @staticmethod
    def _decode_response(body: bytes, status: int) -> dict[str, Any]:
        payload = ExternalAgentAdapter._decode_response_body(body)
        if not isinstance(payload, dict):
            raise AdapterError(status, "Expected a JSON object response", payload)
        return payload

    @staticmethod
    def _decode_response_body(body: bytes) -> Any:
        if not body:
            return {}
        try:
            return json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise AdapterError(0, "Red King returned invalid JSON") from error

    @staticmethod
    def _investigation_path(investigation_id: str) -> str:
        return f"/api/investigations/{quote(investigation_id, safe='')}"

    def _require_storage_key(self, key: str) -> None:
        if key not in self.allowed_storage_keys:
            raise PermissionError(f"Storage key is not allowlisted: {key}")
