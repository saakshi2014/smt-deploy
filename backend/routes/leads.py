"""
leads.py — Leads API Routes
Handles: create lead, fetch leads, update lead, change stage
"""

from flask import Blueprint, request, jsonify, session
from firebase_config import get_firestore_client
from firebase_admin import firestore
import uuid
from datetime import datetime

leads_bp = Blueprint('leads', __name__)


# ── HELPER: Check authentication ───────────────────────────────────────────────
def require_auth():
    if 'uid' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    return None


# ── ROUTE 1: Create a new lead ─────────────────────────────────────────────────
@leads_bp.route('/api/leads', methods=['POST'])
def create_lead():
    """
    Creates a new lead in Firestore.
    Only employees and M1 managers can create leads.

    Request body:
    {
        "name":        "John Smith",
        "company":     "Acme Corp",
        "email":       "john@acme.com",
        "phone":       "+91 9876543210",
        "linkedinUrl": "https://linkedin.com/in/johnsmith"
    }
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate required fields
    name = data.get('name', '').strip()
    if not name:
        return jsonify({"error": "Lead name is required"}), 400

    uid    = session['uid']
    role   = session['role']

    # Determine teamId based on role
    db       = get_firestore_client()
    user_doc = db.collection('users').document(uid).get()
    if not user_doc.exists:
        return jsonify({"error": "User profile not found"}), 404

    user_data = user_doc.to_dict()
    team_id   = user_data.get('teamId', 'team_001')

    # Generate unique lead ID
    lead_id = str(uuid.uuid4())

    # Build the lead document
    lead = {
        "leadId":       lead_id,
        "employeeUid":  uid,
        "teamId":       team_id,
        "name":         name,
        "company":      data.get('company', '').strip(),
        "email":        data.get('email', '').strip(),
        "phone":        data.get('phone', '').strip(),
        "linkedinUrl":  data.get('linkedinUrl', '').strip(),
        "currentStage": "stage_1_1",  # Always starts at Qualified – Pending Outreach
        "isArchived":   False,
        "createdAt":    firestore.SERVER_TIMESTAMP,
        "updatedAt":    firestore.SERVER_TIMESTAMP
    }

    # Save to Firestore
    db.collection('leads').document(lead_id).set(lead)

    # Write first audit log entry
    log_id = str(uuid.uuid4())
    db.collection('audit_logs').document(log_id).set({
        "logId":       log_id,
        "leadId":      lead_id,
        "employeeUid": uid,
        "fromStage":   None,
        "toStage":     "stage_1_1",
        "changedAt":   firestore.SERVER_TIMESTAMP,
        "notes":       "Lead created"
    })

    return jsonify({
        "message": "Lead created successfully",
        "leadId":  lead_id,
        "lead":    {
            "leadId":       lead_id,
            "name":         lead['name'],
            "company":      lead['company'],
            "email":        lead['email'],
            "phone":        lead['phone'],
            "linkedinUrl":  lead['linkedinUrl'],
            "currentStage": "stage_1_1",
            "stageName":    "Qualified – Pending Outreach",
            "isArchived":   False,
        }
    }), 201


# ── ROUTE 2: Get all leads for current user ────────────────────────────────────
@leads_bp.route('/api/leads', methods=['GET'])
def get_leads():
    """
    Returns leads based on user role:
    - Employee: only their own leads
    - M1 Manager: all leads in their team
    - M2 Manager: all leads in the organisation
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    uid  = session['uid']
    role = session['role']

    try:
        db = get_firestore_client()

        # Fetch leads based on role
        if role == 'employee':
            leads_ref = db.collection('leads')\
                          .where('employeeUid', '==', uid)\
                          .get()
        elif role == 'm1_manager':
            # Get M1's teamId from their user document
            user_doc  = db.collection('users').document(uid).get()
            team_id   = user_doc.to_dict().get('teamId', '')
            leads_ref = db.collection('leads')\
                          .where('teamId', '==', team_id)\
                          .get()
        else:
            # M2 sees all leads
            leads_ref = db.collection('leads').get()

        # Fetch all pipeline stages for resolving stage names
        stages_ref = db.collection('pipeline_stages').get()
        stages_map = {}
        for stage in stages_ref:
            s = stage.to_dict()
            stages_map[s['stageId']] = s['stageName']

        # Build the leads list
        leads_list = []
        for lead_doc in leads_ref:
            lead = lead_doc.to_dict()

            # Resolve stage name
            current_stage_id   = lead.get('currentStage', 'stage_1_1')
            current_stage_name = stages_map.get(current_stage_id, 'Unknown')

            # Format timestamps
            created_at = lead.get('createdAt')
            if hasattr(created_at, 'strftime'):
                created_at = created_at.strftime('%d %b %Y')
            else:
                created_at = 'Just now'

            leads_list.append({
                "leadId":        lead.get('leadId'),
                "name":          lead.get('name'),
                "company":       lead.get('company', '—'),
                "email":         lead.get('email', '—'),
                "phone":         lead.get('phone', '—'),
                "linkedinUrl":   lead.get('linkedinUrl', ''),
                "currentStage":  current_stage_id,
                "stageName":     current_stage_name,
                "isArchived":    lead.get('isArchived', False),
                "employeeUid":   lead.get('employeeUid'),
                "createdAt":     created_at,
            })

        # Sort by most recently created first
       # Sort by most recently created first
        leads_list.sort(key=lambda x: x['leadId'], reverse=True)

        # ── PAGINATION ────────────────────────────────────────────────────────
        page       = int(request.args.get('page', 1))
        per_page   = int(request.args.get('per_page', 50))
        total      = len(leads_list)
        start      = (page - 1) * per_page
        end        = start + per_page
        paginated  = leads_list[start:end]
        total_pages = (total + per_page - 1) // per_page

        return jsonify({
            "leads":       paginated,
            "total":       total,
            "activeCount": sum(1 for l in leads_list
                               if not l['isArchived']),
            "page":        page,
            "perPage":     per_page,
            "totalPages":  total_pages,
            "hasNext":     page < total_pages,
            "hasPrev":     page > 1,
        })
    except Exception as e:
        print(f"Error fetching leads: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 3: Update lead details ───────────────────────────────────────────────
@leads_bp.route('/api/leads/<lead_id>', methods=['PATCH'])
def update_lead(lead_id):
    """
    Updates lead details (name, company, email, phone, linkedinUrl).
    Does NOT change the pipeline stage — that is a separate route.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        db       = get_firestore_client()
        lead_ref = db.collection('leads').document(lead_id)
        lead_doc = lead_ref.get()

        if not lead_doc.exists:
            return jsonify({"error": "Lead not found"}), 404

        # Only allow updating these fields
        allowed_fields = ['name', 'company', 'email', 'phone', 'linkedinUrl']
        update_data    = {k: v for k, v in data.items() if k in allowed_fields}
        update_data['updatedAt'] = firestore.SERVER_TIMESTAMP

        lead_ref.update(update_data)

        return jsonify({"message": "Lead updated successfully"})

    except Exception as e:
        print(f"Error updating lead: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 4: Change pipeline stage ────────────────────────────────────────────
@leads_bp.route('/api/leads/<lead_id>/stage', methods=['PATCH'])
def change_stage(lead_id):
    """
    Changes the pipeline stage of a lead.
    Also writes an audit log entry for every stage change.

    Request body: { "newStage": "stage_2", "notes": "optional note" }
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    data      = request.get_json()
    new_stage = data.get('newStage') if data else None

    if not new_stage:
        return jsonify({"error": "newStage is required"}), 400

    try:
        db       = get_firestore_client()
        lead_ref = db.collection('leads').document(lead_id)
        lead_doc = lead_ref.get()

        if not lead_doc.exists:
            return jsonify({"error": "Lead not found"}), 404

        lead_data  = lead_doc.to_dict()
        from_stage = lead_data.get('currentStage')

        # Check if new stage exists
        stage_doc = db.collection('pipeline_stages').document(new_stage).get()
        if not stage_doc.exists:
            return jsonify({"error": "Invalid stage"}), 400

        stage_data = stage_doc.to_dict()

        # Update the lead
        is_archived = stage_data.get('isArchived', False)
        lead_ref.update({
            "currentStage": new_stage,
            "isArchived":   is_archived,
            "updatedAt":    firestore.SERVER_TIMESTAMP
        })

        # Write audit log
        log_id = str(uuid.uuid4())
        db.collection('audit_logs').document(log_id).set({
            "logId":       log_id,
            "leadId":      lead_id,
            "employeeUid": session['uid'],
            "fromStage":   from_stage,
            "toStage":     new_stage,
            "changedAt":   firestore.SERVER_TIMESTAMP,
            "notes":       data.get('notes', '')
        })

        return jsonify({
            "message":      "Stage updated successfully",
            "leadId":       lead_id,
            "fromStage":    from_stage,
            "toStage":      new_stage,
            "stageName":    stage_data.get('stageName'),
            "isArchived":   is_archived
        })

    except Exception as e:
        print(f"Error changing stage: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 5: Get lead history (audit log) ─────────────────────────────────────
@leads_bp.route('/api/leads/<lead_id>/history', methods=['GET'])
def get_lead_history(lead_id):
    """
    Returns the full audit trail for a lead.
    Shows every stage change with who changed it and when.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        db   = get_firestore_client()
        logs = db.collection('audit_logs')\
                 .where('leadId', '==', lead_id)\
                 .get()

        # Fetch stage names
        stages_ref = db.collection('pipeline_stages').get()
        stages_map = {s.to_dict()['stageId']: s.to_dict()['stageName']
                      for s in stages_ref}

        history = []
        for log in logs:
            entry = log.to_dict()
            history.append({
                "logId":         entry.get('logId'),
                "fromStage":     entry.get('fromStage'),
                "fromStageName": stages_map.get(entry.get('fromStage'), 'Start'),
                "toStage":       entry.get('toStage'),
                "toStageName":   stages_map.get(entry.get('toStage'), 'Unknown'),
                "notes":         entry.get('notes', ''),
                "changedAt":     str(entry.get('changedAt', ''))
            })

        return jsonify({"history": history, "total": len(history)})

    except Exception as e:
        print(f"Error fetching history: {e}")
        return jsonify({"error": str(e)}), 500
    # ── ROUTE 6: Get team members (for M1 dashboard) ──────────────────────────────
@leads_bp.route('/api/team/members', methods=['GET'])
def get_team_members():
    """
    Returns all members of the M1 manager's team.
    Used by M1 dashboard to show employee names in the table.
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

        # Get M1's teamId
        user_doc = db.collection('users').document(uid).get()
        team_id  = user_doc.to_dict().get('teamId', 'team_001')

        # Get all members of the team
        members_ref = db.collection('teams').document(team_id)\
                        .collection('members').get()

        members = []
        for member in members_ref:
            m = member.to_dict()
            members.append({
                "uid":         m.get('uid'),
                "email":       m.get('email'),
                "displayName": m.get('displayName', m.get('email', ''))
            })

        return jsonify({"members": members, "total": len(members)})

    except Exception as e:
        print(f"Error fetching team members: {e}")
        return jsonify({"error": str(e)}), 500
    # ── ROUTE 7: Delete a lead ─────────────────────────────────────────────────────
@leads_bp.route('/api/leads/<lead_id>', methods=['DELETE'])
def delete_lead(lead_id):
    """
    Permanently deletes a lead and its audit logs.
    Only M1 Managers and M2 Managers can delete leads.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    role = session['role']
    if role not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Only managers can delete leads"}), 403

    try:
        db       = get_firestore_client()
        lead_ref = db.collection('leads').document(lead_id)
        lead_doc = lead_ref.get()

        if not lead_doc.exists:
            return jsonify({"error": "Lead not found"}), 404

        # Delete all audit logs for this lead
        logs = db.collection('audit_logs')\
                 .where('leadId', '==', lead_id).get()
        for log in logs:
            log.reference.delete()

        # Delete the lead itself
        lead_ref.delete()

        return jsonify({"message": "Lead deleted successfully"})

    except Exception as e:
        print(f"Error deleting lead: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 8: Archive / Unarchive a lead ───────────────────────────────────────
@leads_bp.route('/api/leads/<lead_id>/archive', methods=['PATCH'])
def toggle_archive(lead_id):
    """
    Toggles the archived status of a lead.
    Archived leads are excluded from active pipeline counts.

    Request body: { "archive": true } or { "archive": false }
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    data    = request.get_json()
    archive = data.get('archive', True) if data else True

    try:
        db       = get_firestore_client()
        lead_ref = db.collection('leads').document(lead_id)
        lead_doc = lead_ref.get()

        if not lead_doc.exists:
            return jsonify({"error": "Lead not found"}), 404

        lead_ref.update({
            "isArchived": archive,
            "updatedAt":  firestore.SERVER_TIMESTAMP
        })

        # Write audit log for archive action
        log_id = str(uuid.uuid4())
        db.collection('audit_logs').document(log_id).set({
            "logId":       log_id,
            "leadId":      lead_id,
            "employeeUid": session['uid'],
            "fromStage":   lead_doc.to_dict().get('currentStage'),
            "toStage":     lead_doc.to_dict().get('currentStage'),
            "changedAt":   firestore.SERVER_TIMESTAMP,
            "notes":       "Lead archived" if archive else "Lead unarchived"
        })

        return jsonify({
            "message":    "Lead archived" if archive else "Lead unarchived",
            "isArchived": archive
        })

    except Exception as e:
        print(f"Error toggling archive: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 9: Get single lead details ──────────────────────────────────────────
@leads_bp.route('/api/leads/<lead_id>', methods=['GET'])
def get_lead(lead_id):
    """
    Returns full details of a single lead.
    Used by the lead detail panel.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        db       = get_firestore_client()
        lead_doc = db.collection('leads').document(lead_id).get()

        if not lead_doc.exists:
            return jsonify({"error": "Lead not found"}), 404

        lead = lead_doc.to_dict()

        # Resolve stage name
        stages_ref = db.collection('pipeline_stages').get()
        stages_map = {s.to_dict()['stageId']: s.to_dict()['stageName']
                      for s in stages_ref}

        current_stage_id   = lead.get('currentStage', 'stage_1_1')
        current_stage_name = stages_map.get(current_stage_id, 'Unknown')

        return jsonify({
            "leadId":       lead.get('leadId'),
            "name":         lead.get('name'),
            "company":      lead.get('company', ''),
            "email":        lead.get('email', ''),
            "phone":        lead.get('phone', ''),
            "linkedinUrl":  lead.get('linkedinUrl', ''),
            "currentStage": current_stage_id,
            "stageName":    current_stage_name,
            "isArchived":   lead.get('isArchived', False),
            "employeeUid":  lead.get('employeeUid'),
            "teamId":       lead.get('teamId'),
        })

    except Exception as e:
        print(f"Error fetching lead: {e}")
        return jsonify({"error": str(e)}), 500
    
    # ── ROUTE 10: Get org-wide summary (M2 only) ──────────────────────────────────
@leads_bp.route('/api/org/summary', methods=['GET'])
def get_org_summary():
    """
    Returns organisation-wide summary for M2 Manager.
    Includes total leads, active leads, meetings scheduled/completed,
    and per-team breakdown.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    if session['role'] != 'm2_manager':
        return jsonify({"error": "Access denied"}), 403

    try:
        db = get_firestore_client()

        # Fetch all leads
        all_leads = db.collection('leads').get()
        leads_data = [l.to_dict() for l in all_leads]

        # Fetch all teams
        all_teams = db.collection('teams').get()
        teams_map = {}
        for team in all_teams:
            t = team.to_dict()
            teams_map[t['teamId']] = t['teamName']

        # Fetch all users for name resolution
        all_users = db.collection('users').get()
        users_map = {}
        for user in all_users:
            u = user.to_dict()
            users_map[u['uid']] = u.get('displayName', u.get('email', ''))

        # Fetch all pipeline stages
        stages_ref = db.collection('pipeline_stages').get()
        stages_map = {}
        for stage in stages_ref:
            s = stage.to_dict()
            stages_map[s['stageId']] = s['stageName']

        # Calculate org-wide stats
        total_leads       = len(leads_data)
        active_leads      = sum(1 for l in leads_data if not l.get('isArchived'))
        meetings_scheduled = sum(
            1 for l in leads_data if l.get('currentStage') == 'stage_7'
        )
        meetings_completed = sum(
            1 for l in leads_data if l.get('currentStage') == 'stage_8'
        )
        interested_leads  = sum(
            1 for l in leads_data if l.get('currentStage') == 'stage_6_1'
        )
        warm_leads        = sum(
            1 for l in leads_data if l.get('currentStage') == 'stage_6_3'
        )

        # Per-team breakdown
        team_breakdown = {}
        for lead in leads_data:
            team_id = lead.get('teamId', 'unknown')
            if team_id not in team_breakdown:
                team_breakdown[team_id] = {
                    "teamId":            team_id,
                    "teamName":          teams_map.get(team_id, 'Unknown Team'),
                    "totalLeads":        0,
                    "activeLeads":       0,
                    "meetingsScheduled": 0,
                    "meetingsCompleted": 0,
                    "interestedLeads":   0,
                }
            team_breakdown[team_id]['totalLeads'] += 1
            if not lead.get('isArchived'):
                team_breakdown[team_id]['activeLeads'] += 1
            if lead.get('currentStage') == 'stage_7':
                team_breakdown[team_id]['meetingsScheduled'] += 1
            if lead.get('currentStage') == 'stage_8':
                team_breakdown[team_id]['meetingsCompleted'] += 1
            if lead.get('currentStage') == 'stage_6_1':
                team_breakdown[team_id]['interestedLeads'] += 1

        # Stage distribution across whole org
        stage_counts = {}
        for lead in leads_data:
            sid = lead.get('currentStage', 'stage_1_1')
            stage_counts[sid] = stage_counts.get(sid, 0) + 1

        stage_distribution = [
            {
                "stageId":   sid,
                "stageName": stages_map.get(sid, 'Unknown'),
                "count":     count
            }
            for sid, count in stage_counts.items()
        ]

        return jsonify({
            "orgStats": {
                "totalLeads":        total_leads,
                "activeLeads":       active_leads,
                "meetingsScheduled": meetings_scheduled,
                "meetingsCompleted": meetings_completed,
                "interestedLeads":   interested_leads,
                "warmLeads":         warm_leads,
                "archivedLeads":     total_leads - active_leads,
            },
            "teamBreakdown":    list(team_breakdown.values()),
            "stageDistribution": stage_distribution,
            "totalTeams":        len(team_breakdown),
        })

    except Exception as e:
        print(f"Error fetching org summary: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 11: Get all leads for a specific team (M2 drill-down) ───────────────
@leads_bp.route('/api/org/teams/<team_id>/leads', methods=['GET'])
def get_team_leads_m2(team_id):
    """
    Returns all leads for a specific team.
    Used by M2 Manager when drilling down into a specific team.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    if session['role'] != 'm2_manager':
        return jsonify({"error": "Access denied"}), 403

    try:
        db = get_firestore_client()

        # Fetch leads for this team
        leads_ref = db.collection('leads')\
                      .where('teamId', '==', team_id).get()

        # Fetch stage names
        stages_ref = db.collection('pipeline_stages').get()
        stages_map = {s.to_dict()['stageId']: s.to_dict()['stageName']
                      for s in stages_ref}

        # Fetch user names
        users_ref  = db.collection('users').get()
        users_map  = {u.to_dict()['uid']: u.to_dict().get(
                          'displayName', u.to_dict().get('email', ''))
                      for u in users_ref}

        leads_list = []
        for lead_doc in leads_ref:
            lead = lead_doc.to_dict()
            current_stage_id   = lead.get('currentStage', 'stage_1_1')
            current_stage_name = stages_map.get(current_stage_id, 'Unknown')
            employee_name      = users_map.get(
                lead.get('employeeUid', ''), 'Unknown'
            )

            created_at = lead.get('createdAt')
            if hasattr(created_at, 'strftime'):
                created_at = created_at.strftime('%d %b %Y')
            else:
                created_at = 'Recently'

            leads_list.append({
                "leadId":       lead.get('leadId'),
                "name":         lead.get('name'),
                "company":      lead.get('company', '—'),
                "email":        lead.get('email', '—'),
                "currentStage": current_stage_id,
                "stageName":    current_stage_name,
                "isArchived":   lead.get('isArchived', False),
                "employeeUid":  lead.get('employeeUid'),
                "employeeName": employee_name,
                "linkedinUrl":  lead.get('linkedinUrl', ''),
                "createdAt":    created_at,
            })

        leads_list.sort(key=lambda x: x['leadId'], reverse=True)

        return jsonify({
            "leads":  leads_list,
            "total":  len(leads_list),
            "teamId": team_id,
        })

    except Exception as e:
        print(f"Error fetching team leads for M2: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 12: Get all teams (M2 only) ─────────────────────────────────────────
@leads_bp.route('/api/org/teams', methods=['GET'])
def get_all_teams():
    """
    Returns all teams in the organisation.
    Used by M2 Manager dashboard.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    if session['role'] != 'm2_manager':
        return jsonify({"error": "Access denied"}), 403

    try:
        db        = get_firestore_client()
        teams_ref = db.collection('teams').get()

        # Fetch all users for M1 name resolution
        users_ref = db.collection('users').get()
        users_map = {u.to_dict()['uid']: u.to_dict().get(
                         'displayName', u.to_dict().get('email', ''))
                     for u in users_ref}

        teams = []
        for team_doc in teams_ref:
            team = team_doc.to_dict()
            m1_name = users_map.get(
                team.get('m1ManagerUid', ''), 'Unknown M1'
            )
            teams.append({
                "teamId":   team.get('teamId'),
                "teamName": team.get('teamName'),
                "m1Name":   m1_name,
                "isActive": team.get('isActive', True),
            })

        return jsonify({"teams": teams, "total": len(teams)})

    except Exception as e:
        print(f"Error fetching teams: {e}")
        return jsonify({"error": str(e)}), 500

    # ── ROUTE 10: Bulk import leads from CSV ───────────────────────────────────────
@leads_bp.route('/api/leads/bulk-import', methods=['POST'])
def bulk_import_leads():
    """
    Imports multiple leads from a CSV file upload.
    Accepts multipart/form-data with a 'file' field.

    CSV format (required columns):
    name, company, email, phone, linkedinUrl

    Returns a summary of imported/skipped/failed rows.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    uid  = session['uid']
    role = session['role']

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith('.csv'):
        return jsonify({"error": "Only CSV files are supported"}), 400

    try:
        import csv
        import io

        db      = get_firestore_client()
        content = file.read().decode('utf-8-sig')
        reader  = csv.DictReader(io.StringIO(content))

        # Validate headers
        required_cols = {'name'}
        if not reader.fieldnames:
            return jsonify({"error": "CSV file is empty"}), 400

        headers_lower = {h.lower().strip() for h in reader.fieldnames}
        missing = required_cols - headers_lower
        if missing:
            return jsonify({
                "error": f"Missing required column: {missing}"
            }), 400

        # Get user's teamId
        user_doc = db.collection('users').document(uid).get()
        team_id  = user_doc.to_dict().get('teamId', 'team_001')

        imported = 0
        skipped  = 0
        errors   = []

        # Process each row
        batch      = db.batch()
        batch_size = 0
        MAX_BATCH  = 450  # Firestore batch limit is 500

        for row_num, row in enumerate(reader, start=2):
            try:
                # Normalize keys
                row_clean = {k.lower().strip(): v.strip()
                             for k, v in row.items() if k}

                name = row_clean.get('name', '').strip()
                if not name:
                    skipped += 1
                    errors.append(f"Row {row_num}: Name is empty — skipped")
                    continue

                lead_id = str(uuid.uuid4())
                lead = {
                    "leadId":       lead_id,
                    "employeeUid":  uid,
                    "teamId":       team_id,
                    "name":         name,
                    "company":      row_clean.get('company', ''),
                    "email":        row_clean.get('email', ''),
                    "phone":        row_clean.get('phone', ''),
                    "linkedinUrl":  row_clean.get('linkedinurl', ''),
                    "currentStage": "stage_1_1",
                    "isArchived":   False,
                    "createdAt":    firestore.SERVER_TIMESTAMP,
                    "updatedAt":    firestore.SERVER_TIMESTAMP,
                }

                lead_ref = db.collection('leads').document(lead_id)
                batch.set(lead_ref, lead)

                # Also write audit log in batch
                log_id  = str(uuid.uuid4())
                log_ref = db.collection('audit_logs').document(log_id)
                batch.set(log_ref, {
                    "logId":       log_id,
                    "leadId":      lead_id,
                    "employeeUid": uid,
                    "fromStage":   None,
                    "toStage":     "stage_1_1",
                    "changedAt":   firestore.SERVER_TIMESTAMP,
                    "notes":       "Imported from CSV"
                })

                batch_size += 2  # lead + audit log
                imported   += 1

                # Commit batch every MAX_BATCH operations
                if batch_size >= MAX_BATCH:
                    batch.commit()
                    batch      = db.batch()
                    batch_size = 0

            except Exception as row_error:
                skipped += 1
                errors.append(
                    f"Row {row_num}: {str(row_error)}")

        # Commit remaining
        if batch_size > 0:
            batch.commit()

        return jsonify({
            "message":  f"Import complete: {imported} imported, "
                        f"{skipped} skipped",
            "imported": imported,
            "skipped":  skipped,
            "errors":   errors[:10]  # Return first 10 errors only
        })

    except UnicodeDecodeError:
        return jsonify({
            "error": "File encoding error. Save CSV as UTF-8 and retry."
        }), 400
    except Exception as e:
        print(f"Error importing leads: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 11: Download CSV import template ─────────────────────────────────────
@leads_bp.route('/api/leads/import-template', methods=['GET'])
def download_import_template():
    """
    Returns a blank CSV template for bulk lead import.
    Employee downloads this, fills it in, then uploads it.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    from flask import Response
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'name', 'company', 'email', 'phone', 'linkedinUrl'
    ])

    # Example rows
    writer.writerow([
        'John Smith', 'Acme Corp',
        'john@acme.com', '+91 9876543210',
        'https://linkedin.com/in/johnsmith'
    ])
    writer.writerow([
        'Jane Doe', 'Tech Ventures',
        'jane@techventures.com', '+91 9876543211',
        'https://linkedin.com/in/janedoe'
    ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition':
                'attachment; filename="leads_import_template.csv"'
        }
    )    