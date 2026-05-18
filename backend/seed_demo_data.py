"""
seed_demo_data.py — Seeds realistic demo leads for stakeholder demo
Run from project root: python backend/seed_demo_data.py

Creates 10 realistic leads across various pipeline stages
so the dashboards look meaningful for the V1 demo.
"""

import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from firebase_config import initialize_firebase, get_firestore_client
from firebase_admin import firestore

# ── PASTE YOUR EMPLOYEE UID HERE ───────────────────────────────────────────────
EMPLOYEE_UID = "DXsAbjuiEgTHmZBEdGw7u8zaOxF2"
TEAM_ID      = "team_001"
# ──────────────────────────────────────────────────────────────────────────────

DEMO_LEADS = [
    {
        "name":        "Priya Sharma",
        "company":     "TechVentures Pvt Ltd",
        "email":       "priya.sharma@techventures.com",
        "phone":       "+91 9876543201",
        "linkedinUrl": "https://linkedin.com/in/priyasharma",
        "currentStage": "stage_8",
        "isArchived":  False,
    },
    {
        "name":        "Rahul Mehta",
        "company":     "InnoSoft Solutions",
        "email":       "rahul.mehta@innosoft.in",
        "phone":       "+91 9876543202",
        "linkedinUrl": "https://linkedin.com/in/rahulmehta",
        "currentStage": "stage_7",
        "isArchived":  False,
    },
    {
        "name":        "Ananya Krishnan",
        "company":     "Digital Dynamics",
        "email":       "ananya.k@digitaldynamics.com",
        "phone":       "+91 9876543203",
        "linkedinUrl": "https://linkedin.com/in/ananyak",
        "currentStage": "stage_6_1",
        "isArchived":  False,
    },
    {
        "name":        "Vikram Patel",
        "company":     "CloudBase Systems",
        "email":       "vikram.patel@cloudbase.io",
        "phone":       "+91 9876543204",
        "linkedinUrl": "https://linkedin.com/in/vikrampatel",
        "currentStage": "stage_6_3",
        "isArchived":  False,
    },
    {
        "name":        "Sneha Reddy",
        "company":     "Apex Consulting",
        "email":       "sneha.reddy@apexconsult.com",
        "phone":       "+91 9876543205",
        "linkedinUrl": "https://linkedin.com/in/snehareddy",
        "currentStage": "stage_4",
        "isArchived":  False,
    },
    {
        "name":        "Arjun Nair",
        "company":     "NextGen Technologies",
        "email":       "arjun.nair@nextgen.tech",
        "phone":       "+91 9876543206",
        "linkedinUrl": "https://linkedin.com/in/arjunnair",
        "currentStage": "stage_3",
        "isArchived":  False,
    },
    {
        "name":        "Kavya Iyer",
        "company":     "SmartBiz Analytics",
        "email":       "kavya.iyer@smartbiz.in",
        "phone":       "+91 9876543207",
        "linkedinUrl": "https://linkedin.com/in/kavyaiyer",
        "currentStage": "stage_2_1",
        "isArchived":  False,
    },
    {
        "name":        "Rohan Gupta",
        "company":     "FutureTech Labs",
        "email":       "rohan.gupta@futuretech.co.in",
        "phone":       "+91 9876543208",
        "linkedinUrl": "https://linkedin.com/in/rohangupta",
        "currentStage": "stage_2",
        "isArchived":  False,
    },
    {
        "name":        "Meera Joshi",
        "company":     "GrowthMatrix Pvt Ltd",
        "email":       "meera.joshi@growthmatrix.com",
        "phone":       "+91 9876543209",
        "linkedinUrl": "https://linkedin.com/in/meerajoshi",
        "currentStage": "stage_1_1",
        "isArchived":  False,
    },
    {
        "name":        "Siddharth Kumar",
        "company":     "PeakPerform Solutions",
        "email":       "siddharth.k@peakperform.in",
        "phone":       "+91 9876543210",
        "linkedinUrl": "https://linkedin.com/in/siddharthk",
        "currentStage": "stage_6_2",
        "isArchived":  True,
    },
]


def seed_demo_data():
    print("\n" + "=" * 52)
    print("   Seeding Demo Data for V1 Stakeholder Demo")
    print("=" * 52)

    if "PASTE_" in EMPLOYEE_UID:
        print("\n❌ ERROR: Replace EMPLOYEE_UID with the real UID")
        print("   Open seed_demo_data.py and paste the real UID")
        return

    initialize_firebase()
    db = get_firestore_client()

    for lead_data in DEMO_LEADS:
        lead_id = str(uuid.uuid4())

        lead = {
            "leadId":       lead_id,
            "employeeUid":  EMPLOYEE_UID,
            "teamId":       TEAM_ID,
            "name":         lead_data["name"],
            "company":      lead_data["company"],
            "email":        lead_data["email"],
            "phone":        lead_data["phone"],
            "linkedinUrl":  lead_data["linkedinUrl"],
            "currentStage": lead_data["currentStage"],
            "isArchived":   lead_data["isArchived"],
            "createdAt":    firestore.SERVER_TIMESTAMP,
            "updatedAt":    firestore.SERVER_TIMESTAMP
        }

        db.collection('leads').document(lead_id).set(lead)

        # Write audit log
        log_id = str(uuid.uuid4())
        db.collection('audit_logs').document(log_id).set({
            "logId":       log_id,
            "leadId":      lead_id,
            "employeeUid": EMPLOYEE_UID,
            "fromStage":   None,
            "toStage":     lead_data["currentStage"],
            "changedAt":   firestore.SERVER_TIMESTAMP,
            "notes":       "Demo lead created for V1"
        })

        print(f"✅ Created: {lead_data['name']} "
              f"| {lead_data['company']} "
              f"| Stage: {lead_data['currentStage']}")

    print(f"\n✅ {len(DEMO_LEADS)} DEMO LEADS CREATED SUCCESSFULLY")
    print("=" * 52)
    print("\nLogin as employee@test.com to see them in the dashboard.")


if __name__ == '__main__':
    seed_demo_data()