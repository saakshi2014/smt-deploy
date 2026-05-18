"""
kpi.py — KPI Tracking API Routes
Handles: calculate KPIs, set targets, get KPI dashboard data,
         custom KPI columns
"""

from flask import Blueprint, request, jsonify, session
from firebase_config import get_firestore_client
from firebase_admin import firestore
from datetime import datetime, timezone, timedelta
import uuid

kpi_bp = Blueprint('kpi', __name__)


def require_auth():
    if 'uid' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    return None


# ── KPI CALCULATION ENGINE ─────────────────────────────────────────────────────

def calculate_lead_measures(db, employee_uid, start_date, end_date):
    """
    Calculates all 5 lead measures for a given employee
    within a date range using audit_logs and leads collections.

    Lead Measures:
    1. Outreach Count    — connection requests sent (stage_2 entries)
    2. Connection Rate   — % of requests accepted (stage_2_1 / stage_2)
    3. Message Count     — initial messages sent (stage_3 entries)
    4. Reply Rate        — % of messages that got reply (stage_4 / stage_3)
    5. Meeting Conv Rate — % of replies that became meetings (stage_7 / stage_4)
    """
    try:
        logs_ref = db.collection('audit_logs')\
                     .where('employeeUid', '==', employee_uid).get()

        # Count stage transitions within date range
        stage_counts = {}
        for log in logs_ref:
            entry     = log.to_dict()
            changed_at = entry.get('changedAt')

            # Filter by date range
            if changed_at and hasattr(changed_at, 'replace'):
                log_date = changed_at.replace(tzinfo=timezone.utc)
                if not (start_date <= log_date <= end_date):
                    continue

            to_stage = entry.get('toStage')
            if to_stage:
                stage_counts[to_stage] = stage_counts.get(to_stage, 0) + 1

        # Extract counts
        outreach_count  = stage_counts.get('stage_2', 0)
        connected       = stage_counts.get('stage_2_1', 0)
        message_count   = stage_counts.get('stage_3', 0)
        replies         = stage_counts.get('stage_4', 0)
        meetings        = stage_counts.get('stage_7', 0)

        # Calculate rates safely
        connection_rate  = round((connected / outreach_count * 100), 1) \
                           if outreach_count > 0 else 0.0
        reply_rate       = round((replies / message_count * 100), 1) \
                           if message_count > 0 else 0.0
        meeting_conv_rate = round((meetings / replies * 100), 1) \
                            if replies > 0 else 0.0

        return {
            "outreachCount":       outreach_count,
            "connectionRate":      connection_rate,
            "initialMessageCount": message_count,
            "replyRate":           reply_rate,
            "meetingConversionRate": meeting_conv_rate,
        }

    except Exception as e:
        print(f"Error calculating lead measures: {e}")
        return {
            "outreachCount": 0, "connectionRate": 0.0,
            "initialMessageCount": 0, "replyRate": 0.0,
            "meetingConversionRate": 0.0
        }


def calculate_lag_measures(db, employee_uid, start_date, end_date):
    """
    Calculates all 4 lag measures for a given employee.

    Lag Measures:
    1. Meetings Scheduled  — leads at stage_7
    2. Meetings Completed  — leads at stage_8
    3. Interested Leads    — leads at stage_6_1
    4. Warm Leads Nurtured — leads that moved from stage_6_3 to stage_6_1 or 7
    """
    try:
        leads_ref = db.collection('leads')\
                      .where('employeeUid', '==', employee_uid).get()

        meetings_scheduled = 0
        meetings_completed = 0
        interested_leads   = 0

        for lead_doc in leads_ref:
            lead = lead_doc.to_dict()
            stage = lead.get('currentStage', '')

            if stage == 'stage_7':
                meetings_scheduled += 1
            elif stage == 'stage_8':
                meetings_completed += 1
            elif stage == 'stage_6_1':
                interested_leads += 1

        # Warm leads nurtured: moved from 6_3 to 6_1 or 7 within date range
        logs_ref = db.collection('audit_logs')\
                     .where('employeeUid', '==', employee_uid)\
                     .where('fromStage', '==', 'stage_6_3').get()

        warm_leads_nurtured = 0
        for log in logs_ref:
            entry      = log.to_dict()
            changed_at = entry.get('changedAt')
            to_stage   = entry.get('toStage', '')

            if changed_at and hasattr(changed_at, 'replace'):
                log_date = changed_at.replace(tzinfo=timezone.utc)
                if not (start_date <= log_date <= end_date):
                    continue

            if to_stage in ['stage_6_1', 'stage_7']:
                warm_leads_nurtured += 1

        return {
            "meetingsScheduled": meetings_scheduled,
            "meetingsCompleted": meetings_completed,
            "interestedLeads":   interested_leads,
            "warmLeadsNurtured": warm_leads_nurtured,
        }

    except Exception as e:
        print(f"Error calculating lag measures: {e}")
        return {
            "meetingsScheduled": 0, "meetingsCompleted": 0,
            "interestedLeads": 0,   "warmLeadsNurtured": 0
        }


# ── ROUTE 1: Get KPIs for a specific employee ──────────────────────────────────
@kpi_bp.route('/api/kpi/employee/<employee_uid>', methods=['GET'])
def get_employee_kpis(employee_uid):
    """
    Returns all KPIs (lead + lag measures) for a specific employee.

    Optional query params:
    - ?period=monthly (default) | weekly | custom
    - ?startDate=2026-04-01
    - ?endDate=2026-04-30
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    uid  = session['uid']
    role = session['role']

    # Access control: employee can only see their own KPIs
    if role == 'employee' and uid != employee_uid:
        return jsonify({"error": "Access denied"}), 403

    try:
        # Determine date range
        period     = request.args.get('period', 'monthly')
        now        = datetime.now(timezone.utc)

        if period == 'weekly':
            start_date = now - timedelta(days=7)
            end_date   = now
        elif period == 'custom':
            start_str  = request.args.get('startDate', '')
            end_str    = request.args.get('endDate', '')
            try:
                start_date = datetime.strptime(start_str, '%Y-%m-%d')\
                                     .replace(tzinfo=timezone.utc)
                end_date   = datetime.strptime(end_str,   '%Y-%m-%d')\
                                     .replace(tzinfo=timezone.utc)
            except ValueError:
                return jsonify({
                    "error": "Invalid date format. Use YYYY-MM-DD"
                }), 400
        else:
            # Monthly: first day of current month to now
            start_date = now.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date   = now

        db = get_firestore_client()

        # Calculate KPIs
        lead_measures = calculate_lead_measures(
            db, employee_uid, start_date, end_date)
        lag_measures  = calculate_lag_measures(
            db, employee_uid, start_date, end_date)

        # Get targets for this employee
        targets = get_employee_targets(db, employee_uid, period)

        # Get employee info
        user_doc  = db.collection('users').document(employee_uid).get()
        user_name = ''
        if user_doc.exists:
            u = user_doc.to_dict()
            user_name = u.get('displayName', u.get('email', ''))

        return jsonify({
            "employeeUid":  employee_uid,
            "employeeName": user_name,
            "period":       period,
            "startDate":    start_date.strftime('%Y-%m-%d'),
            "endDate":      end_date.strftime('%Y-%m-%d'),
            "leadMeasures": lead_measures,
            "lagMeasures":  lag_measures,
            "targets":      targets,
        })

    except Exception as e:
        print(f"Error fetching employee KPIs: {e}")
        return jsonify({"error": str(e)}), 500


def get_employee_targets(db, employee_uid, period='monthly'):
    """
    Fetches KPI targets for an employee from Firestore.
    Returns default targets if none are set.
    """
    try:
        targets_ref = db.collection('kpi_targets')\
                        .where('employeeUid', '==', employee_uid)\
                        .where('period', '==', period).get()

        if targets_ref:
            for t in targets_ref:
                return t.to_dict().get('targets', {})

        # Default targets if none set
        return {
            "outreachCount":         50,
            "connectionRate":        40.0,
            "initialMessageCount":   30,
            "replyRate":             30.0,
            "meetingConversionRate": 20.0,
            "meetingsScheduled":     5,
            "meetingsCompleted":     3,
            "interestedLeads":       8,
            "warmLeadsNurtured":     3,
        }
    except Exception as e:
        print(f"Error fetching targets: {e}")
        return {}


# ── ROUTE 2: Get KPIs for current user ────────────────────────────────────────
@kpi_bp.route('/api/kpi/me', methods=['GET'])
def get_my_kpis():
    """
    Shortcut — returns KPIs for the currently logged-in employee.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    uid = session['uid']
    # Delegate to get_employee_kpis
    from flask import current_app
    with current_app.test_request_context():
        pass

    try:
        period = request.args.get('period', 'monthly')
        now    = datetime.now(timezone.utc)

        if period == 'weekly':
            start_date = now - timedelta(days=7)
            end_date   = now
        else:
            start_date = now.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date   = now

        db = get_firestore_client()

        lead_measures = calculate_lead_measures(
            db, uid, start_date, end_date)
        lag_measures  = calculate_lag_measures(
            db, uid, start_date, end_date)
        targets       = get_employee_targets(db, uid, period)

        return jsonify({
            "employeeUid":  uid,
            "period":       period,
            "startDate":    start_date.strftime('%Y-%m-%d'),
            "endDate":      end_date.strftime('%Y-%m-%d'),
            "leadMeasures": lead_measures,
            "lagMeasures":  lag_measures,
            "targets":      targets,
        })

    except Exception as e:
        print(f"Error fetching my KPIs: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 3: Set KPI targets ───────────────────────────────────────────────────
@kpi_bp.route('/api/kpi/targets', methods=['POST'])
def set_kpi_targets():
    """
    Sets KPI targets for an employee or team.
    M1/M2 only.

    Request body:
    {
        "employeeUid": "uid-here",
        "period":      "monthly",
        "targets": {
            "outreachCount":         60,
            "connectionRate":        50.0,
            "initialMessageCount":   40,
            "replyRate":             35.0,
            "meetingConversionRate": 25.0,
            "meetingsScheduled":     8,
            "meetingsCompleted":     5,
            "interestedLeads":       10,
            "warmLeadsNurtured":     4
        }
    }
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    role = session['role']
    if role not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Only managers can set KPI targets"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    employee_uid = data.get('employeeUid', '').strip()
    period       = data.get('period', 'monthly')
    targets      = data.get('targets', {})

    if not employee_uid:
        return jsonify({"error": "Employee UID is required"}), 400
    if not targets:
        return jsonify({"error": "Targets are required"}), 400

    try:
        db = get_firestore_client()

        # Check if targets already exist for this employee + period
        existing = db.collection('kpi_targets')\
                     .where('employeeUid', '==', employee_uid)\
                     .where('period', '==', period).get()

        target_data = {
            "employeeUid": employee_uid,
            "setByUid":    session['uid'],
            "period":      period,
            "targets":     targets,
            "updatedAt":   firestore.SERVER_TIMESTAMP
        }

        if existing:
            # Update existing target
            for doc in existing:
                doc.reference.update(target_data)
                target_id = doc.id
        else:
            # Create new target
            target_id = str(uuid.uuid4())
            target_data["targetId"]  = target_id
            target_data["createdAt"] = firestore.SERVER_TIMESTAMP
            db.collection('kpi_targets').document(target_id)\
              .set(target_data)

        return jsonify({
            "message":     "KPI targets set successfully",
            "employeeUid": employee_uid,
            "period":      period,
            "targets":     targets
        })

    except Exception as e:
        print(f"Error setting KPI targets: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 4: Get team KPI summary (M1) ────────────────────────────────────────
@kpi_bp.route('/api/kpi/team', methods=['GET'])
def get_team_kpis():
    """
    Returns KPIs for all members of the M1's team.
    Used by M1 dashboard KPI comparison view.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    uid  = session['uid']
    role = session['role']

    if role not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Access denied"}), 403

    try:
        db = get_firestore_client()

        # Get team members
        user_doc = db.collection('users').document(uid).get()
        team_id  = user_doc.to_dict().get('teamId', 'team_001')

        members_ref = db.collection('teams').document(team_id)\
                        .collection('members').get()

        period     = request.args.get('period', 'monthly')
        now        = datetime.now(timezone.utc)
        start_date = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date   = now

        if period == 'weekly':
            start_date = now - timedelta(days=7)

        team_kpis = []
        for member in members_ref:
            m    = member.to_dict()
            m_uid = m.get('uid')
            if not m_uid:
                continue

            lead_m   = calculate_lead_measures(db, m_uid, start_date, end_date)
            lag_m    = calculate_lag_measures(db, m_uid, start_date, end_date)
            targets  = get_employee_targets(db, m_uid, period)

            team_kpis.append({
                "employeeUid":  m_uid,
                "employeeName": m.get('displayName', m.get('email', '')),
                "leadMeasures": lead_m,
                "lagMeasures":  lag_m,
                "targets":      targets,
            })

        return jsonify({
            "teamId":   team_id,
            "period":   period,
            "teamKpis": team_kpis,
            "total":    len(team_kpis)
        })

    except Exception as e:
        print(f"Error fetching team KPIs: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 5: Create custom KPI column ─────────────────────────────────────────
@kpi_bp.route('/api/kpi/custom-columns', methods=['POST'])
def create_custom_kpi_column():
    """
    Creates a custom KPI column for the team.
    M1/M2 only.

    Request body:
    {
        "columnName":  "LinkedIn Posts",
        "description": "Number of LinkedIn posts made per week",
        "dataType":    "numeric"
    }
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    role = session['role']
    if role not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Only managers can create KPI columns"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    column_name = data.get('columnName', '').strip()
    description = data.get('description', '').strip()
    data_type   = data.get('dataType', 'numeric')

    if not column_name:
        return jsonify({"error": "Column name is required"}), 400

    if data_type not in ['numeric', 'percentage', 'text']:
        return jsonify({
            "error": "dataType must be numeric, percentage, or text"
        }), 400

    try:
        db = get_firestore_client()

        # Get manager's teamId
        user_doc = db.collection('users').document(session['uid']).get()
        team_id  = user_doc.to_dict().get('teamId', 'team_001')

        column_id = str(uuid.uuid4())

        column = {
            "columnId":   column_id,
            "columnName": column_name,
            "description": description,
            "dataType":   data_type,
            "teamId":     team_id,
            "isActive":   True,
            "hasData":    False,
            "createdBy":  session['uid'],
            "createdAt":  firestore.SERVER_TIMESTAMP
        }

        db.collection('kpi_custom_columns').document(column_id).set(column)

        return jsonify({
            "message":  "Custom KPI column created successfully",
            "columnId": column_id,
            "column":   {
                "columnId":   column_id,
                "columnName": column_name,
                "dataType":   data_type,
                "isActive":   True
            }
        }), 201

    except Exception as e:
        print(f"Error creating custom KPI column: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 6: Get custom KPI columns for team ──────────────────────────────────
@kpi_bp.route('/api/kpi/custom-columns', methods=['GET'])
def get_custom_kpi_columns():

    """
    Returns all custom KPI columns for the current user's team.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        db = get_firestore_client()

        user_doc = db.collection('users').document(session['uid']).get()
        team_id  = user_doc.to_dict().get('teamId', 'team_001')

        columns_ref = db.collection('kpi_custom_columns')\
                        .where('teamId', '==', team_id)\
                        .where('isActive', '==', True).get()

        columns = []
        for col in columns_ref:
            c = col.to_dict()
            columns.append({
                "columnId":   c.get('columnId'),
                "columnName": c.get('columnName'),
                "description": c.get('description', ''),
                "dataType":   c.get('dataType', 'numeric'),
                "hasData":    c.get('hasData', False),
            })

        return jsonify({"columns": columns, "total": len(columns)})

    except Exception as e:
        print(f"Error fetching custom columns: {e}")
        return jsonify({"error": str(e)}), 500

        # ── ROUTE 12: Get ALL custom KPI columns including inactive (M1/M2) ────────────
@kpi_bp.route('/api/kpi/custom-columns/all', methods=['GET'])
def get_all_custom_kpi_columns():
    """
    Returns ALL custom KPI columns including inactive ones.
    Used by M1/M2 dashboard to manage columns (deactivate/reactivate).
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    if session['role'] not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Access denied"}), 403

    try:
        db = get_firestore_client()

        user_doc = db.collection('users')\
                     .document(session['uid']).get()
        team_id  = user_doc.to_dict().get('teamId', 'team_001')

        columns_ref = db.collection('kpi_custom_columns')\
                        .where('teamId', '==', team_id).get()

        columns = []
        for col in columns_ref:
            c = col.to_dict()
            columns.append({
                "columnId":    c.get('columnId'),
                "columnName":  c.get('columnName'),
                "description": c.get('description', ''),
                "dataType":    c.get('dataType', 'numeric'),
                "isActive":    c.get('isActive', True),
                "hasData":     c.get('hasData', False),
            })

        # Sort: active first then inactive
        columns.sort(key=lambda x: (not x['isActive'], x['columnName']))

        return jsonify({
            "columns":       columns,
            "total":         len(columns),
            "activeCount":   sum(1 for c in columns if c['isActive']),
            "inactiveCount": sum(1 for c in columns if not c['isActive'])
        })

    except Exception as e:
        print(f"Error fetching all custom columns: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 7: Submit value for custom KPI column ────────────────────────────────
@kpi_bp.route('/api/kpi/custom-columns/<column_id>/entry',
              methods=['POST'])
def submit_custom_kpi_entry(column_id):
    """
    Employee submits a value for a custom KPI column.

    Request body:
    { "value": 15, "entryDate": "2026-04-25" }
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    value      = data.get('value')
    entry_date = data.get('entryDate', '')

    if value is None:
        return jsonify({"error": "Value is required"}), 400

    try:
        db     = get_firestore_client()
        entry_id = str(uuid.uuid4())

        entry = {
            "entryId":    entry_id,
            "columnId":   column_id,
            "employeeUid": session['uid'],
            "value":      value,
            "entryDate":  entry_date,
            "createdAt":  firestore.SERVER_TIMESTAMP
        }

        db.collection('kpi_custom_entries').document(entry_id).set(entry)

        # Mark column as having data
        db.collection('kpi_custom_columns').document(column_id)\
          .update({"hasData": True})

        return jsonify({
            "message": "KPI entry submitted successfully",
            "entryId": entry_id
        }), 201

    except Exception as e:
        print(f"Error submitting KPI entry: {e}")
        return jsonify({"error": str(e)}), 500

     # ── ROUTE 8: Get KPI trend data ────────────────────────────────────────────────
@kpi_bp.route('/api/kpi/trend/<employee_uid>', methods=['GET'])
def get_kpi_trend(employee_uid):
    """
    Returns KPI values for the last 6 weeks or 6 months
    so the frontend can draw a line chart.

    Query params:
    - ?period=weekly  → last 6 weeks
    - ?period=monthly → last 6 months (default)
    - ?kpi=outreachCount (which KPI to trend)
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    uid  = session['uid']
    role = session['role']

    if role == 'employee' and uid != employee_uid:
        return jsonify({"error": "Access denied"}), 403

    period  = request.args.get('period', 'monthly')
    kpi_key = request.args.get('kpi', 'outreachCount')
    now     = datetime.now(timezone.utc)

    try:
        db = get_firestore_client()

        if period == 'weekly':
            # Last 6 weeks
            buckets = []
            for i in range(5, -1, -1):
                week_start = now - timedelta(days=(i + 1) * 7)
                week_end   = now - timedelta(days=i * 7)
                buckets.append({
                    "label":      f"Wk -{i}" if i > 0 else "This Wk",
                    "start":      week_start,
                    "end":        week_end,
                })
        else:
            # Last 6 months
            buckets = []
            months  = ['Jan','Feb','Mar','Apr','May','Jun',
                       'Jul','Aug','Sep','Oct','Nov','Dec']
            for i in range(5, -1, -1):
                d = datetime(
                    now.year, now.month, 1,
                    tzinfo=timezone.utc
                ) - timedelta(days=i * 30)
                m_start = d.replace(day=1)
                if d.month == 12:
                    m_end = d.replace(year=d.year + 1, month=1, day=1)
                else:
                    m_end = d.replace(month=d.month + 1, day=1)
                buckets.append({
                    "label": f"{months[d.month-1]} {d.year}",
                    "start": m_start,
                    "end":   min(m_end, now)
                })

        # For each bucket calculate the KPI value
        trend_data = []
        for bucket in buckets:
            if kpi_key in [
                'outreachCount', 'connectionRate',
                'initialMessageCount', 'replyRate',
                'meetingConversionRate'
            ]:
                vals = calculate_lead_measures(
                    db, employee_uid,
                    bucket['start'], bucket['end']
                )
            else:
                vals = calculate_lag_measures(
                    db, employee_uid,
                    bucket['start'], bucket['end']
                )

            trend_data.append({
                "label": bucket['label'],
                "value": vals.get(kpi_key, 0)
            })

        return jsonify({
            "employeeUid": employee_uid,
            "kpi":         kpi_key,
            "period":      period,
            "trend":       trend_data,
            "labels":      [t['label'] for t in trend_data],
            "values":      [t['value'] for t in trend_data],
        })

    except Exception as e:
        print(f"Error fetching KPI trend: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 9: Org KPI summary with date range filter (M2) ──────────────────────
@kpi_bp.route('/api/kpi/org-summary', methods=['GET'])
def get_org_kpi_summary():
    """
    Returns org-wide KPI aggregated across all teams.
    Supports custom date range for M2 filtering.

    Query params:
    - ?startDate=2026-04-01
    - ?endDate=2026-04-30
    - ?period=monthly (default)
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    if session['role'] != 'm2_manager':
        return jsonify({"error": "Access denied"}), 403

    period   = request.args.get('period', 'monthly')
    now      = datetime.now(timezone.utc)

    start_str = request.args.get('startDate', '')
    end_str   = request.args.get('endDate', '')

    try:
        if start_str and end_str:
            start_date = datetime.strptime(
                start_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            end_date   = datetime.strptime(
                end_str,   '%Y-%m-%d').replace(tzinfo=timezone.utc)
        elif period == 'weekly':
            start_date = now - timedelta(days=7)
            end_date   = now
        else:
            start_date = now.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date   = now

        db = get_firestore_client()

        # Get all employees
        users_ref = db.collection('users')\
                      .where('role', '==', 'employee').get()

        # Aggregate KPIs across all employees
        org_lead = {
            'outreachCount': 0, 'connectionRate': 0.0,
            'initialMessageCount': 0, 'replyRate': 0.0,
            'meetingConversionRate': 0.0
        }
        org_lag = {
            'meetingsScheduled': 0, 'meetingsCompleted': 0,
            'interestedLeads': 0,   'warmLeadsNurtured': 0
        }
        employee_count = 0

        for user_doc in users_ref:
            uid = user_doc.to_dict().get('uid')
            if not uid:
                continue

            lead_m = calculate_lead_measures(db, uid, start_date, end_date)
            lag_m  = calculate_lag_measures(db, uid, start_date, end_date)

            org_lead['outreachCount']       += lead_m['outreachCount']
            org_lead['initialMessageCount'] += lead_m['initialMessageCount']
            org_lag['meetingsScheduled']    += lag_m['meetingsScheduled']
            org_lag['meetingsCompleted']    += lag_m['meetingsCompleted']
            org_lag['interestedLeads']      += lag_m['interestedLeads']
            org_lag['warmLeadsNurtured']    += lag_m['warmLeadsNurtured']
            employee_count += 1

        return jsonify({
            "period":         period,
            "startDate":      start_date.strftime('%Y-%m-%d'),
            "endDate":        end_date.strftime('%Y-%m-%d'),
            "employeeCount":  employee_count,
            "orgLeadMeasures": org_lead,
            "orgLagMeasures":  org_lag,
        })

    except Exception as e:
        print(f"Error fetching org KPI summary: {e}")
        return jsonify({"error": str(e)}), 500   

@kpi_bp.route('/api/kpi/custom-columns/<column_id>/deactivate',
              methods=['PATCH'])
def deactivate_custom_column(column_id):
    """
    Deactivates a custom KPI column.
    Historical entries are preserved — only isActive is set to False.
    SRS: Custom KPI columns cannot be deleted, only deactivated.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    if session['role'] not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Access denied"}), 403

    try:
        db  = get_firestore_client()
        ref = db.collection('kpi_custom_columns').document(column_id)
        doc = ref.get()

        if not doc.exists:
            return jsonify({"error": "Column not found"}), 404

        # Check if column has data — must preserve if so
        entries = db.collection('kpi_custom_entries')\
                    .where('columnId', '==', column_id).get()

        ref.update({
            "isActive":     False,
            "hasData":      len(list(entries)) > 0,
            "deactivatedAt": firestore.SERVER_TIMESTAMP,
            "deactivatedBy": session['uid']
        })

        return jsonify({
            "message":  "Column deactivated. Historical data preserved.",
            "columnId": column_id
        })

    except Exception as e:
        print(f"Error deactivating column: {e}")
        return jsonify({"error": str(e)}), 500    
        # ── ROUTE 10: Deactivate a custom KPI column ───────────────────────────────────
@kpi_bp.route('/api/kpi/custom-columns/<column_id>/deactivate',
              methods=['PATCH'])
def deactivate_custom_kpi_column(column_id):
    """
    Deactivates a custom KPI column.
    SRS Section 4.3: Custom KPI columns cannot be deleted
    once data has been entered — only deactivated.
    Historical entries are always preserved.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    if session['role'] not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Access denied"}), 403

    try:
        db  = get_firestore_client()
        ref = db.collection('kpi_custom_columns').document(column_id)
        doc = ref.get()

        if not doc.exists:
            return jsonify({"error": "Column not found"}), 404

        col_data = doc.to_dict()

        # Check if column already has data entries
        entries = db.collection('kpi_custom_entries')\
                    .where('columnId', '==', column_id).get()
        entry_count = len(list(entries))

        # Deactivate — NEVER delete if data exists
        ref.update({
            "isActive":      False,
            "hasData":       entry_count > 0,
            "deactivatedAt": firestore.SERVER_TIMESTAMP,
            "deactivatedBy": session['uid'],
        })

        msg = (
            f"Column deactivated. "
            f"{entry_count} historical "
            f"{'entry' if entry_count == 1 else 'entries'} preserved."
            if entry_count > 0
            else "Column deactivated."
        )

        return jsonify({
            "message":      msg,
            "columnId":     column_id,
            "entryCount":   entry_count,
            "dataPreserved": entry_count > 0
        })

    except Exception as e:
        print(f"Error deactivating KPI column: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 11: Reactivate a custom KPI column ───────────────────────────────────
@kpi_bp.route('/api/kpi/custom-columns/<column_id>/reactivate',
              methods=['PATCH'])
def reactivate_custom_kpi_column(column_id):
    """Reactivates a previously deactivated custom KPI column."""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    if session['role'] not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Access denied"}), 403

    try:
        db  = get_firestore_client()
        ref = db.collection('kpi_custom_columns').document(column_id)
        doc = ref.get()

        if not doc.exists:
            return jsonify({"error": "Column not found"}), 404

        ref.update({"isActive": True})

        return jsonify({
            "message":  "Column reactivated successfully.",
            "columnId": column_id
        })

    except Exception as e:
        print(f"Error reactivating KPI column: {e}")
        return jsonify({"error": str(e)}), 500