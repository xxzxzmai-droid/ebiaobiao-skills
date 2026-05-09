# Workflow Architecture

## Common Table Model

- `source_*`: raw business records or imported rows.
- `reference_*`: mapping tables, departments, projects, users, thresholds.
- `report_*`: generated report rows and final output state.
- `audit_log`: run ID, operator, timestamp, source count, success count, failed count, error digest.
- `config`: field IDs, view IDs, feature switches, output options.

## Backend Responsibilities

- Store API token server-side only.
- Validate caller identity from eLink, enterprise WeChat, SSO, or trusted intranet auth.
- Map business permissions before reading/writing e报表.
- Chunk writes according to Fusion API limits.
- Retry 429 and transient failures with backoff.
- Write audit logs and return business-readable results.

## Embedded Frontend Responsibilities

- Render task-specific UI and progress.
- Call backend APIs, not Fusion API directly.
- Adapt layout for phone, desktop, and enterprise WeChat embedded windows.
- Show loading, empty, validation, permission, partial-failure, and success states.

## Network Guidance

- A local laptop service is for preview/debug only.
- An intranet server is not reachable from external phones by default.
- External access requires VPN, reverse proxy, public gateway, or approved enterprise ingress.
- Keep a single controlled ingress when internal and external users both need the workflow.

## Acceptance Checklist

- Token is never present in frontend code or logs.
- Read-only smoke succeeds before writes.
- Development-space write smoke succeeds before production-like rollout.
- Audit table records each run.
- Re-running the same batch is either blocked or idempotent.
- UI is usable in narrow embedded windows.
