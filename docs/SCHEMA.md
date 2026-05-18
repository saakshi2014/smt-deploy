# Firestore Database Schema
## Sales & Marketing Performance Tracking System
### Last Updated: Day 24 — Final Version

---

## Overview

All data is stored in Firebase Firestore (NoSQL document database).
Collections are flat — no deep nesting beyond one subcollection level.
All document IDs are either UUIDs or semantic IDs (e.g. team_001).

---

## users/{userId}

Document ID = Firebase Auth UID

| Field | Type | Description |
|-------|------|-------------|
| uid | string | Firebase Auth UID |
| email | string | user@example.com |
| displayName | string | Full display name |
| role | string | employee / m1_manager / m2_manager |
| teamId | string | ID of assigned team |
| isActive | boolean | false = deactivated account |
| createdAt | timestamp | Account creation time |

---

## teams/{teamId}

Document ID = teamId (e.g. team_001)

| Field | Type | Description |
|-------|------|-------------|
| teamId | string | e.g. team_001 |
| teamName | string | e.g. Sales Team Alpha |
| m1ManagerUid | string | UID of the M1 Manager |
| m2ManagerUid | string | UID of the M2 Manager |
| isActive | boolean | Team active status |
| createdAt | timestamp | Creation time |
| createdBy | string | UID of creator |

### Subcollection: teams/{teamId}/members/{uid}

| Field | Type | Description |
|-------|------|-------------|
| uid | string | Member UID |
| email | string | Member email |
| role | string | employee / m1_manager |
| joinedAt | timestamp | When added to team |

---

## pipeline_stages/{stageId}

Document ID = stageId (e.g. stage_1_1 or custom_abc123)

| Field | Type | Description |
|-------|------|-------------|
| stageId | string | e.g. stage_1_1 |
| stageNumber | string | e.g. 1.1 |
| stageName | string | e.g. Qualified – Pending Outreach |
| description | string | Stage description |
| stageOrder | number | Sort order (supports decimals) |
| isDefault | boolean | true = built-in stage |
| isActive | boolean | false = hidden from UI |
| isArchived | boolean | true = stage_6_2 only |
| createdBy | string | null for defaults |
| createdAt | timestamp | Creation time |

### Default 13 Stages

| stageId | stageNumber | stageName |
|---------|-------------|-----------|
| stage_1_1 | 1.1 | Qualified – Pending Outreach |
| stage_1_2 | 1.2 | Not Qualified |
| stage_2 | 2 | Connection Request Sent |
| stage_2_1 | 2.1 | Connected on LinkedIn |
| stage_2_2 | 2.2 | Connection Not Accepted |
| stage_3 | 3 | Initial Message Sent |
| stage_3_1 | 3.1 | No Response |
| stage_4 | 4 | Initial Reply Received |
| stage_6_1 | 6.1 | Interested – Ready for Meeting |
| stage_6_2 | 6.2 | Not Interested – Archived |
| stage_6_3 | 6.3 | Warm Lead – Needs Nurturing |
| stage_7 | 7 | Meeting Scheduled |
| stage_8 | 8 | Meeting Completed |

---

## leads/{leadId}

Document ID = auto-generated UUID

| Field | Type | Description |
|-------|------|-------------|
| leadId | string | Auto-generated UUID |
| employeeUid | string | Owner employee UID |
| teamId | string | Team this lead belongs to |
| name | string | Lead full name |
| company | string | Lead company |
| email | string | Lead email |
| phone | string | Lead phone number |
| linkedinUrl | string | LinkedIn profile URL |
| currentStage | string | stageId of current stage |
| isArchived | boolean | true when at stage_6_2 |
| createdAt | timestamp | Lead creation time |
| updatedAt | timestamp | Last update time |

---

## audit_logs/{logId}

Document ID = auto-generated UUID

| Field | Type | Description |
|-------|------|-------------|
| logId | string | Auto-generated UUID |
| leadId | string | Which lead was changed |
| employeeUid | string | Who made the change |
| fromStage | string | stageId before change (null if first) |
| toStage | string | stageId after change |
| changedAt | timestamp | When the change happened |
| notes | string | Optional note about the change |

---

## tasks/{taskId}

Document ID = auto-generated UUID

| Field | Type | Description |
|-------|------|-------------|
| taskId | string | Auto-generated UUID |
| title | string | Task title |
| description | string | Detailed instructions |
| assignedToUid | string | Employee who must complete this |
| assignedToName | string | Employee name (denormalised) |
| assignedByUid | string | M1/M2 who created this |
| assignedByRole | string | m1_manager / m2_manager |
| teamId | string | Team this task belongs to |
| dueDate | timestamp | Task deadline |
| priority | string | low / medium / high |
| status | string | pending / in_progress / completed / overdue |
| createdAt | timestamp | Creation time |
| completedAt | timestamp | null until completed |
| isDeleted | boolean | Soft delete flag |

---

## notifications/{notifId}

Document ID = auto-generated UUID

| Field | Type | Description |
|-------|------|-------------|
| notifId | string | Auto-generated UUID |
| recipientUid | string | Who receives this notification |
| message | string | Notification text |
| type | string | task_assigned / task_completed / task_overdue |
| relatedId | string | taskId this notification is about |
| isRead | boolean | false = unread |
| createdAt | timestamp | Creation time |

---

## kpi_targets/{targetId}

Document ID = auto-generated UUID

| Field | Type | Description |
|-------|------|-------------|
| targetId | string | Auto-generated UUID |
| employeeUid | string | Employee these targets apply to |
| setByUid | string | M1/M2 who set the targets |
| period | string | monthly / weekly |
| targets | map | { outreachCount: 50, connectionRate: 40.0, ... } |
| createdAt | timestamp | Creation time |
| updatedAt | timestamp | Last update time |

---

## kpi_custom_columns/{columnId}

Document ID = auto-generated UUID

| Field | Type | Description |
|-------|------|-------------|
| columnId | string | Auto-generated UUID |
| columnName | string | e.g. LinkedIn Posts |
| description | string | What this KPI measures |
| dataType | string | numeric / percentage / text |
| teamId | string | Team this column belongs to |
| isActive | boolean | false = hidden |
| hasData | boolean | true once entries exist |
| createdBy | string | M1/M2 who created this |
| createdAt | timestamp | Creation time |

---

## kpi_custom_entries/{entryId}

Document ID = auto-generated UUID

| Field | Type | Description |
|-------|------|-------------|
| entryId | string | Auto-generated UUID |
| columnId | string | Which custom KPI column |
| employeeUid | string | Who submitted this |
| value | any | The KPI value |
| entryDate | string | YYYY-MM-DD |
| createdAt | timestamp | Submission time |

---

## coaching_sessions/{sessionId}

Document ID = auto-generated UUID

| Field | Type | Description |
|-------|------|-------------|
| sessionId | string | Auto-generated UUID |
| specialistUid | string | Employee being coached |
| specialistName | string | Employee name (denormalised) |
| coachUid | string | M1 who ran the session |
| coachName | string | M1 name (denormalised) |
| teamId | string | Team |
| sessionDate | timestamp | When session took place |
| topic | string | Session topic |
| notes | string | Session notes |
| followUpDate | timestamp | null if no follow-up set |
| isCompleted | boolean | false until marked complete |
| createdAt | timestamp | Record creation time |

---

## manager_reviews/{reviewId}

Document ID = auto-generated UUID

| Field | Type | Description |
|-------|------|-------------|
| reviewId | string | Auto-generated UUID |
| m1ManagerUid | string | M1 being reviewed |
| m1ManagerName | string | M1 name (denormalised) |
| m2ManagerUid | string | M2 scheduling the review |
| m2ManagerName | string | M2 name (denormalised) |
| scheduledDate | timestamp | When meeting is scheduled |
| agenda | string | Topics to discuss |
| notes | string | Meeting notes (filled post-meeting) |
| actionItems | array | List of action item strings |
| isCompleted | boolean | false until marked complete |
| completedAt | timestamp | null until completed |
| createdAt | timestamp | Creation time |

---

## Audit Trail Coverage

| Event | Logged | Location |
|-------|--------|----------|
| Lead stage change | ✅ Yes | audit_logs collection |
| Lead created | ✅ Yes | audit_logs (fromStage: null) |
| Lead archived | ✅ Yes | audit_logs (notes: "Lead archived") |
| Lead imported via CSV | ✅ Yes | audit_logs (notes: "Imported from CSV") |
| Task status change | ✅ Yes | Notifications collection |
| Coaching session logged | ✅ Yes | coaching_sessions collection |
| Team membership change | ⚠️ Seeded only | No runtime team change UI in V4 |