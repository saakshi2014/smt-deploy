"""
seed_teams.py — Seeds a test team into Firestore
Run this ONCE from the project root:
    python backend/seed_teams.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from firebase_config import initialize_firebase, get_firestore_client
from firebase_admin import firestore

# ── PASTE YOUR UIDs HERE ───────────────────────────────────────────────────────
# These are the same UIDs you used in seed_users.py

EMPLOYEE_UID   = "DXsAbjuiEgTHmZBEdGw7u8zaOxF2"
M1_MANAGER_UID = "APm9grZhkPUNSexOJpfzY8eZeUz2"
M2_MANAGER_UID = "vnpNDxrwePVKE8GqFrhqKESbizI2"

# ──────────────────────────────────────────────────────────────────────────────


def seed_teams():
    print("\n" + "=" * 52)
    print("   Seeding Teams into Firestore")
    print("=" * 52)

    # Check UIDs are filled in
    for uid, label in [
        (EMPLOYEE_UID,   "EMPLOYEE_UID"),
        (M1_MANAGER_UID, "M1_MANAGER_UID"),
        (M2_MANAGER_UID, "M2_MANAGER_UID")
    ]:
        if "PASTE_" in uid:
            print(f"\n❌ ERROR: Replace {label} with the real UID")
            print("   Open seed_teams.py and paste the real UIDs")
            return

    initialize_firebase()
    db = get_firestore_client()

    # Check if team already exists
    existing = db.collection('teams').document('team_001').get()
    if existing.exists:
        print("\n⚠️  Team team_001 already exists. Skipping.")
        print("=" * 52)
        return

    # ── Create the test team ───────────────────────────────────────────────────
    team = {
        "teamId":       "team_001",
        "teamName":     "Sales Team Alpha",
        "m1ManagerUid": M1_MANAGER_UID,
        "m2ManagerUid": M2_MANAGER_UID,
        "isActive":     True,
        "createdAt":    firestore.SERVER_TIMESTAMP,
        "createdBy":    M2_MANAGER_UID
    }

    db.collection('teams').document('team_001').set(team)
    print(f"✅ Created team: {team['teamName']} (ID: team_001)")

    # ── Add members subcollection ──────────────────────────────────────────────
    # Each member is a document in teams/team_001/members/{uid}
    members = [
        {
            "uid":       EMPLOYEE_UID,
            "email":     "employee@test.com",
            "role":      "employee",
            "joinedAt":  firestore.SERVER_TIMESTAMP
        },
        {
            "uid":       M1_MANAGER_UID,
            "email":     "m1manager@test.com",
            "role":      "m1_manager",
            "joinedAt":  firestore.SERVER_TIMESTAMP
        }
    ]

    for member in members:
        db.collection('teams').document('team_001')\
          .collection('members').document(member['uid']).set(member)
        print(f"✅ Added member: {member['email']} as {member['role']}")

    print(f"\n✅ TEAM SEEDED SUCCESSFULLY")
    print("=" * 52)


if __name__ == '__main__':
    seed_teams()