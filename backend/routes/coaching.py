"""
coaching.py — Coaching Session Tracker API Routes
M1 Managers log coaching sessions against their team members.
Sessions include topic, notes, and optional follow-up date.
"""

from flask import Blueprint, request, jsonify, session
from firebase_config import get_firestore_client
from firebase_admin import firestore
import uuid
from datetime import datetime, timezone

coaching_bp = Blueprint('coaching', __name__)


def require_auth():
    if 'uid' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    return None


# ── ROUTE 1: Create a coaching session ────────────────────────────────────────
@coaching_bp.route('/api/coaching', methods=['POST'])
def create_coaching_session():
    """
    M1 logs a new coaching session for a team member.

    Request body:
    {
        "specialistUid": "employee-uid",
        "sessionDate":   "2026-05-01",
        "topic":         "Improving outreach rate",
        "notes":         "Discussed LinkedIn messaging strategy",
        "followUpDate":  "2026-05-15"
    }
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    role = session['role']
    if role not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Only managers can log coaching sessions"}),\
               403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    specialist_uid  = data.get('specialistUid', '').strip()
    session_date_str = data.get('sessionDate', '').strip()
    topic           = data.get('topic', '').strip()
    notes           = data.get('notes', '').strip()
    follow_up_str   = data.get('followUpDate', '').strip()

    if not specialist_uid:
        return jsonify({"error": "Specialist UID is required"}), 400
    if not topic:
        return jsonify({"error": "Session topic is required"}), 400
    if not session_date_str:
        return jsonify({"error": "Session date is required"}), 400

    try:
        # Parse dates
        session_date = datetime.strptime(session_date_str, '%Y-%m-%d')\
                               .replace(tzinfo=timezone.utc)
        follow_up_date = None
        if follow_up_str:
            follow_up_date = datetime.strptime(follow_up_str, '%Y-%m-%d')\
                                     .replace(tzinfo=timezone.utc)

        db = get_firestore_client()

        # Get specialist info
        specialist_doc = db.collection('users')\
                           .document(specialist_uid).get()
        if not specialist_doc.exists:
            return jsonify({"error": "Specialist not found"}), 404

        specialist_data = specialist_doc.to_dict()
        specialist_name = specialist_data.get(
            'displayName', specialist_data.get('email', ''))

        # Get coach info
        coach_doc  = db.collection('users').document(session['uid']).get()
        coach_name = coach_doc.to_dict().get(
            'displayName',
            coach_doc.to_dict().get('email', '')) if coach_doc.exists else ''

        # Get teamId
        user_doc = db.collection('users').document(session['uid']).get()
        team_id  = user_doc.to_dict().get('teamId', 'team_001')

        session_id = str(uuid.uuid4())

        coaching_session = {
            "sessionId":      session_id,
            "specialistUid":  specialist_uid,
            "specialistName": specialist_name,
            "coachUid":       session['uid'],
            "coachName":      coach_name,
            "teamId":         team_id,
            "sessionDate":    session_date,
            "topic":          topic,
            "notes":          notes,
            "followUpDate":   follow_up_date,
            "isCompleted":    False,
            "createdAt":      firestore.SERVER_TIMESTAMP,
        }

        db.collection('coaching_sessions')\
          .document(session_id).set(coaching_session)

        return jsonify({
            "message":   "Coaching session logged successfully",
            "sessionId": session_id,
            "session": {
                "sessionId":      session_id,
                "specialistName": specialist_name,
                "topic":          topic,
                "sessionDate":    session_date_str,
                "followUpDate":   follow_up_str or None,
            }
        }), 201

    except ValueError as e:
        return jsonify({"error": f"Invalid date format: {e}"}), 400
    except Exception as e:
        print(f"Error creating coaching session: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 2: Get coaching sessions ────────────────────────────────────────────
@coaching_bp.route('/api/coaching', methods=['GET'])
def get_coaching_sessions():
    """
    Returns coaching sessions based on role:
    - M1: sessions they coached
    - M2: all sessions in org
    - Employee: sessions where they are the specialist

    Optional query params:
    - ?specialistUid=uid  → filter by specialist
    - ?upcoming=true      → only sessions with future follow-up dates
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    uid            = session['uid']
    role           = session['role']
    specialist_uid = request.args.get('specialistUid', '')
    upcoming_only  = request.args.get('upcoming', '').lower() == 'true'

    try:
        db = get_firestore_client()

        if role == 'employee':
            sessions_ref = db.collection('coaching_sessions')\
                             .where('specialistUid', '==', uid).get()
        elif role == 'm1_manager':
            sessions_ref = db.collection('coaching_sessions')\
                             .where('coachUid', '==', uid).get()
        else:
            # M2 sees all
            sessions_ref = db.collection('coaching_sessions').get()

        sessions_list = []
        now = datetime.now(timezone.utc)

        for doc in sessions_ref:
            s = doc.to_dict()

            # Filter by specialist if requested
            if specialist_uid and s.get('specialistUid') != specialist_uid:
                continue

            # Format dates
            session_date = s.get('sessionDate')
            if hasattr(session_date, 'strftime'):
                session_date_str = session_date.strftime('%d %b %Y')
                session_date_iso = session_date.strftime('%Y-%m-%d')
            else:
                session_date_str = str(session_date)[:10] \
                                   if session_date else ''
                session_date_iso = session_date_str

            follow_up = s.get('followUpDate')
            follow_up_str  = ''
            follow_up_iso  = ''
            is_follow_up_due = False

            if follow_up:
                if hasattr(follow_up, 'strftime'):
                    follow_up_str = follow_up.strftime('%d %b %Y')
                    follow_up_iso = follow_up.strftime('%Y-%m-%d')
                    follow_up_utc = follow_up.replace(tzinfo=timezone.utc)
                    is_follow_up_due = follow_up_utc <= now
                else:
                    follow_up_str = str(follow_up)[:10]
                    follow_up_iso = follow_up_str

            # Filter upcoming if requested
            if upcoming_only and not is_follow_up_due:
                continue

            sessions_list.append({
                "sessionId":       s.get('sessionId'),
                "specialistUid":   s.get('specialistUid'),
                "specialistName":  s.get('specialistName', ''),
                "coachUid":        s.get('coachUid'),
                "coachName":       s.get('coachName', ''),
                "teamId":          s.get('teamId'),
                "sessionDate":     session_date_str,
                "sessionDateIso":  session_date_iso,
                "topic":           s.get('topic', ''),
                "notes":           s.get('notes', ''),
                "followUpDate":    follow_up_str,
                "followUpDateIso": follow_up_iso,
                "isFollowUpDue":   is_follow_up_due,
                "isCompleted":     s.get('isCompleted', False),
            })

        # Sort newest first
        sessions_list.sort(
            key=lambda x: x['sessionDateIso'], reverse=True)

        return jsonify({
            "sessions":      sessions_list,
            "total":         len(sessions_list),
            "followUpsDue":  sum(
                1 for s in sessions_list if s['isFollowUpDue']
                and not s['isCompleted'])
        })

    except Exception as e:
        print(f"Error fetching coaching sessions: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 3: Update coaching session ──────────────────────────────────────────
@coaching_bp.route('/api/coaching/<session_id>', methods=['PATCH'])
def update_coaching_session(session_id):
    """
    Updates notes, follow-up date, or marks session as completed.

    Request body:
    { "notes": "Updated notes", "isCompleted": true }
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        db          = get_firestore_client()
        session_ref = db.collection('coaching_sessions')\
                        .document(session_id)
        session_doc = session_ref.get()

        if not session_doc.exists:
            return jsonify({"error": "Session not found"}), 404

        update_data = {}
        if 'notes' in data:
            update_data['notes'] = data['notes']
        if 'topic' in data:
            update_data['topic'] = data['topic']
        if 'isCompleted' in data:
            update_data['isCompleted'] = data['isCompleted']
        if 'followUpDate' in data and data['followUpDate']:
            try:
                fu_date = datetime.strptime(
                    data['followUpDate'], '%Y-%m-%d')\
                    .replace(tzinfo=timezone.utc)
                update_data['followUpDate'] = fu_date
            except ValueError:
                pass

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        session_ref.update(update_data)
        return jsonify({
            "message":   "Session updated successfully",
            "sessionId": session_id
        })

    except Exception as e:
        print(f"Error updating coaching session: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 4: Delete coaching session ──────────────────────────────────────────
@coaching_bp.route('/api/coaching/<session_id>', methods=['DELETE'])
def delete_coaching_session(session_id):
    """Deletes a coaching session. M1/M2 only."""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    if session['role'] not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Access denied"}), 403

    try:
        db  = get_firestore_client()
        ref = db.collection('coaching_sessions').document(session_id)
        if not ref.get().exists:
            return jsonify({"error": "Session not found"}), 404
        ref.delete()
        return jsonify({"message": "Session deleted successfully"})

    except Exception as e:
        print(f"Error deleting coaching session: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 5: Get coaching stats for M1 dashboard ──────────────────────────────
@coaching_bp.route('/api/coaching/stats', methods=['GET'])
def get_coaching_stats():
    """
    Returns coaching statistics for the current M1 manager.
    Shows sessions per specialist and upcoming follow-ups.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    uid  = session['uid']
    role = session['role']

    if role not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Access denied"}), 403

    try:
        db           = get_firestore_client()
        now          = datetime.now(timezone.utc)

        if role == 'm1_manager':
            sessions_ref = db.collection('coaching_sessions')\
                             .where('coachUid', '==', uid).get()
        else:
            sessions_ref = db.collection('coaching_sessions').get()

        total          = 0
        completed      = 0
        follow_ups_due = 0
        per_specialist = {}

        for doc in sessions_ref:
            s = doc.to_dict()
            total += 1
            if s.get('isCompleted'):
                completed += 1

            follow_up = s.get('followUpDate')
            if follow_up and hasattr(follow_up, 'replace'):
                fu_utc = follow_up.replace(tzinfo=timezone.utc)
                if fu_utc <= now and not s.get('isCompleted'):
                    follow_ups_due += 1

            sp_uid  = s.get('specialistUid', '')
            sp_name = s.get('specialistName', 'Unknown')
            if sp_uid not in per_specialist:
                per_specialist[sp_uid] = {
                    "name": sp_name, "count": 0}
            per_specialist[sp_uid]['count'] += 1

        return jsonify({
            "total":         total,
            "completed":     completed,
            "pending":       total - completed,
            "followUpsDue":  follow_ups_due,
            "perSpecialist": list(per_specialist.values())
        })

    except Exception as e:
        print(f"Error fetching coaching stats: {e}")
        return jsonify({"error": str(e)}), 500