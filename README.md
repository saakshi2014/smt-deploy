# Sales & Marketing Performance Tracking System

**Masters Level Project — Academic Year 2025–26**
Mahatma Gandhi Memorial College, Udupi
Submitted by: Saakshi | Reg No: P05MG24S038019

---

## Project Overview

A full-stack web-based performance tracking system for sales and
marketing teams. The system supports three hierarchical user roles —
Employee, M1 Manager (Team Manager), and M2 Manager (Senior Manager)
— each with distinct access levels, dashboards, and capabilities.

Built as a two-month MVP project using an agile sprint methodology,
delivering four functional versions across 25 development days.

---

## Sprint History

| Sprint | Days | Version | Focus |
|--------|------|---------|-------|
| Sprint 1 | Day 1–10 | V1.0 | Auth, Pipeline Tracking, 3 Dashboards |
| Sprint 2 | Day 11–15 | V2.0 | Task Management, KPI Engine, Notifications |
| Sprint 3 | Day 16–21 | V3.0 | Charts, Coaching, Reviews, Security, CSV Export |
| Sprint 4 | Day 22–25 | V4.0 | Docker, Pagination, Bulk Import, Final QA |

---

## Complete Feature List

### Authentication & Access Control
- Firebase Email/Password Authentication
- JWT token verification on every API route
- Role-based routing (Employee / M1 Manager / M2 Manager)
- Route protection — all dashboards require login
- Session management with auto-expiry ping
- Secure logout with cookie clearing

### Employee Dashboard
- Personal lead pipeline — Add, Edit, Archive leads
- 13 default pipeline stages with colour-coded badges
- Stage change with audit trail
- Lead detail panel with quick actions
- Search and filter by stage, name, company, email
- Show/hide archived leads toggle
- My Tasks tab — view, update status, priority badges
- My KPIs tab — 9 KPI progress bars vs targets
- Custom KPI value input
- CSV export of own leads
- Bulk lead import via CSV upload
- Pagination — 50 leads per page

### M1 Manager Dashboard
- Team Pipeline — all leads with employee column
- 6-card stats bar (Total, Active, Interested, Scheduled, Completed, Archived)
- Stage Distribution panel with progress bars
- Filter by stage, employee, search
- Task Management — create/assign tasks with priority and due date
- Team KPIs — side-by-side comparison table
- Bar chart — actual vs target per KPI
- Pipeline funnel chart for team
- Pipeline Stages — create/rename/deactivate custom stages
- Coaching Sessions — log, edit, track follow-ups
- CSV export for leads, tasks, KPI, coaching

### M2 Manager Dashboard
- Organisation Overview with 6 top-line KPI cards
- Team Cards with conversion rate indicators
- Drill-down navigation — Org → Team → Leads
- Date range filter (This Month / This Week / Custom)
- Lead Measures bar chart — org total
- Lag Measures bar chart — org total
- Organisation Pipeline Funnel chart
- Task Health Panel — org-wide task counts by status
- Team task breakdown with completion progress bars
- Manager Reviews — schedule, track, add notes and action items
- CSV export for leads and KPI data

### KPI Engine (9 Default KPIs)
Lead Measures:
1. Outreach Count
2. Connection Rate %
3. Initial Message Count
4. Reply Rate %
5. Meeting Conversion Rate %

Lag Measures:
6. Meetings Scheduled
7. Meetings Completed
8. Interested Leads
9. Warm Leads Nurtured

### Additional Features
- In-app notification bell with unread badge
- Notification dropdown with mark-as-read
- Auto-notify on task assignment, completion, overdue
- Overdue task auto-flagging
- Firestore Security Rules — role-based access control
- Stages caching — 5-minute in-memory cache
- Bulk lead import via CSV with error reporting
- Download CSV import template
- Full 33-test regression suite

---

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | HTML5, CSS3, JavaScript ES6+ | — |
| CSS Framework | Bootstrap 5 | 5.3.0 |
| Icons | Bootstrap Icons | 1.11.0 |
| Charts | Chart.js | 4.4.0 |
| Backend | Python Flask | 3.0.0 |
| Database | Firebase Firestore | 2.14.0 |
| Authentication | Firebase Auth | 6.4.0 |
| Deployment | Docker + Docker Compose | — |
| Version Control | Git + GitHub | — |

---

## Project Structure
sales-marketing-tracker/
├── backend/
│   ├── app.py                    Flask application factory
│   ├── firebase_config.py        Firebase Admin SDK init
│   ├── requirements.txt          Python dependencies
│   ├── routes/
│   │   ├── auth.py               Authentication routes
│   │   ├── leads.py              Lead CRUD + org routes
│   │   ├── stages.py             Pipeline stages API
│   │   ├── tasks.py              Task management API
│   │   ├── notifications.py      Notification API
│   │   ├── custom_stages.py      Custom stage management
│   │   ├── kpi.py                KPI calculation engine
│   │   ├── coaching.py           Coaching session tracker
│   │   ├── reviews.py            Manager review tracker
│   │   └── export.py             CSV export routes
│   ├── tests/
│   │   └── test_all.py           33-test regression suite
│   ├── seed_users.py
│   ├── seed_stages.py
│   ├── seed_teams.py
│   ├── seed_all.py
│   └── seed_demo_data.py
├── frontend/
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── employee_dashboard.html
│   │   ├── m1_dashboard.html
│   │   └── m2_dashboard.html
│   └── static/
│       ├── css/main.css
│       └── js/
│           ├── main.js
│           ├── leads.js
│           ├── tasks.js
│           ├── charts.js
│           ├── kpi_dashboard.js
│           ├── m1_dashboard.js
│           ├── m2_dashboard.js
│           ├── coaching.js
│           ├── reviews.js
│           └── custom_stages.js
├── docker/
│   └── Dockerfile
├── docs/
│   └── SCHEMA.md
├── docker-compose.yml
├── .dockerignore
├── .env.example
└── README.md

---

## Firestore Collections

| Collection | Purpose |
|-----------|---------|
| users | User profiles with roles |
| teams | Teams with members subcollection |
| leads | Lead pipeline data |
| pipeline_stages | Default and custom stages |
| audit_logs | Stage change history |
| tasks | Task assignments |
| notifications | In-app notifications |
| kpi_targets | KPI target values |
| kpi_custom_columns | Custom KPI definitions |
| kpi_custom_entries | Employee KPI values |
| coaching_sessions | Coaching records |
| manager_reviews | Review meeting records |

---

## Local Setup

### Prerequisites
- Python 3.10+
- Git
- Firebase project with Firestore and Auth enabled

### Installation

```bash

✅ DAY 24 & 25 — Complete Step-by-Step Guide
Academic Documentation & Final Project Submission

🟡 Before You Start — 2 Checks
Check 1 — Activate venv and confirm develop branch
venv\Scripts\activate
git branch
Check 2 — Confirm Flask still works
cd backend
python app.py
Confirm Firebase Admin SDK initialised successfully. Press Ctrl + C then cd ...

═══════════════════════════════════════
DAY 24 — Academic Documentation
═══════════════════════════════════════
🔵 PHASE 1 — Update README.md
Step 1 — Open and rewrite README.md
Open README.md in VS Code. Press Ctrl + A → Delete. Paste in:
markdown# Sales & Marketing Performance Tracking System

**Masters Level Project — Academic Year 2025–26**
Mahatma Gandhi Memorial College, Udupi
Submitted by: Saakshi | Reg No: P05MG24S038019

---

## Project Overview

A full-stack web-based performance tracking system for sales and
marketing teams. The system supports three hierarchical user roles —
Employee, M1 Manager (Team Manager), and M2 Manager (Senior Manager)
— each with distinct access levels, dashboards, and capabilities.

Built as a two-month MVP project using an agile sprint methodology,
delivering four functional versions across 25 development days.

---

## Sprint History

| Sprint | Days | Version | Focus |
|--------|------|---------|-------|
| Sprint 1 | Day 1–10 | V1.0 | Auth, Pipeline Tracking, 3 Dashboards |
| Sprint 2 | Day 11–15 | V2.0 | Task Management, KPI Engine, Notifications |
| Sprint 3 | Day 16–21 | V3.0 | Charts, Coaching, Reviews, Security, CSV Export |
| Sprint 4 | Day 22–25 | V4.0 | Docker, Pagination, Bulk Import, Final QA |

---

## Complete Feature List

### Authentication & Access Control
- Firebase Email/Password Authentication
- JWT token verification on every API route
- Role-based routing (Employee / M1 Manager / M2 Manager)
- Route protection — all dashboards require login
- Session management with auto-expiry ping
- Secure logout with cookie clearing

### Employee Dashboard
- Personal lead pipeline — Add, Edit, Archive leads
- 13 default pipeline stages with colour-coded badges
- Stage change with audit trail
- Lead detail panel with quick actions
- Search and filter by stage, name, company, email
- Show/hide archived leads toggle
- My Tasks tab — view, update status, priority badges
- My KPIs tab — 9 KPI progress bars vs targets
- Custom KPI value input
- CSV export of own leads
- Bulk lead import via CSV upload
- Pagination — 50 leads per page

### M1 Manager Dashboard
- Team Pipeline — all leads with employee column
- 6-card stats bar (Total, Active, Interested, Scheduled, Completed, Archived)
- Stage Distribution panel with progress bars
- Filter by stage, employee, search
- Task Management — create/assign tasks with priority and due date
- Team KPIs — side-by-side comparison table
- Bar chart — actual vs target per KPI
- Pipeline funnel chart for team
- Pipeline Stages — create/rename/deactivate custom stages
- Coaching Sessions — log, edit, track follow-ups
- CSV export for leads, tasks, KPI, coaching

### M2 Manager Dashboard
- Organisation Overview with 6 top-line KPI cards
- Team Cards with conversion rate indicators
- Drill-down navigation — Org → Team → Leads
- Date range filter (This Month / This Week / Custom)
- Lead Measures bar chart — org total
- Lag Measures bar chart — org total
- Organisation Pipeline Funnel chart
- Task Health Panel — org-wide task counts by status
- Team task breakdown with completion progress bars
- Manager Reviews — schedule, track, add notes and action items
- CSV export for leads and KPI data

### KPI Engine (9 Default KPIs)
Lead Measures:
1. Outreach Count
2. Connection Rate %
3. Initial Message Count
4. Reply Rate %
5. Meeting Conversion Rate %

Lag Measures:
6. Meetings Scheduled
7. Meetings Completed
8. Interested Leads
9. Warm Leads Nurtured

### Additional Features
- In-app notification bell with unread badge
- Notification dropdown with mark-as-read
- Auto-notify on task assignment, completion, overdue
- Overdue task auto-flagging
- Firestore Security Rules — role-based access control
- Stages caching — 5-minute in-memory cache
- Bulk lead import via CSV with error reporting
- Download CSV import template
- Full 33-test regression suite

---

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | HTML5, CSS3, JavaScript ES6+ | — |
| CSS Framework | Bootstrap 5 | 5.3.0 |
| Icons | Bootstrap Icons | 1.11.0 |
| Charts | Chart.js | 4.4.0 |
| Backend | Python Flask | 3.0.0 |
| Database | Firebase Firestore | 2.14.0 |
| Authentication | Firebase Auth | 6.4.0 |
| Deployment | Docker + Docker Compose | — |
| Version Control | Git + GitHub | — |

---

## Project Structure
sales-marketing-tracker/
├── backend/
│   ├── app.py                    Flask application factory
│   ├── firebase_config.py        Firebase Admin SDK init
│   ├── requirements.txt          Python dependencies
│   ├── routes/
│   │   ├── auth.py               Authentication routes
│   │   ├── leads.py              Lead CRUD + org routes
│   │   ├── stages.py             Pipeline stages API
│   │   ├── tasks.py              Task management API
│   │   ├── notifications.py      Notification API
│   │   ├── custom_stages.py      Custom stage management
│   │   ├── kpi.py                KPI calculation engine
│   │   ├── coaching.py           Coaching session tracker
│   │   ├── reviews.py            Manager review tracker
│   │   └── export.py             CSV export routes
│   ├── tests/
│   │   └── test_all.py           33-test regression suite
│   ├── seed_users.py
│   ├── seed_stages.py
│   ├── seed_teams.py
│   ├── seed_all.py
│   └── seed_demo_data.py
├── frontend/
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── employee_dashboard.html
│   │   ├── m1_dashboard.html
│   │   └── m2_dashboard.html
│   └── static/
│       ├── css/main.css
│       └── js/
│           ├── main.js
│           ├── leads.js
│           ├── tasks.js
│           ├── charts.js
│           ├── kpi_dashboard.js
│           ├── m1_dashboard.js
│           ├── m2_dashboard.js
│           ├── coaching.js
│           ├── reviews.js
│           └── custom_stages.js
├── docker/
│   └── Dockerfile
├── docs/
│   └── SCHEMA.md
├── docker-compose.yml
├── .dockerignore
├── .env.example
└── README.md

---

## Firestore Collections

| Collection | Purpose |
|-----------|---------|
| users | User profiles with roles |
| teams | Teams with members subcollection |
| leads | Lead pipeline data |
| pipeline_stages | Default and custom stages |
| audit_logs | Stage change history |
| tasks | Task assignments |
| notifications | In-app notifications |
| kpi_targets | KPI target values |
| kpi_custom_columns | Custom KPI definitions |
| kpi_custom_entries | Employee KPI values |
| coaching_sessions | Coaching records |
| manager_reviews | Review meeting records |

---

## Local Setup

### Prerequisites
- Python 3.10+
- Git
- Firebase project with Firestore and Auth enabled

### Installation

```bash
# 1. Clone repository
git clone https://github.com/saakshi2014/sales-marketing-tracker.git
cd sales-marketing-tracker

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate        # Mac/Linux

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Set up environment
copy .env.example .env          # Windows
cp .env.example .env            # Mac/Linux
# Fill in your Firebase credentials in .env

# 5. Add firebase-service-account.json to project root

# 6. Seed initial data (first time only)
python backend/seed_all.py
python backend/seed_demo_data.py

# 7. Run the application
cd backend
python app.py
```

Open: `http://127.0.0.1:5000`

---

## Docker Setup

```bash
docker compose up --build
```

Open: `http://localhost:5000`

---

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Employee | employee@test.com | Test@1234 |
| M1 Manager | m1manager@test.com | Test@1234 |
| M2 Manager | m2manager@test.com | Test@1234 |

---

## Running Tests

```bash
python backend/tests/test_all.py
```

Expected: 33/33 PASS

---

## V1–V4 Acceptance Criteria

### V1 (Sprint 1) — All Passed ✅
1. All 3 roles log in and land on correct dashboard
2. Employee moves lead through all 13 pipeline stages
3. Every stage change creates an audit log entry
4. M1 sees team leads only — no cross-team data
5. M2 sees org-wide summary across all teams
6. Route protection — no dashboard access without login

### V2 (Sprint 2) — All Passed ✅
1. M1/M2 can create and assign tasks with priority and due date
2. Employee sees assigned tasks and updates status
3. Tasks past due date auto-flagged as Overdue
4. M2 sees consolidated task health across all teams
5. Employee notified on task assignment
6. M1 notified on task completion/overdue
7. M1/M2 can create/rename/deactivate custom stages
8. All 9 KPIs calculate correctly from pipeline data
9. KPI targets settable per employee
10. Employee KPI dashboard shows progress vs target

### V3 (Sprint 3) — All Passed ✅
1. Bar charts render on M1 and M2 dashboards
2. Funnel chart shows pipeline conversion
3. M2 date range filter updates all charts
4. M1 can log and track coaching sessions
5. M2 can schedule and track manager reviews
6. Firestore security rules enforce role isolation
7. CSV export works for all 4 data types
8. 33/33 regression tests pass

### V4 (Sprint 4) — All Passed ✅
1. Docker Compose builds and runs correctly
2. Pagination works for large lead datasets
3. Bulk CSV import creates leads in Firestore
4. Import error handling works correctly
5. Stages API uses caching
6. All previous acceptance criteria still pass

---

## Security

- Firebase Authentication handles all identity
- JWT tokens verified server-side on every request
- Firestore Security Rules enforce collection-level access
- Secret keys stored in .env (gitignored)
- Service account JSON gitignored
- Role-based access control on all 35+ API routes

---

## Known Limitations

- Docker TLS issue on restricted networks (use home WiFi)
- Firestore test mode rules expire after 30 days
  (production rules implemented in Sprint 3)
- KPI trend chart uses estimated weekly buckets

---

## Academic Information

- Student: Saakshi
- Registration: P05MG24S038019
- Institution: Mahatma Gandhi Memorial College, Udupi
- Program: Masters
- Project Duration: 25 development days (5 weeks)
- Development Methodology: Agile Scrum (4 sprints)