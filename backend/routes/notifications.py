"""
notifications.py — Notifications API Routes
Handles: fetch notifications, mark as read, mark all as read
"""

from flask import Blueprint, jsonify, session
from firebase_config import get_firestore_client

notifications_bp = Blueprint('notifications', __name__)


# ── HELPER ────────────────────────────────────────────────────────────────────
def require_auth():
    if 'uid' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    return None


# ── ROUTE 1: Get notifications for current user ────────────────────────────────
@notifications_bp.route('/api/notifications', methods=['GET'])
def get_notifications():
    """
    Returns all notifications for the currently logged-in user.
    Sorted by newest first.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    uid = session['uid']

    try:
        db   = get_firestore_client()
        refs = db.collection('notifications')\
                 .where('recipientUid', '==', uid)\
                 .get()

        notifs = []
        for doc in refs:
            n = doc.to_dict()

            created_at = n.get('createdAt')
            if hasattr(created_at, 'strftime'):
                created_at_str = created_at.strftime('%d %b %Y %H:%M')
            else:
                created_at_str = 'Just now'

            notifs.append({
                "notifId":    n.get('notifId'),
                "message":    n.get('message'),
                "type":       n.get('type'),
                "relatedId":  n.get('relatedId'),
                "isRead":     n.get('isRead', False),
                "createdAt":  created_at_str,
            })

        # Sort newest first (by notifId as proxy — UUIDs are time-ordered)
        notifs.sort(key=lambda x: x['notifId'], reverse=True)

        unread_count = sum(1 for n in notifs if not n['isRead'])

        return jsonify({
            "notifications": notifs,
            "unreadCount":   unread_count,
            "total":         len(notifs)
        })

    except Exception as e:
        print(f"Error fetching notifications: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 2: Mark a single notification as read ────────────────────────────────
@notifications_bp.route('/api/notifications/<notif_id>/read',
                        methods=['PUT'])
def mark_as_read(notif_id):
    """
    Marks a single notification as read.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        db       = get_firestore_client()
        notif_ref = db.collection('notifications').document(notif_id)
        notif_doc = notif_ref.get()

        if not notif_doc.exists:
            return jsonify({"error": "Notification not found"}), 404

        # Security: user can only mark their own notifications as read
        if notif_doc.to_dict().get('recipientUid') != session['uid']:
            return jsonify({"error": "Access denied"}), 403

        notif_ref.update({"isRead": True})
        return jsonify({"message": "Notification marked as read"})

    except Exception as e:
        print(f"Error marking notification: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 3: Mark ALL notifications as read ────────────────────────────────────
@notifications_bp.route('/api/notifications/read-all', methods=['PUT'])
def mark_all_as_read():
    """
    Marks all unread notifications for the current user as read.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    uid = session['uid']

    try:
        db   = get_firestore_client()
        refs = db.collection('notifications')\
                 .where('recipientUid', '==', uid)\
                 .where('isRead', '==', False)\
                 .get()

        count = 0
        for doc in refs:
            doc.reference.update({"isRead": True})
            count += 1

        return jsonify({
            "message": f"Marked {count} notifications as read",
            "count":   count
        })

    except Exception as e:
        print(f"Error marking all notifications: {e}")
        return jsonify({"error": str(e)}), 500
        