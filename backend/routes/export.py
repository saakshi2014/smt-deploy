"""
export.py — CSV Export API Routes
Allows M1/M2 to export leads, tasks, KPI data as CSV files.
"""

from flask import Blueprint, request, jsonify, session, Response
from firebase_config import get_firestore_client
import csv
import io
from datetime import datetime, timezone

export_bp = Blueprint('export', __name__)


def require_auth():
    if 'uid' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    return None


def format_date(dt):
    """Formats a Firestore timestamp to readable string."""
    if dt and hasattr(dt, 'strftime'):
        return dt.strftime('%d %b %Y')
    return str(dt)[:10] if dt else ''


# ── ROUTE 1: Export Leads as CSV ───────────────────────────────────────────────
@export_bp.route('/api/export/leads', methods=['GET'])
def export_leads():
    """
    Exports leads as a downloadable CSV file.
    - Employee: own leads only
    - M1: team leads
    - M2: all leads
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    uid  = session['uid']
    role = session['role']

    try:
        db = get_firestore_client()

        # Fetch stages for name resolution
        stages_ref = db.collection('pipeline_stages').get()
        stages_map = {s.to_dict()['stageId']: s.to_dict()['stageName']
                      for s in stages_ref}

        # Fetch users for name resolution
        users_ref = db.collection('users').get()
        users_map = {u.to_dict()['uid']: u.to_dict().get(
                         'displayName', u.to_dict().get('email', ''))
                     for u in users_ref}

        # Fetch leads based on role
        if role == 'employee':
            leads_ref = db.collection('leads')\
                          .where('employeeUid', '==', uid).get()
        elif role == 'm1_manager':
            user_doc  = db.collection('users').document(uid).get()
            team_id   = user_doc.to_dict().get('teamId', '')
            leads_ref = db.collection('leads')\
                          .where('teamId', '==', team_id).get()
        else:
            leads_ref = db.collection('leads').get()

        # Build CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([
            'Lead Name', 'Company', 'Email', 'Phone',
            'LinkedIn URL', 'Current Stage', 'Status',
            'Employee', 'Date Added'
        ])

        for lead_doc in leads_ref:
            lead = lead_doc.to_dict()
            writer.writerow([
                lead.get('name', ''),
                lead.get('company', ''),
                lead.get('email', ''),
                lead.get('phone', ''),
                lead.get('linkedinUrl', ''),
                stages_map.get(lead.get('currentStage', ''), ''),
                'Archived' if lead.get('isArchived') else 'Active',
                users_map.get(lead.get('employeeUid', ''), ''),
                format_date(lead.get('createdAt')),
            ])

        output.seek(0)
        filename = f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition':
                    f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        print(f"Error exporting leads: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 2: Export Tasks as CSV ───────────────────────────────────────────────
@export_bp.route('/api/export/tasks', methods=['GET'])
def export_tasks():
    """
    Exports tasks as a downloadable CSV file.
    M1/M2 only.
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

        if role == 'm1_manager':
            tasks_ref = db.collection('tasks')\
                          .where('assignedByUid', '==', uid)\
                          .where('isDeleted', '==', False).get()
        else:
            tasks_ref = db.collection('tasks')\
                          .where('isDeleted', '==', False).get()

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'Title', 'Description', 'Assigned To',
            'Assigned By', 'Priority', 'Status',
            'Due Date', 'Completed At'
        ])

        for task_doc in tasks_ref:
            task = task_doc.to_dict()
            due  = task.get('dueDate')
            due_str = format_date(due) if due else ''
            comp = task.get('completedAt')
            comp_str = format_date(comp) if comp else ''

            writer.writerow([
                task.get('title', ''),
                task.get('description', ''),
                task.get('assignedToName', ''),
                task.get('assignedByRole', ''),
                task.get('priority', ''),
                task.get('status', ''),
                due_str,
                comp_str,
            ])

        output.seek(0)
        filename = (f"tasks_export_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition':
                    f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        print(f"Error exporting tasks: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 3: Export KPI Data as CSV ────────────────────────────────────────────
@export_bp.route('/api/export/kpi', methods=['GET'])
def export_kpi():
    """
    Exports KPI summary data as CSV.
    M1: team members' KPI data
    M2: all employees
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

        # Get employees to export
        if role == 'm1_manager':
            user_doc    = db.collection('users').document(uid).get()
            team_id     = user_doc.to_dict().get('teamId', '')
            members_ref = db.collection('teams').document(team_id)\
                            .collection('members').get()
            employee_uids = [m.to_dict().get('uid') for m in members_ref
                             if m.to_dict().get('uid')]
        else:
            users_ref     = db.collection('users')\
                              .where('role', '==', 'employee').get()
            employee_uids = [u.to_dict().get('uid') for u in users_ref
                             if u.to_dict().get('uid')]

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'Employee', 'Email',
            'Outreach Count', 'Connection Rate %',
            'Messages Sent', 'Reply Rate %',
            'Meeting Conv Rate %',
            'Meetings Scheduled', 'Meetings Completed',
            'Interested Leads', 'Warm Leads Nurtured'
        ])

        from datetime import timedelta
        now        = datetime.now(timezone.utc)
        start_date = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)

        # Import KPI calculation functions
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from kpi import calculate_lead_measures, calculate_lag_measures

        users_ref = db.collection('users').get()
        users_map = {u.to_dict()['uid']: u.to_dict()
                     for u in users_ref}

        for emp_uid in employee_uids:
            user_data  = users_map.get(emp_uid, {})
            name       = user_data.get(
                'displayName', user_data.get('email', ''))
            email      = user_data.get('email', '')

            lead_m = calculate_lead_measures(db, emp_uid, start_date, now)
            lag_m  = calculate_lag_measures(db, emp_uid, start_date, now)

            writer.writerow([
                name, email,
                lead_m.get('outreachCount', 0),
                lead_m.get('connectionRate', 0),
                lead_m.get('initialMessageCount', 0),
                lead_m.get('replyRate', 0),
                lead_m.get('meetingConversionRate', 0),
                lag_m.get('meetingsScheduled', 0),
                lag_m.get('meetingsCompleted', 0),
                lag_m.get('interestedLeads', 0),
                lag_m.get('warmLeadsNurtured', 0),
            ])

        output.seek(0)
        filename = (f"kpi_export_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition':
                    f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        print(f"Error exporting KPI data: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 4: Export Coaching Sessions as CSV ────────────────────────────────────
@export_bp.route('/api/export/coaching', methods=['GET'])
def export_coaching():
    """Exports coaching sessions as CSV. M1/M2 only."""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    uid  = session['uid']
    role = session['role']

    if role not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Access denied"}), 403

    try:
        db = get_firestore_client()

        if role == 'm1_manager':
            sessions_ref = db.collection('coaching_sessions')\
                             .where('coachUid', '==', uid).get()
        else:
            sessions_ref = db.collection('coaching_sessions').get()

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'Specialist Name', 'Coach Name', 'Session Date',
            'Topic', 'Notes', 'Follow-up Date', 'Status'
        ])

        for doc in sessions_ref:
            s = doc.to_dict()
            writer.writerow([
                s.get('specialistName', ''),
                s.get('coachName', ''),
                format_date(s.get('sessionDate')),
                s.get('topic', ''),
                s.get('notes', ''),
                format_date(s.get('followUpDate')),
                'Completed' if s.get('isCompleted') else 'Pending',
            ])

        output.seek(0)
        filename = (f"coaching_export_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition':
                    f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        print(f"Error exporting coaching data: {e}")
        return jsonify({"error": str(e)}), 500