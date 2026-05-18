"""
seed_users.py — Seeds the 3 test users into Firestore
Run this ONCE to create user documents for your 3 test accounts.

How to run (from project root):
    python backend/seed_users.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

from firebase_config import initialize_firebase, get_firestore_client
from firebase_admin import firestore

# ── PASTE YOUR 3 UIDs HERE ─────────────────────────────────────────────────────

EMPLOYEE_UID   = "DXsAbjuiEgTHmZBEdGw7u8zaOxF2"
M1_MANAGER_UID = "APm9grZhkPUNSexOJpfzY8eZeUz2"
M2_MANAGER_UID = "vnpNDxrwePVKE8GqFrhqKESbizI2"

# ──────────────────────────────────────────────────────────────────────────────


def seed_users():

    print("\n" + "=" * 52)
    print("   Seeding Users into Firestore")
    print("=" * 52)

    initialize_firebase()

    db = get_firestore_client()

    # ──────────────────────────────────────────────────────────────────────
    # EMPLOYEE USER
    # ──────────────────────────────────────────────────────────────────────

    if "PASTE_" in EMPLOYEE_UID:
        print("\n❌ ERROR: Replace EMPLOYEE_UID with real UID")
        return

    db.collection('users').document(EMPLOYEE_UID).set({
        "uid":         EMPLOYEE_UID,
        "email":       "employee@test.com",
        "displayName": "Test Employee",
        "role":        "employee",
        "teamId":      "team_001",
        "isActive":    True,
        "createdAt":   firestore.SERVER_TIMESTAMP
    })

    print("✅ Created: employee@test.com | role: employee")

    # ──────────────────────────────────────────────────────────────────────
    # M1 MANAGER USER
    # ──────────────────────────────────────────────────────────────────────

    if "PASTE_" in M1_MANAGER_UID:
        print("\n❌ ERROR: Replace M1_MANAGER_UID with real UID")
        return

    db.collection('users').document(M1_MANAGER_UID).set({
        "uid":         M1_MANAGER_UID,
        "email":       "m1manager@test.com",
        "displayName": "Test M1 Manager",
        "role":        "m1_manager",
        "teamId":      "team_001",
        "isActive":    True,
        "createdAt":   firestore.SERVER_TIMESTAMP
    })

    print("✅ Created: m1manager@test.com | role: m1_manager")

    # ──────────────────────────────────────────────────────────────────────
    # M2 MANAGER USER
    # ──────────────────────────────────────────────────────────────────────

    if "PASTE_" in M2_MANAGER_UID:
        print("\n❌ ERROR: Replace M2_MANAGER_UID with real UID")
        return

    # ── Highlander Rule check before seeding M2 ───────────────────────────

    existing_m2 = (
        db.collection('users')
        .where('role', '==', 'm2_manager')
        .get()
    )

    other_m2 = [
        d for d in existing_m2
        if d.id != M2_MANAGER_UID
    ]

    if other_m2:

        print("\n⚠️  WARNING: Another M2 Manager already exists!")
        print("   Highlander Rule: Only ONE M2 Manager allowed.")
        print("   Skipping M2 creation to avoid conflict.")

    else:

        db.collection('users').document(M2_MANAGER_UID).set({
            "uid":         M2_MANAGER_UID,
            "email":       "m2manager@test.com",
            "displayName": "Test M2 Manager",
            "role":        "m2_manager",
            "teamId":      None,
            "isActive":    True,
            "createdAt":   firestore.SERVER_TIMESTAMP
        })

        print("✅ Created: m2manager@test.com | role: m2_manager")

    # ──────────────────────────────────────────────────────────────────────

    print("\n✅ USER SEEDING PROCESS COMPLETED")
    print("=" * 52)


if __name__ == '__main__':
    seed_users()