# External Agent Integration Contract

Status: Phase 21 contract for one external Agent Orchestrator.

This document describes the existing Red King REST boundary. It does not add
endpoints, authentication, an agent framework, or a new persistence layer.

## Connection

- Base URL: the deployed Red King backend URL. The Core frontend uses
  `VITE_API_BASE_URL`; a caller may use the same base URL.
- Content type for JSON requests: `application/json`.
- Authentication: none is defined by the current API contract. Network access
  must therefore be controlled outside this API.
- Error shape: normal route errors use `{ "detail": "..." }`. Malformed JSON or
  invalid request data may return FastAPI validation errors with HTTP `422`.
  Unknown routes return the framework's normal `404` response.

## Endpoint Contract

### `GET /api/status`

- Purpose: liveness and operational status check.
- Request: no body or query parameters.
- Response `200`:

  ```json
  {
    "system": "ONLINE",
    "hive_mind": "CONNECTED",
    "uplink": "SECURE (VPN)",
    "stealth": "ACTIVE",
    "active_nodes": 52,
    "threat_level": "DEFCON 4",
    "security_mode": "HARDENED"
  }
  ```

- Errors: rate limiting may reject requests; otherwise no application error is
  defined for a successful status check.
- Operation: read-only.
- External orchestrator: **suitable** as the first liveness check and before
  any mutating call.

### `GET /api/dashboard`

- Purpose: retrieve the current dashboard summary.
- Request: no body or query parameters.
- Response `200`:

  ```json
  {
    "system": "ONLINE",
    "status": "OK",
    "active_nodes": 52,
    "investigations": 3,
    "alerts": 0
  }
  ```

- Errors: server errors use the normal error shape.
- Operation: read-only.
- External orchestrator: **suitable** for coarse operational context. Values
  are a snapshot and must not be treated as durable workflow state.

### `GET /api/investigations`

- Purpose: list investigations available to Red King.
- Request: optional query parameters `status` and `q` (case-insensitive title
  search).
- Response `200`:

  ```json
  {
    "investigations": [
      {
        "id": "inv-1",
        "title": "Suspicious login pattern",
        "status": "open",
        "updatedAt": "2024-01-01T00:00:00Z"
      }
    ]
  }
  ```

- Errors: server errors use the normal error shape.
- Operation: read-only.
- External orchestrator: **suitable** for discovery and polling, with
  filtering performed through the existing query parameters.

### `POST /api/investigations`

- Purpose: create an investigation.
- Request body:

  ```json
  {
    "title": "Review suspicious login",
    "status": "open"
  }
  ```

  `title` is required and trimmed. `status` is optional and defaults to
  `open`; the backend currently accepts the supplied status value without an
  enum restriction.
- Response `200`:

  ```json
  {
    "investigation": {
      "id": "generated-uuid",
      "title": "Review suspicious login",
      "status": "open",
      "updatedAt": "2026-08-24T08:20:28.370506"
    }
  }
  ```

- Errors: `400` with `{ "detail": "Title is required" }` when the title is
  empty; malformed request data may return `422`.
- Operation: mutating. It persists the investigation and an initial timeline
  event.
- External orchestrator: **suitable with explicit policy approval**. Use the
  returned `id` as the resource identifier and do not retry blindly after an
  unknown network outcome, because creation is not idempotent.

### `PUT /api/investigations/{investigation_id}`

- Purpose: update an existing investigation's title and/or status.
- Request body: a JSON object containing optional `title` and `status` fields.

  ```json
  {
    "status": "in-progress"
  }
  ```

- Response `200`:

  ```json
  {
    "investigation": {
      "id": "inv-1",
      "title": "Suspicious login pattern",
      "status": "in-progress",
      "updatedAt": "2026-08-24T08:20:28.390076"
    }
  }
  ```

- Errors: `404` with `{ "detail": "Investigation not found" }`; malformed
  request data may return `422`.
- Operation: mutating. A supplied `status` also appends a timeline event.
- External orchestrator: **suitable with explicit policy approval**. Keep
  updates narrow and do not assume a status enum that the backend does not
  currently enforce.

### `GET /api/investigations/{investigation_id}/timeline`

- Purpose: retrieve timeline events for one investigation.
- Request: no body or query parameters.
- Response `200`:

  ```json
  {
    "timeline": [
      {
        "id": "event-id",
        "investigationId": "inv-1",
        "label": "Investigation opened",
        "time": "2024-01-01T00:00:00Z"
      }
    ]
  }
  ```

- Errors: an unknown investigation currently returns `200` with an empty
  `timeline` array; server errors use the normal error shape.
- Operation: read-only.
- External orchestrator: **suitable** for audit/context reads. Treat an empty
  result as either no events or an unknown id because the current API does not
  distinguish them.

### `GET /api/investigations/{investigation_id}/evidence`

- Purpose: retrieve evidence metadata associated with one investigation.
- Request: no body or query parameters.
- Response `200`:

  ```json
  {
    "evidence": [
      {
        "id": "e1",
        "investigationId": "inv-1",
        "name": "login_screenshot.png",
        "kind": "image"
      }
    ]
  }
  ```

- Errors: an unknown investigation currently returns `200` with an empty
  `evidence` array; server errors use the normal error shape.
- Operation: read-only.
- External orchestrator: **suitable** for context reads. This route returns
  metadata only and does not upload or download evidence.

### `DELETE /api/investigations/{investigation_id}`

- Purpose: delete an investigation and its related timeline and evidence
  metadata.
- Request: no body or query parameters.
- Response `200`:

  ```json
  {
    "deleted": true,
    "id": "inv-1"
  }
  ```

- Errors: `404` with `{ "detail": "Investigation not found" }`.
- Operation: mutating and destructive.
- External orchestrator: **not suitable for unattended use**. Permit only in
  an explicitly approved operator workflow.

### `GET /api/storage/{key}`

- Purpose: read a value from the existing JSON-backed frontend storage.
- Request: no body or query parameters. `{key}` is the storage key path
  segment.
- Response `200`:

  ```json
  {
    "value": { "example": true }
  }
  ```

- Errors: `404` with `{ "detail": "Storage key not found" }`.
- Operation: read-only.
- External orchestrator: **conditionally suitable** only for an allowlisted
  key agreed by the deployment owner. Do not enumerate or infer keys.

### `POST /api/storage/{key}`

- Purpose: write a value to the existing JSON-backed frontend storage.
- Request body: preferably `{ "value": <JSON value> }`. For compatibility,
  any JSON payload is also accepted and stored as the value.
- Response `200`:

  ```json
  {
    "value": { "example": true }
  }
  ```

- Errors: malformed request data may return `422`; server errors use the normal
  error shape.
- Operation: mutating.
- External orchestrator: **not suitable for unattended use** unless the key
  and value schema are explicitly allowlisted. This is a generic persistence
  escape hatch, not an orchestration queue.

## Recommended Initial Usage

An external orchestrator should begin with `GET /api/status`, optionally read
`GET /api/dashboard`, then use investigation list/read operations for context.
Investigation creation and updates require an explicit workflow policy. Delete
and generic storage writes should remain operator-controlled. No endpoint in
this contract represents an asynchronous job queue or a command-execution
interface.
