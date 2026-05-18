# API Reference
## Sales & Marketing Performance Tracking System

Base URL: `http://127.0.0.1:5000`

All routes require an active session (login first).

---

## Authentication Routes

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | /api/auth/verify | All | Verify Firebase JWT token |
| GET | /api/auth/me | All | Get current user info |
| GET | /logout | All | Clear session and logout |

---

## Lead Routes

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | /api/leads | All | Create a new lead |
| GET | /api/leads | All | Get leads (role-filtered, paginated) |
| GET | /api/leads/{id} | All | Get single lead details |
| PATCH | /api/leads/{id} | All | Update lead details |
| DELETE | /api/leads/{id} | M1/M2 | Delete a lead |
| PATCH | /api/leads/{id}/stage | All | Change pipeline stage |
| PATCH | /api/leads/{id}/archive | All | Archive/unarchive a lead |
| GET | /api/leads/{id}/history | All | Get audit trail for a lead |
| POST | /api/leads/bulk-import | All | Import leads from CSV |
| GET | /api/leads/import-template | All | Download import template |

---

## Pipeline Stages Routes

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | /api/stages | All | Get active stages (cached) |
| GET | /api/custom-stages | M1/M2 | Get all stages including inactive |
| POST | /api/custom-stages | M1/M2 | Create a custom stage |
| PATCH | /api/custom-stages/{id} | M1/M2 | Rename a custom stage |
| PATCH | /api/custom-stages/{id}/toggle | M1/M2 | Activate/deactivate stage |

---

## Task Routes

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | /api/tasks | M1/M2 | Create and assign a task |
| GET | /api/tasks | All | Get tasks (role-filtered) |
| GET | /api/tasks/{id} | All | Get single task |
| PATCH | /api/tasks/{id} | All | Update task status or details |
| DELETE | /api/tasks/{id} | M1/M2 | Soft delete a task |
| GET | /api/tasks/assignees | M1/M2 | Get assignable employees |
| GET | /api/tasks/stats | M2 | Task health stats by team |

---

## Notification Routes

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | /api/notifications | All | Get user notifications |
| PUT | /api/notifications/{id}/read | All | Mark single as read |
| PUT | /api/notifications/read-all | All | Mark all as read |

---

## KPI Routes

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | /api/kpi/me | Employee | Get own KPIs |
| GET | /api/kpi/employee/{uid} | All | Get specific employee KPIs |
| GET | /api/kpi/team | M1/M2 | Get team KPI comparison |
| POST | /api/kpi/targets | M1/M2 | Set KPI targets |
| GET | /api/kpi/trend/{uid} | All | Get KPI trend over time |
| GET | /api/kpi/org-summary | M2 | Org-wide KPI aggregation |
| GET | /api/kpi/custom-columns | All | Get custom KPI columns |
| POST | /api/kpi/custom-columns | M1/M2 | Create custom KPI column |
| POST | /api/kpi/custom-columns/{id}/entry | Employee | Submit KPI value |

---

## Coaching Routes

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | /api/coaching | M1/M2 | Log a coaching session |
| GET | /api/coaching | All | Get coaching sessions |
| PATCH | /api/coaching/{id} | M1/M2 | Update session |
| DELETE | /api/coaching/{id} | M1/M2 | Delete session |
| GET | /api/coaching/stats | M1/M2 | Coaching statistics |

---

## Manager Review Routes

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | /api/reviews | M2 | Schedule a review |
| GET | /api/reviews | M1/M2 | Get reviews |
| PATCH | /api/reviews/{id} | M1/M2 | Update review |
| DELETE | /api/reviews/{id} | M2 | Delete review |
| GET | /api/reviews/m1-managers | M2 | Get M1 managers list |

---

## Organisation Routes

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | /api/org/summary | M2 | Org-wide lead summary |
| GET | /api/org/teams | M2 | Get all teams |
| GET | /api/org/teams/{id}/leads | M2 | Get all leads for a team |
| GET | /api/team/members | M1/M2 | Get team members |

---

## Export Routes

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | /api/export/leads | All | Download leads as CSV |
| GET | /api/export/tasks | M1/M2 | Download tasks as CSV |
| GET | /api/export/kpi | M1/M2 | Download KPI data as CSV |
| GET | /api/export/coaching | M1/M2 | Download coaching as CSV |

---

## Total: 45 API Routes across 10 modules