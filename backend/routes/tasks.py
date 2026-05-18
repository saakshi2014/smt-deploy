"""
tasks.py — Task Management API Routes
Handles: create task, fetch tasks, update status, delete task,
         overdue flagging
"""

from flask import Blueprint, request, jsonify, session
from firebase_config import get_firestore_client
from firebase_admin import firestore
import uuid
from datetime import datetime, timezone

tasks_bp = Blueprint('tasks', __name__)


# ── HELPER: Check authentication ───────────────────────────────────────────────
def require_auth():
    if 'uid' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    return None


# ── HELPER: Write notification ─────────────────────────────────────────────────
def write_notification(db, recipient_uid, message, notif_type, related_id=None):
    """
    Writes a notification document to Firestore.
    Called internally whenever a task is assigned, completed or overdue.
    """
    try:
        notif_id = str(uuid.uuid4())
        db.collection('notifications').document(notif_id).set({
            "notifId":      notif_id,
            "recipientUid": recipient_uid,
            "message":      message,
            "type":         notif_type,
            "relatedId":    related_id,
            "isRead":       False,
            "createdAt":    firestore.SERVER_TIMESTAMP
        })
    except Exception as e:
        print(f"Failed to write notification: {e}")


# ── ROUTE 1: Create a task ─────────────────────────────────────────────────────
@tasks_bp.route('/api/tasks', methods=['POST'])
def create_task():
    """
    Creates a new task and assigns it to an employee.

    M1 Manager: can assign to own team members only
    M2 Manager: can assign to any employee in any team

    Request body:
    {
        "title":            "Follow up with leads",
        "description":      "Call all stage 4 leads this week",
        "assignedToUid":    "employee-uid-here",
        "dueDate":          "2026-04-30",
        "priority":         "high"
    }
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    role = session['role']
    if role not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Only managers can create tasks"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    title          = data.get('title', '').strip()
    assigned_to    = data.get('assignedToUid', '').strip()
    due_date_str   = data.get('dueDate', '').strip()
    priority       = data.get('priority', 'medium').lower()
    description    = data.get('description', '').strip()

    # Validate required fields
    if not title:
        return jsonify({"error": "Task title is required"}), 400
    if not assigned_to:
        return jsonify({"error": "Assigned employee is required"}), 400
    if not due_date_str:
        return jsonify({"error": "Due date is required"}), 400
    if priority not in ['low', 'medium', 'high']:
        return jsonify({"error": "Priority must be low, medium or high"}), 400

    # Parse due date
    try:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        due_date = due_date.replace(tzinfo=timezone.utc)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    try:
        db      = get_firestore_client()
        uid     = session['uid']

        # Get assigner's teamId
        user_doc  = db.collection('users').document(uid).get()
        team_id   = user_doc.to_dict().get('teamId', 'team_001')

        # Verify assigned employee exists
        assignee_doc = db.collection('users').document(assigned_to).get()
        if not assignee_doc.exists:
            return jsonify({"error": "Assigned employee not found"}), 404

        assignee_data = assignee_doc.to_dict()
        assignee_name = assignee_data.get('displayName',
                        assignee_data.get('email', 'Unknown'))

        task_id = str(uuid.uuid4())

        task = {
            "taskId":          task_id,
            "title":           title,
            "description":     description,
            "assignedToUid":   assigned_to,
            "assignedToName":  assignee_name,
            "assignedByUid":   uid,
            "assignedByRole":  role,
            "teamId":          team_id,
            "dueDate":         due_date,
            "priority":        priority,
            "status":          "pending",
            "createdAt":       firestore.SERVER_TIMESTAMP,
            "completedAt":     None,
            "isDeleted":       False
        }

        db.collection('tasks').document(task_id).set(task)

        # Write notification to assignee
        assigner_doc  = db.collection('users').document(uid).get()
        assigner_name = assigner_doc.to_dict().get(
            'displayName', assigner_doc.to_dict().get('email', 'Manager'))

        write_notification(
            db,
            recipient_uid = assigned_to,
            message       = f"New task assigned by {assigner_name}: {title}",
            notif_type    = "task_assigned",
            related_id    = task_id
        )

        return jsonify({
            "message": "Task created successfully",
            "taskId":  task_id,
            "task": {
                "taskId":         task_id,
                "title":          title,
                "description":    description,
                "assignedToName": assignee_name,
                "dueDate":        due_date_str,
                "priority":       priority,
                "status":         "pending"
            }
        }), 201

    except Exception as e:
        print(f"Error creating task: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 2: Get tasks ─────────────────────────────────────────────────────────
@tasks_bp.route('/api/tasks', methods=['GET'])
def get_tasks():
    """
    Returns tasks based on user role:
    - Employee:    only tasks assigned to them
    - M1 Manager:  all tasks they assigned
    - M2 Manager:  all tasks in the organisation

    Optional query params:
    - ?status=pending|in_progress|completed|overdue
    - ?priority=low|medium|high
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    uid    = session['uid']
    role   = session['role']
    status = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')

    try:
        db = get_firestore_client()

        # First run overdue check
        flag_overdue_tasks(db)

        # Fetch tasks based on role
        if role == 'employee':
            tasks_ref = db.collection('tasks')\
                          .where('assignedToUid', '==', uid)\
                          .where('isDeleted', '==', False)\
                          .get()
        elif role == 'm1_manager':
            tasks_ref = db.collection('tasks')\
                          .where('assignedByUid', '==', uid)\
                          .where('isDeleted', '==', False)\
                          .get()
        else:
            # M2 sees all tasks
            tasks_ref = db.collection('tasks')\
                          .where('isDeleted', '==', False)\
                          .get()

        tasks_list = []
        for task_doc in tasks_ref:
            task = task_doc.to_dict()

            # Apply status filter if provided
            if status and task.get('status') != status:
                continue

            # Apply priority filter if provided
            if priority_filter and task.get('priority') != priority_filter:
                continue

            # Format due date
            due_date = task.get('dueDate')
            if hasattr(due_date, 'strftime'):
                due_date_str = due_date.strftime('%Y-%m-%d')
                due_date_display = due_date.strftime('%d %b %Y')
            else:
                due_date_str     = str(due_date)[:10] if due_date else ''
                due_date_display = due_date_str

            # Check if overdue for display
            is_overdue = task.get('status') == 'overdue'

            tasks_list.append({
                "taskId":         task.get('taskId'),
                "title":          task.get('title'),
                "description":    task.get('description', ''),
                "assignedToUid":  task.get('assignedToUid'),
                "assignedToName": task.get('assignedToName', ''),
                "assignedByUid":  task.get('assignedByUid'),
                "assignedByRole": task.get('assignedByRole', ''),
                "teamId":         task.get('teamId'),
                "dueDate":        due_date_str,
                "dueDateDisplay": due_date_display,
                "priority":       task.get('priority', 'medium'),
                "status":         task.get('status', 'pending'),
                "isOverdue":      is_overdue,
                "completedAt":    str(task.get('completedAt', '')) or None,
            })

        # Sort — overdue first, then by due date
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        status_order   = {'overdue': 0, 'pending': 1,
                          'in_progress': 2, 'completed': 3}

        tasks_list.sort(key=lambda x: (
            status_order.get(x['status'], 9),
            priority_order.get(x['priority'], 9),
            x['dueDate']
        ))

        # Count by status
        counts = {
            "pending":     sum(1 for t in tasks_list if t['status'] == 'pending'),
            "in_progress": sum(1 for t in tasks_list if t['status'] == 'in_progress'),
            "completed":   sum(1 for t in tasks_list if t['status'] == 'completed'),
            "overdue":     sum(1 for t in tasks_list if t['status'] == 'overdue'),
            "total":       len(tasks_list)
        }

        return jsonify({
            "tasks":  tasks_list,
            "counts": counts
        })

    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 3: Update task status ────────────────────────────────────────────────
@tasks_bp.route('/api/tasks/<task_id>', methods=['PATCH'])
def update_task(task_id):
    """
    Updates a task's status or details.

    Employee:   can update status only (their own tasks)
    M1/M2:     can update any field

    Request body:
    { "status": "in_progress" }
    or
    { "status": "completed" }
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    uid  = session['uid']
    role = session['role']

    try:
        db       = get_firestore_client()
        task_ref = db.collection('tasks').document(task_id)
        task_doc = task_ref.get()

        if not task_doc.exists:
            return jsonify({"error": "Task not found"}), 404

        task_data = task_doc.to_dict()

        # Employee can only update their own tasks
        if role == 'employee' and task_data.get('assignedToUid') != uid:
            return jsonify({"error": "You can only update your own tasks"}), 403

        new_status = data.get('status')
        update_data = {}

        # Handle status update
        if new_status:
            valid_statuses = ['pending', 'in_progress', 'completed', 'overdue']
            if new_status not in valid_statuses:
                return jsonify({"error": f"Invalid status: {new_status}"}), 400

            update_data['status'] = new_status

            # If completed, record completion time
            if new_status == 'completed':
                update_data['completedAt'] = firestore.SERVER_TIMESTAMP

                # Notify the assigner (M1) that task is complete
                assigner_uid  = task_data.get('assignedByUid')
                assignee_name = task_data.get('assignedToName', 'Employee')
                task_title    = task_data.get('title', 'Task')

                if assigner_uid and assigner_uid != uid:
                    write_notification(
                        db,
                        recipient_uid = assigner_uid,
                        message       = f"{assignee_name} completed task: {task_title}",
                        notif_type    = "task_completed",
                        related_id    = task_id
                    )

        # M1/M2 can also update title, description, priority, dueDate
        if role in ['m1_manager', 'm2_manager']:
            allowed = ['title', 'description', 'priority']
            for field in allowed:
                if field in data:
                    update_data[field] = data[field]

            if 'dueDate' in data:
                try:
                    due_date = datetime.strptime(data['dueDate'], '%Y-%m-%d')
                    update_data['dueDate'] = due_date.replace(
                        tzinfo=timezone.utc)
                except ValueError:
                    pass

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        task_ref.update(update_data)

        return jsonify({
            "message": "Task updated successfully",
            "taskId":  task_id,
            "updates": {k: v for k, v in update_data.items()
                       if k != 'completedAt'}
        })

    except Exception as e:
        print(f"Error updating task: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 4: Delete a task ─────────────────────────────────────────────────────
@tasks_bp.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """
    Soft deletes a task (sets isDeleted = True).
    Only M1 and M2 Managers can delete tasks.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    role = session['role']
    if role not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Only managers can delete tasks"}), 403

    try:
        db       = get_firestore_client()
        task_ref = db.collection('tasks').document(task_id)
        task_doc = task_ref.get()

        if not task_doc.exists:
            return jsonify({"error": "Task not found"}), 404

        task_ref.update({
            "isDeleted": True,
            "deletedAt": firestore.SERVER_TIMESTAMP
        })

        return jsonify({"message": "Task deleted successfully"})

    except Exception as e:
        print(f"Error deleting task: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 5: Get single task ───────────────────────────────────────────────────
@tasks_bp.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """
    Returns full details of a single task.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        db       = get_firestore_client()
        task_doc = db.collection('tasks').document(task_id).get()

        if not task_doc.exists:
            return jsonify({"error": "Task not found"}), 404

        task = task_doc.to_dict()

        due_date = task.get('dueDate')
        if hasattr(due_date, 'strftime'):
            due_date_str = due_date.strftime('%Y-%m-%d')
        else:
            due_date_str = str(due_date)[:10] if due_date else ''

        return jsonify({
            "taskId":         task.get('taskId'),
            "title":          task.get('title'),
            "description":    task.get('description', ''),
            "assignedToUid":  task.get('assignedToUid'),
            "assignedToName": task.get('assignedToName', ''),
            "assignedByUid":  task.get('assignedByUid'),
            "teamId":         task.get('teamId'),
            "dueDate":        due_date_str,
            "priority":       task.get('priority', 'medium'),
            "status":         task.get('status', 'pending'),
            "completedAt":    str(task.get('completedAt', '')) or None,
        })

    except Exception as e:
        print(f"Error fetching task: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 6: Get team members for task assignment ──────────────────────────────
@tasks_bp.route('/api/tasks/assignees', methods=['GET'])
def get_assignees():
    """
    Returns list of employees that the current manager can assign tasks to.
    M1: returns their team members only
    M2: returns all employees in the organisation
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
            # Get M1's team members
            user_doc = db.collection('users').document(uid).get()
            team_id  = user_doc.to_dict().get('teamId', 'team_001')

            members_ref = db.collection('teams').document(team_id)\
                            .collection('members').get()
            assignees = []
            for member in members_ref:
                m = member.to_dict()
                if m.get('uid') != uid:  # Exclude M1 themselves
                    assignees.append({
                        "uid":         m.get('uid'),
                        "displayName": m.get('displayName',
                                       m.get('email', '')),
                        "email":       m.get('email', ''),
                        "role":        m.get('role', 'employee')
                    })
        else:
            # M2 gets all employees
            users_ref = db.collection('users')\
                          .where('role', '==', 'employee').get()
            assignees = []
            for user in users_ref:
                u = user.to_dict()
                assignees.append({
                    "uid":         u.get('uid'),
                    "displayName": u.get('displayName',
                                   u.get('email', '')),
                    "email":       u.get('email', ''),
                    "teamId":      u.get('teamId', '')
                })

        return jsonify({"assignees": assignees, "total": len(assignees)})

    except Exception as e:
        print(f"Error fetching assignees: {e}")
        return jsonify({"error": str(e)}), 500


# ── HELPER: Flag overdue tasks ─────────────────────────────────────────────────
def flag_overdue_tasks(db):
    """
    Checks all pending/in_progress tasks and marks them overdue
    if their due date has passed.
    Called automatically on every GET /api/tasks request.
    """
    try:
        now = datetime.now(timezone.utc)

        # Get all non-completed, non-deleted tasks
        tasks_ref = db.collection('tasks')\
                      .where('isDeleted', '==', False)\
                      .where('status', 'in', ['pending', 'in_progress'])\
                      .get()

        for task_doc in tasks_ref:
            task     = task_doc.to_dict()
            due_date = task.get('dueDate')

            if due_date and hasattr(due_date, 'replace'):
                if due_date.replace(tzinfo=timezone.utc) < now:
                    task_doc.reference.update({"status": "overdue"})

                    # Notify M1 that their task is overdue
                    assigner_uid = task.get('assignedByUid')
                    task_title   = task.get('title', 'Task')
                    assignee_name = task.get('assignedToName', 'Employee')

                    if assigner_uid:
                        write_notification(
                            db,
                            recipient_uid = assigner_uid,
                            message       = f"Task overdue: {task_title} "
                                          f"assigned to {assignee_name}",
                            notif_type    = "task_overdue",
                            related_id    = task.get('taskId')
                        )

    except Exception as e:
        print(f"Overdue check error: {e}")


# ── ROUTE 7: Get task stats for M2 health panel ────────────────────────────────
@tasks_bp.route('/api/tasks/stats', methods=['GET'])
def get_task_stats():
    """
    Returns task health statistics for M2 Manager.
    Shows pending, in_progress, completed, overdue counts
    broken down by team.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    if session['role'] != 'm2_manager':
        return jsonify({"error": "Access denied"}), 403

    try:
        db = get_firestore_client()

        # Flag overdue first
        flag_overdue_tasks(db)

        # Get all tasks
        tasks_ref = db.collection('tasks')\
                      .where('isDeleted', '==', False).get()

        # Get team names
        teams_ref = db.collection('teams').get()
        teams_map = {t.to_dict()['teamId']: t.to_dict()['teamName']
                     for t in teams_ref}

        # Org-wide counts
        org_counts = {
            "pending": 0, "in_progress": 0,
            "completed": 0, "overdue": 0, "total": 0
        }

        # Per-team counts
        team_counts = {}

        for task_doc in tasks_ref:
            task    = task_doc.to_dict()
            status  = task.get('status', 'pending')
            team_id = task.get('teamId', 'unknown')

            org_counts['total'] += 1
            if status in org_counts:
                org_counts[status] += 1

            if team_id not in team_counts:
                team_counts[team_id] = {
                    "teamId":    team_id,
                    "teamName":  teams_map.get(team_id, 'Unknown Team'),
                    "pending":   0, "in_progress": 0,
                    "completed": 0, "overdue": 0, "total": 0
                }
            team_counts[team_id]['total'] += 1
            if status in team_counts[team_id]:
                team_counts[team_id][status] += 1

        return jsonify({
            "orgCounts":  org_counts,
            "teamCounts": list(team_counts.values())
        })

    except Exception as e:
        print(f"Error fetching task stats: {e}")
        return jsonify({"error": str(e)}), 500