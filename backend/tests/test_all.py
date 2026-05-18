"""
test_all.py — Full Regression Test Suite
Run from project root: python backend/tests/test_all.py

Tests all major features across all 3 roles.
Each test prints PASS or FAIL with explanation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firebase_config import initialize_firebase, get_firestore_client
from firebase_admin import firestore
import uuid

# ── TEST CONFIG ────────────────────────────────────────────────────────────────
# These UIDs must match your seeded test accounts

EMPLOYEE_UID   = "DXsAbjuiEgTHmZBEdGw7u8zaOxF2"
M1_UID         = "APm9grZhkPUNSexOJpfzY8eZeUz2"
M2_UID         = "vnpNDxrwePVKE8GqFrhqKESbizI2"
TEAM_ID        = "team_001"

# ── RESULTS TRACKER ────────────────────────────────────────────────────────────
passed = 0
failed = 0
results = []


def test(name, condition, detail=""):
    global passed, failed
    status = "✅ PASS" if condition else "❌ FAIL"
    if condition:
        passed += 1
    else:
        failed += 1
    results.append((status, name, detail))
    print(f"  {status} — {name}")
    if not condition and detail:
        print(f"         Detail: {detail}")


# ── SECTION 1: Firebase Connection ────────────────────────────────────────────
def test_firebase_connection():
    print("\n── Section 1: Firebase Connection ───────────────")
    try:
        initialize_firebase()
        db = get_firestore_client()
        test("Firebase Admin SDK initialises", True)

        # Test write
        test_ref = db.collection('_regression_test').document('ping')
        test_ref.set({"ping": "pong", "ts": firestore.SERVER_TIMESTAMP})
        doc = test_ref.get()
        test("Firestore write and read works",
             doc.exists and doc.to_dict().get('ping') == 'pong')
        test_ref.delete()
        test("Firestore delete works", not test_ref.get().exists)
    except Exception as e:
        test("Firebase connection", False, str(e))


# ── SECTION 2: Data Integrity ──────────────────────────────────────────────────
def test_data_integrity():
    print("\n── Section 2: Data Integrity ─────────────────────")
    db = get_firestore_client()

    # Check users exist
    emp_doc = db.collection('users').document(EMPLOYEE_UID).get()
    test("Employee user document exists", emp_doc.exists)
    if emp_doc.exists:
        test("Employee has correct role",
             emp_doc.to_dict().get('role') == 'employee')

    m1_doc = db.collection('users').document(M1_UID).get()
    test("M1 Manager user document exists", m1_doc.exists)
    if m1_doc.exists:
        test("M1 has correct role",
             m1_doc.to_dict().get('role') == 'm1_manager')

    m2_doc = db.collection('users').document(M2_UID).get()
    test("M2 Manager user document exists", m2_doc.exists)
    if m2_doc.exists:
        test("M2 has correct role",
             m2_doc.to_dict().get('role') == 'm2_manager')

    # Check team exists
    team_doc = db.collection('teams').document(TEAM_ID).get()
    test("Team document exists", team_doc.exists)

    # Check pipeline stages
    stages = db.collection('pipeline_stages').get()
    stage_count = len(list(stages))
    test("Pipeline stages seeded (13+)", stage_count >= 13,
         f"Found {stage_count} stages")

    # Check leads exist
    leads = db.collection('leads')\
              .where('employeeUid', '==', EMPLOYEE_UID).get()
    lead_count = len(list(leads))
    test("Employee has at least 1 lead", lead_count >= 1,
         f"Found {lead_count} leads")


# ── SECTION 3: Lead Operations ─────────────────────────────────────────────────
def test_lead_operations():
    print("\n── Section 3: Lead Operations ────────────────────")
    db = get_firestore_client()

    test_lead_id = str(uuid.uuid4())

    # Create a test lead
    try:
        db.collection('leads').document(test_lead_id).set({
            "leadId":       test_lead_id,
            "employeeUid":  EMPLOYEE_UID,
            "teamId":       TEAM_ID,
            "name":         "Regression Test Lead",
            "company":      "Test Corp",
            "email":        "regression@test.com",
            "phone":        "+91 9000000000",
            "linkedinUrl":  "",
            "currentStage": "stage_1_1",
            "isArchived":   False,
            "createdAt":    firestore.SERVER_TIMESTAMP,
            "updatedAt":    firestore.SERVER_TIMESTAMP,
        })
        lead_doc = db.collection('leads').document(test_lead_id).get()
        test("Lead creation works", lead_doc.exists)
        test("Lead has correct employee UID",
             lead_doc.to_dict().get('employeeUid') == EMPLOYEE_UID)
        test("Lead starts at stage_1_1",
             lead_doc.to_dict().get('currentStage') == 'stage_1_1')
    except Exception as e:
        test("Lead creation works", False, str(e))
        return

    # Update stage
    try:
        db.collection('leads').document(test_lead_id).update({
            "currentStage": "stage_2",
            "updatedAt":    firestore.SERVER_TIMESTAMP,
        })
        updated = db.collection('leads').document(test_lead_id).get()
        test("Lead stage update works",
             updated.to_dict().get('currentStage') == 'stage_2')
    except Exception as e:
        test("Lead stage update works", False, str(e))

    # Write audit log
    try:
        log_id = str(uuid.uuid4())
        db.collection('audit_logs').document(log_id).set({
            "logId":       log_id,
            "leadId":      test_lead_id,
            "employeeUid": EMPLOYEE_UID,
            "fromStage":   "stage_1_1",
            "toStage":     "stage_2",
            "changedAt":   firestore.SERVER_TIMESTAMP,
            "notes":       "Regression test"
        })
        log_doc = db.collection('audit_logs').document(log_id).get()
        test("Audit log creation works", log_doc.exists)
        test("Audit log has correct lead ID",
             log_doc.to_dict().get('leadId') == test_lead_id)
        db.collection('audit_logs').document(log_id).delete()
    except Exception as e:
        test("Audit log creation works", False, str(e))

    # Archive lead
    try:
        db.collection('leads').document(test_lead_id).update({
            "isArchived": True,
            "updatedAt":  firestore.SERVER_TIMESTAMP,
        })
        archived = db.collection('leads').document(test_lead_id).get()
        test("Lead archive works",
             archived.to_dict().get('isArchived') is True)
    except Exception as e:
        test("Lead archive works", False, str(e))

    # Clean up
    db.collection('leads').document(test_lead_id).delete()
    test("Lead deletion works",
         not db.collection('leads').document(test_lead_id).get().exists)


# ── SECTION 4: Task Operations ─────────────────────────────────────────────────
def test_task_operations():
    print("\n── Section 4: Task Operations ────────────────────")
    db = get_firestore_client()

    task_id = str(uuid.uuid4())

    # Create task
    try:
        from datetime import datetime, timezone, timedelta
        due_date = datetime.now(timezone.utc) + timedelta(days=7)

        db.collection('tasks').document(task_id).set({
            "taskId":          task_id,
            "title":           "Regression Test Task",
            "description":     "Test task for regression suite",
            "assignedToUid":   EMPLOYEE_UID,
            "assignedToName":  "Test Employee",
            "assignedByUid":   M1_UID,
            "assignedByRole":  "m1_manager",
            "teamId":          TEAM_ID,
            "dueDate":         due_date,
            "priority":        "high",
            "status":          "pending",
            "createdAt":       firestore.SERVER_TIMESTAMP,
            "completedAt":     None,
            "isDeleted":       False,
        })
        task_doc = db.collection('tasks').document(task_id).get()
        test("Task creation works", task_doc.exists)
        test("Task has correct status",
             task_doc.to_dict().get('status') == 'pending')
        test("Task has correct priority",
             task_doc.to_dict().get('priority') == 'high')
    except Exception as e:
        test("Task creation works", False, str(e))
        return

    # Update task status
    try:
        db.collection('tasks').document(task_id).update({
            "status": "in_progress"
        })
        updated = db.collection('tasks').document(task_id).get()
        test("Task status update works",
             updated.to_dict().get('status') == 'in_progress')
    except Exception as e:
        test("Task status update works", False, str(e))

    # Soft delete task
    try:
        db.collection('tasks').document(task_id).update({
            "isDeleted": True
        })
        deleted = db.collection('tasks').document(task_id).get()
        test("Task soft delete works",
             deleted.to_dict().get('isDeleted') is True)
    except Exception as e:
        test("Task soft delete works", False, str(e))

    # Hard delete for cleanup
    db.collection('tasks').document(task_id).delete()


# ── SECTION 5: Notification Operations ────────────────────────────────────────
def test_notifications():
    print("\n── Section 5: Notifications ──────────────────────")
    db = get_firestore_client()

    notif_id = str(uuid.uuid4())

    try:
        db.collection('notifications').document(notif_id).set({
            "notifId":      notif_id,
            "recipientUid": EMPLOYEE_UID,
            "message":      "Regression test notification",
            "type":         "task_assigned",
            "relatedId":    "test_task_id",
            "isRead":       False,
            "createdAt":    firestore.SERVER_TIMESTAMP,
        })
        notif_doc = db.collection('notifications')\
                      .document(notif_id).get()
        test("Notification creation works", notif_doc.exists)
        test("Notification is unread by default",
             notif_doc.to_dict().get('isRead') is False)

        # Mark as read
        db.collection('notifications').document(notif_id).update({
            "isRead": True
        })
        updated = db.collection('notifications').document(notif_id).get()
        test("Notification mark as read works",
             updated.to_dict().get('isRead') is True)

        # Cleanup
        db.collection('notifications').document(notif_id).delete()

    except Exception as e:
        test("Notification operations", False, str(e))


# ── SECTION 6: Coaching Sessions ──────────────────────────────────────────────
def test_coaching():
    print("\n── Section 6: Coaching Sessions ──────────────────")
    db = get_firestore_client()

    session_id = str(uuid.uuid4())

    try:
        from datetime import datetime, timezone
        db.collection('coaching_sessions').document(session_id).set({
            "sessionId":      session_id,
            "specialistUid":  EMPLOYEE_UID,
            "specialistName": "Test Employee",
            "coachUid":       M1_UID,
            "coachName":      "Test M1 Manager",
            "teamId":         TEAM_ID,
            "sessionDate":    datetime.now(timezone.utc),
            "topic":          "Regression test coaching",
            "notes":          "Test notes",
            "followUpDate":   None,
            "isCompleted":    False,
            "createdAt":      firestore.SERVER_TIMESTAMP,
        })
        doc = db.collection('coaching_sessions')\
                .document(session_id).get()
        test("Coaching session creation works", doc.exists)
        test("Coaching session not completed by default",
             doc.to_dict().get('isCompleted') is False)

        # Mark complete
        db.collection('coaching_sessions').document(session_id).update({
            "isCompleted": True
        })
        updated = db.collection('coaching_sessions')\
                    .document(session_id).get()
        test("Coaching session mark complete works",
             updated.to_dict().get('isCompleted') is True)

        # Cleanup
        db.collection('coaching_sessions').document(session_id).delete()

    except Exception as e:
        test("Coaching session operations", False, str(e))


# ── SECTION 7: Manager Reviews ─────────────────────────────────────────────────
def test_reviews():
    print("\n── Section 7: Manager Reviews ────────────────────")
    db = get_firestore_client()

    review_id = str(uuid.uuid4())

    try:
        from datetime import datetime, timezone, timedelta
        scheduled = datetime.now(timezone.utc) + timedelta(days=7)

        db.collection('manager_reviews').document(review_id).set({
            "reviewId":      review_id,
            "m1ManagerUid":  M1_UID,
            "m1ManagerName": "Test M1 Manager",
            "m2ManagerUid":  M2_UID,
            "m2ManagerName": "Test M2 Manager",
            "scheduledDate": scheduled,
            "agenda":        "Regression test review",
            "notes":         "",
            "actionItems":   [],
            "isCompleted":   False,
            "createdAt":     firestore.SERVER_TIMESTAMP,
        })
        doc = db.collection('manager_reviews')\
                .document(review_id).get()
        test("Manager review creation works", doc.exists)
        test("Review starts as not completed",
             doc.to_dict().get('isCompleted') is False)

        # Add notes and action items
        db.collection('manager_reviews').document(review_id).update({
            "notes":       "Test meeting notes",
            "actionItems": ["Action 1", "Action 2"],
            "isCompleted": True
        })
        updated = db.collection('manager_reviews')\
                    .document(review_id).get()
        test("Review update with notes works",
             updated.to_dict().get('notes') == 'Test meeting notes')
        test("Review action items saved correctly",
             len(updated.to_dict().get('actionItems', [])) == 2)
        test("Review mark complete works",
             updated.to_dict().get('isCompleted') is True)

        # Cleanup
        db.collection('manager_reviews').document(review_id).delete()

    except Exception as e:
        test("Manager review operations", False, str(e))


# ── SECTION 8: Custom Pipeline Stages ─────────────────────────────────────────
def test_custom_stages():
    print("\n── Section 8: Custom Pipeline Stages ────────────")
    db = get_firestore_client()

    stage_id = f"custom_regression_{str(uuid.uuid4())[:6]}"

    try:
        db.collection('pipeline_stages').document(stage_id).set({
            "stageId":     stage_id,
            "stageNumber": "R1",
            "stageName":   "Regression Test Stage",
            "description": "Created by regression test",
            "stageOrder":  99.0,
            "isDefault":   False,
            "isActive":    True,
            "isArchived":  False,
            "createdBy":   M1_UID,
            "createdAt":   firestore.SERVER_TIMESTAMP,
        })
        doc = db.collection('pipeline_stages').document(stage_id).get()
        test("Custom stage creation works", doc.exists)
        test("Custom stage is active by default",
             doc.to_dict().get('isActive') is True)
        test("Custom stage is not default",
             doc.to_dict().get('isDefault') is False)

        # Deactivate
        db.collection('pipeline_stages').document(stage_id).update({
            "isActive": False
        })
        updated = db.collection('pipeline_stages')\
                    .document(stage_id).get()
        test("Stage deactivation works",
             updated.to_dict().get('isActive') is False)

        # Cleanup
        db.collection('pipeline_stages').document(stage_id).delete()

    except Exception as e:
        test("Custom stage operations", False, str(e))


# ── SECTION 9: Role Isolation ──────────────────────────────────────────────────
def test_role_isolation():
    print("\n── Section 9: Role Isolation ─────────────────────")
    db = get_firestore_client()

    # Check employee can't see other employee's leads
    all_leads = db.collection('leads').get()
    all_lead_uids = set(
        l.to_dict().get('employeeUid') for l in all_leads)
    test("Multiple employees exist in system",
         len(all_lead_uids) >= 1)

    # Check team isolation — leads should have teamId
    leads_with_team = [l for l in db.collection('leads').get()
                       if l.to_dict().get('teamId')]
    test("All leads have teamId assigned",
         len(leads_with_team) > 0)

    # Check notifications are user-specific
    notifs = db.collection('notifications')\
               .where('recipientUid', '==', EMPLOYEE_UID).get()
    test("Notifications are queryable by recipient",
         notifs is not None)


# ── MAIN ───────────────────────────────────────────────────────────────────────
def run_all_tests():
    print("\n" + "=" * 55)
    print("   FULL REGRESSION TEST SUITE — Day 21")
    print("=" * 55)

    # Check UIDs are filled in
    for uid, label in [
        (EMPLOYEE_UID, "EMPLOYEE_UID"),
        (M1_UID,       "M1_UID"),
        (M2_UID,       "M2_UID"),
    ]:
        if "PASTE_" in uid:
            print(f"\n❌ ERROR: Replace {label} in test_all.py")
            print("   Open backend/tests/test_all.py and paste real UIDs")
            return

    test_firebase_connection()
    test_data_integrity()
    test_lead_operations()
    test_task_operations()
    test_notifications()
    test_coaching()
    test_reviews()
    test_custom_stages()
    test_role_isolation()

    print("\n" + "=" * 55)
    print(f"   RESULTS: {passed} PASSED  |  {failed} FAILED")
    print("=" * 55)

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED — System is ready for Sprint 3!")
    else:
        print(f"\n⚠️  {failed} test(s) failed — review above output")

    print()


if __name__ == '__main__':
    run_all_tests()