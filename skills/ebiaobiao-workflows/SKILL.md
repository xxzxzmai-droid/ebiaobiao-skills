---
name: ebiaobiao-workflows
description: "Design and implement 报表 automation workflow architectures around vika datasheets. Use when Codex needs embedded app patterns, backend/API gateway design, scheduled jobs, approval/reporting pipelines, secure token isolation, internal/external network reachability, webhook-like synchronization, batch report generation, or multi-system integrations backed by 报表 Fusion API."
---

# 报表自动化工作流

Use this when the work is bigger than a single API script or widget: embedded pages, backend services, scheduled jobs, cross-system sync, or secure external access.

## Default Architecture

Use this shape unless the user gives a better project-specific architecture:

```text
内嵌页面 / 管理后台
  -> 业务后端或 API 网关
  -> 报表 Fusion API
  -> 维格表 / 仪表盘 / 表单 / 附件
```

The frontend never receives a privileged 报表 API token. The backend maps user identity and business permissions to controlled Fusion API operations.

## Workflow

1. Identify actors: business user, admin, scheduled job, external system, 报表 token owner.
2. Identify network boundary: intranet-only, external phone access, VPN, gateway, or enterprise SSO.
3. Model data as 报表 tables first: source, reference, report, audit log, config.
4. Choose execution:
   - direct Fusion API script for internal batch jobs
   - backend service for embedded/mobile/front-end usage
   - widget for in-报表 interactive UI
   - script mini-program for one-off table operations
5. Define audit fields: batch ID, operator, source count, success count, failure count, status, attachment/result links.
6. Verify with read-only API calls, then development-space writes.

## Guardrails

- Do not solve internal/external reachability in the widget frontend. Use a gateway, VPN, or backend ingress.
- Do not place API tokens in embedded pages, browser storage, bundled JS, or shared configuration.
- For colleague-facing tools, hide technical knobs; expose click-only operations and clear status.
- For scheduled jobs, log run IDs and make operations idempotent around business keys.
- For high-risk writes, use dry-run preview, audit records, and post-write sampling.

## References

- `references/workflow-architecture.md`: reusable architecture and acceptance checklist.
