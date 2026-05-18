"""
reviews.py — Manager Review Tracker API Routes
M2 Manager schedules and tracks review meetings with M1 Managers.
Includes agenda, notes, action items, and completion tracking.
"""

from flask import Blueprint, request, jsonify, session
from firebase_config import get_firestore_client
from firebase_admin import firestore
import uuid
from datetime import datetime, timezone

reviews_bp = Blueprint('reviews', __name__)


def require_auth():
    if 'uid' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    return None


# ── ROUTE 1: Create a manager review ──────────────────────────────────────────
@reviews_bp.route('/api/reviews', methods=['POST'])
def create_review():
    """
    M2 schedules a review meeting with an M1 Manager.

    Request body:
    {
        "m1ManagerUid":  "m1-uid-here",
        "scheduledDate": "2026-05-10",
        "agenda":        "Q2 pipeline review and team performance"
    }
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    if session['role'] != 'm2_manager':
        return jsonify({
            "error": "Only M2 Managers can schedule reviews"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    m1_uid         = data.get('m1ManagerUid', '').strip()
    scheduled_str  = data.get('scheduledDate', '').strip()
    agenda         = data.get('agenda', '').strip()

    if not m1_uid:
        return jsonify({"error": "M1 Manager UID is required"}), 400
    if not scheduled_str:
        return jsonify({"error": "Scheduled date is required"}), 400

    try:
        scheduled_date = datetime.strptime(scheduled_str, '%Y-%m-%d')\
                                 .replace(tzinfo=timezone.utc)

        db = get_firestore_client()

        # Get M1 info
        m1_doc  = db.collection('users').document(m1_uid).get()
        if not m1_doc.exists:
            return jsonify({"error": "M1 Manager not found"}), 404

        m1_data = m1_doc.to_dict()
        m1_name = m1_data.get('displayName', m1_data.get('email', ''))

        # Get M2 info
        m2_doc  = db.collection('users').document(session['uid']).get()
        m2_name = m2_doc.to_dict().get(
            'displayName',
            m2_doc.to_dict().get('email', '')) if m2_doc.exists else ''

        review_id = str(uuid.uuid4())

        review = {
            "reviewId":        review_id,
            "m1ManagerUid":    m1_uid,
            "m1ManagerName":   m1_name,
            "m2ManagerUid":    session['uid'],
            "m2ManagerName":   m2_name,
            "scheduledDate":   scheduled_date,
            "agenda":          agenda,
            "notes":           "",
            "actionItems":     [],
            "isCompleted":     False,
            "completedAt":     None,
            "createdAt":       firestore.SERVER_TIMESTAMP,
        }

        db.collection('manager_reviews').document(review_id).set(review)

        return jsonify({
            "message":  "Review scheduled successfully",
            "reviewId": review_id,
            "review": {
                "reviewId":      review_id,
                "m1ManagerName": m1_name,
                "scheduledDate": scheduled_str,
                "agenda":        agenda,
                "isCompleted":   False,
            }
        }), 201

    except ValueError as e:
        return jsonify({"error": f"Invalid date format: {e}"}), 400
    except Exception as e:
        print(f"Error creating review: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 2: Get manager reviews ──────────────────────────────────────────────
@reviews_bp.route('/api/reviews', methods=['GET'])
def get_reviews():
    """
    Returns reviews based on role:
    - M2: all reviews they scheduled
    - M1: reviews where they are the M1

    Query params:
    - ?completed=true/false
    - ?upcoming=true → only future scheduled dates
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    uid       = session['uid']
    role      = session['role']
    completed = request.args.get('completed', '')
    upcoming  = request.args.get('upcoming', '').lower() == 'true'

    try:
        db  = get_firestore_client()
        now = datetime.now(timezone.utc)

        if role == 'm2_manager':
            reviews_ref = db.collection('manager_reviews')\
                            .where('m2ManagerUid', '==', uid).get()
        elif role == 'm1_manager':
            reviews_ref = db.collection('manager_reviews')\
                            .where('m1ManagerUid', '==', uid).get()
        else:
            return jsonify({"error": "Access denied"}), 403

        reviews_list = []

        for doc in reviews_ref:
            r = doc.to_dict()

            # Filter by completed status
            if completed == 'true' and not r.get('isCompleted'):
                continue
            if completed == 'false' and r.get('isCompleted'):
                continue

            # Format dates
            sched = r.get('scheduledDate')
            if hasattr(sched, 'strftime'):
                sched_str     = sched.strftime('%d %b %Y')
                sched_iso     = sched.strftime('%Y-%m-%d')
                is_upcoming   = sched.replace(tzinfo=timezone.utc) >= now
            else:
                sched_str   = str(sched)[:10] if sched else ''
                sched_iso   = sched_str
                is_upcoming = False

            if upcoming and not is_upcoming:
                continue

            completed_at = r.get('completedAt')
            completed_str = ''
            if completed_at and hasattr(completed_at, 'strftime'):
                completed_str = completed_at.strftime('%d %b %Y')

            reviews_list.append({
                "reviewId":       r.get('reviewId'),
                "m1ManagerUid":   r.get('m1ManagerUid'),
                "m1ManagerName":  r.get('m1ManagerName', ''),
                "m2ManagerUid":   r.get('m2ManagerUid'),
                "m2ManagerName":  r.get('m2ManagerName', ''),
                "scheduledDate":  sched_str,
                "scheduledIso":   sched_iso,
                "agenda":         r.get('agenda', ''),
                "notes":          r.get('notes', ''),
                "actionItems":    r.get('actionItems', []),
                "isCompleted":    r.get('isCompleted', False),
                "completedAt":    completed_str,
                "isUpcoming":     is_upcoming,
            })

        # Sort: upcoming first then newest
        reviews_list.sort(
            key=lambda x: (x['isCompleted'], x['scheduledIso']),
            reverse=False
        )

        upcoming_count = sum(
            1 for r in reviews_list
            if r['isUpcoming'] and not r['isCompleted'])

        return jsonify({
            "reviews":       reviews_list,
            "total":         len(reviews_list),
            "upcomingCount": upcoming_count,
            "completedCount": sum(
                1 for r in reviews_list if r['isCompleted'])
        })

    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 3: Update a review ───────────────────────────────────────────────────
@reviews_bp.route('/api/reviews/<review_id>', methods=['PATCH'])
def update_review(review_id):
    """
    Updates review agenda, notes, action items or marks as completed.

    Request body:
    {
        "agenda":      "Updated agenda",
        "notes":       "Discussion notes from the meeting",
        "actionItems": ["Action 1", "Action 2"],
        "isCompleted": true
    }
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    if session['role'] not in ['m2_manager', 'm1_manager']:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        db         = get_firestore_client()
        review_ref = db.collection('manager_reviews').document(review_id)
        review_doc = review_ref.get()

        if not review_doc.exists:
            return jsonify({"error": "Review not found"}), 404

        update_data = {}

        if 'agenda' in data:
            update_data['agenda'] = data['agenda']
        if 'notes' in data:
            update_data['notes'] = data['notes']
        if 'actionItems' in data:
            if not isinstance(data['actionItems'], list):
                return jsonify({
                    "error": "actionItems must be an array"}), 400
            update_data['actionItems'] = data['actionItems']
        if 'isCompleted' in data:
            update_data['isCompleted'] = data['isCompleted']
            if data['isCompleted']:
                update_data['completedAt'] = firestore.SERVER_TIMESTAMP
        if 'scheduledDate' in data and data['scheduledDate']:
            try:
                new_date = datetime.strptime(
                    data['scheduledDate'], '%Y-%m-%d')\
                    .replace(tzinfo=timezone.utc)
                update_data['scheduledDate'] = new_date
            except ValueError:
                pass

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        review_ref.update(update_data)

        return jsonify({
            "message":  "Review updated successfully",
            "reviewId": review_id
        })

    except Exception as e:
        print(f"Error updating review: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 4: Delete a review ───────────────────────────────────────────────────
@reviews_bp.route('/api/reviews/<review_id>', methods=['DELETE'])
def delete_review(review_id):
    """Deletes a manager review. M2 only."""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    if session['role'] != 'm2_manager':
        return jsonify({"error": "Only M2 can delete reviews"}), 403

    try:
        db  = get_firestore_client()
        ref = db.collection('manager_reviews').document(review_id)
        if not ref.get().exists:
            return jsonify({"error": "Review not found"}), 404
        ref.delete()
        return jsonify({"message": "Review deleted successfully"})

    except Exception as e:
        print(f"Error deleting review: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 5: Get M1 managers list for M2 (to assign reviews) ──────────────────
@reviews_bp.route('/api/reviews/m1-managers', methods=['GET'])
def get_m1_managers():
    """Returns all M1 Managers in the org for M2 to select from."""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    if session['role'] != 'm2_manager':
        return jsonify({"error": "Access denied"}), 403

    try:
        db        = get_firestore_client()
        users_ref = db.collection('users')\
                      .where('role', '==', 'm1_manager').get()

        managers = []
        for user in users_ref:
            u = user.to_dict()
            managers.append({
                "uid":         u.get('uid'),
                "displayName": u.get('displayName', u.get('email', '')),
                "email":       u.get('email', ''),
                "teamId":      u.get('teamId', ''),
            })

        return jsonify({"managers": managers, "total": len(managers)})

    except Exception as e:
        print(f"Error fetching M1 managers: {e}")
        return jsonify({"error": str(e)}), 500