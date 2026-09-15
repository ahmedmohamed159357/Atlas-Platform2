# AI Agent Execution Protocol

## Required Execution State

Every task must be reported using this structure:

- TARGET: exact file, subsystem, endpoint, or command scope
- ACTION: exact inspection, modification, or check performed
- RESULT: observed behavior or output
- EVIDENCE: test output, command output, HTTP status, or other hard proof
- FILES MODIFIED: files changed and the reason for each change
- STATUS: SUCCESS, FAILED, BLOCKED, UNVERIFIED, or PARTIAL
- NEXT STEP: the next authorized action or WAIT FOR CONTROLLER

## Scope and Verification

- Inspect the controlling code path and verify preconditions before modifying code.
- Make only the requested change and technically necessary supporting changes.
- Do not make unrequested architecture changes, refactors, dependency upgrades, or UI changes.
- Treat unrelated findings as notes; do not fix them without explicit authorization.
- Validate changes with the narrowest relevant executable test before reporting success.

## Backend Target

- The operational backend is `app.main:app` in the primary backend directory.
- The required backend port is `9001`.
- Always verify `GET /api/status` and `GET /api/system/health` after starting or changing the backend.
- Do not start a second backend when a healthy target process already owns port `9001`.

## Dependency Isolation

- Use the backend `.venv` interpreter and installer.
- Use `requirements.linux.txt` for backend dependencies.
- Do not install packages globally or alter dependency manifests without explicit authorization.

## Safe Git Practices

- Never stage or commit broken, unrelated, generated, or unverified files.
- Never stage or commit `.venv` contents.
- Review `git diff --cached` and run `git diff --cached --check` before committing.
- Preserve unrelated user changes and keep commits narrowly scoped to the authorized task.
- Push only the reviewed commit to the configured remote.
