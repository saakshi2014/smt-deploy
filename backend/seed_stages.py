"""
seed_stages.py — Seeds all 13 default pipeline stages into Firestore
Run this ONCE from the project root:
    python backend/seed_stages.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from firebase_config import initialize_firebase, get_firestore_client
from firebase_admin import firestore


# ── THE 13 DEFAULT PIPELINE STAGES ────────────────────────────────────────────
# These match exactly the stages defined in the SRS document.
# stageOrder is used to sort stages in the correct sequence in the UI.

DEFAULT_STAGES = [
    {
        "stageId":     "stage_1_1",
        "stageNumber": "1.1",
        "stageName":   "Qualified – Pending Outreach",
        "description": "Lead has been identified and qualified. Outreach has not yet started.",
        "stageOrder":  1,
        "isDefault":   True,
        "isActive":    True,
        "isArchived":  False,
        "createdBy":   None,
        "createdAt":   firestore.SERVER_TIMESTAMP
    },
    {
        "stageId":     "stage_1_2",
        "stageNumber": "1.2",
        "stageName":   "Not Qualified",
        "description": "Lead has been reviewed and does not meet the qualifying criteria.",
        "stageOrder":  2,
        "isDefault":   True,
        "isActive":    True,
        "isArchived":  False,
        "createdBy":   None,
        "createdAt":   firestore.SERVER_TIMESTAMP
    },
    {
        "stageId":     "stage_2",
        "stageNumber": "2",
        "stageName":   "Connection Request Sent",
        "description": "A connection request has been sent to the lead on LinkedIn.",
        "stageOrder":  3,
        "isDefault":   True,
        "isActive":    True,
        "isArchived":  False,
        "createdBy":   None,
        "createdAt":   firestore.SERVER_TIMESTAMP
    },
    {
        "stageId":     "stage_2_1",
        "stageNumber": "2.1",
        "stageName":   "Connected on LinkedIn",
        "description": "The lead has accepted the connection request.",
        "stageOrder":  4,
        "isDefault":   True,
        "isActive":    True,
        "isArchived":  False,
        "createdBy":   None,
        "createdAt":   firestore.SERVER_TIMESTAMP
    },
    {
        "stageId":     "stage_2_2",
        "stageNumber": "2.2",
        "stageName":   "Connection Not Accepted",
        "description": "The lead has not accepted the connection request.",
        "stageOrder":  5,
        "isDefault":   True,
        "isActive":    True,
        "isArchived":  False,
        "createdBy":   None,
        "createdAt":   firestore.SERVER_TIMESTAMP
    },
    {
        "stageId":     "stage_3",
        "stageNumber": "3",
        "stageName":   "Initial Message Sent",
        "description": "The first outreach message has been sent to the lead.",
        "stageOrder":  6,
        "isDefault":   True,
        "isActive":    True,
        "isArchived":  False,
        "createdBy":   None,
        "createdAt":   firestore.SERVER_TIMESTAMP
    },
    {
        "stageId":     "stage_3_1",
        "stageNumber": "3.1",
        "stageName":   "No Response",
        "description": "No reply has been received to the initial message.",
        "stageOrder":  7,
        "isDefault":   True,
        "isActive":    True,
        "isArchived":  False,
        "createdBy":   None,
        "createdAt":   firestore.SERVER_TIMESTAMP
    },
    {
        "stageId":     "stage_4",
        "stageNumber": "4",
        "stageName":   "Initial Reply Received",
        "description": "The lead has responded to the initial outreach message.",
        "stageOrder":  8,
        "isDefault":   True,
        "isActive":    True,
        "isArchived":  False,
        "createdBy":   None,
        "createdAt":   firestore.SERVER_TIMESTAMP
    },
    {
        "stageId":     "stage_6_1",
        "stageNumber": "6.1",
        "stageName":   "Interested – Ready for Meeting",
        "description": "Lead has expressed interest and is open to scheduling a meeting.",
        "stageOrder":  9,
        "isDefault":   True,
        "isActive":    True,
        "isArchived":  False,
        "createdBy":   None,
        "createdAt":   firestore.SERVER_TIMESTAMP
    },
    {
        "stageId":     "stage_6_2",
        "stageNumber": "6.2",
        "stageName":   "Not Interested – Archived",
        "description": "Lead has explicitly declined. Archived for future reference.",
        "stageOrder":  10,
        "isDefault":   True,
        "isActive":    True,
        "isArchived":  True,
        "createdBy":   None,
        "createdAt":   firestore.SERVER_TIMESTAMP
    },
    {
        "stageId":     "stage_6_3",
        "stageNumber": "6.3",
        "stageName":   "Warm Lead – Needs Nurturing",
        "description": "Lead has not committed yet but remains a potential future opportunity.",
        "stageOrder":  11,
        "isDefault":   True,
        "isActive":    True,
        "isArchived":  False,
        "createdBy":   None,
        "createdAt":   firestore.SERVER_TIMESTAMP
    },
    {
        "stageId":     "stage_7",
        "stageNumber": "7",
        "stageName":   "Meeting Scheduled",
        "description": "A meeting has been booked with the lead.",
        "stageOrder":  12,
        "isDefault":   True,
        "isActive":    True,
        "isArchived":  False,
        "createdBy":   None,
        "createdAt":   firestore.SERVER_TIMESTAMP
    },
    {
        "stageId":     "stage_8",
        "stageNumber": "8",
        "stageName":   "Meeting Completed",
        "description": "The meeting with the lead has taken place.",
        "stageOrder":  13,
        "isDefault":   True,
        "isActive":    True,
        "isArchived":  False,
        "createdBy":   None,
        "createdAt":   firestore.SERVER_TIMESTAMP
    },
]


def seed_stages():
    print("\n" + "=" * 52)
    print("   Seeding Pipeline Stages into Firestore")
    print("=" * 52)

    initialize_firebase()
    db = get_firestore_client()

    # Check if stages already exist
    existing = db.collection('pipeline_stages').limit(1).get()
    if len(list(existing)) > 0:
        print("\n⚠️  Pipeline stages already exist in Firestore.")
        print("   Delete the pipeline_stages collection first if you")
        print("   want to re-seed.")
        print("=" * 52)
        return

    # Seed all 13 stages
    for stage in DEFAULT_STAGES:
        stage_id = stage["stageId"]
        db.collection('pipeline_stages').document(stage_id).set(stage)
        print(f"✅ Stage {stage['stageNumber']:4s} — {stage['stageName']}")

    print(f"\n✅ ALL {len(DEFAULT_STAGES)} STAGES SEEDED SUCCESSFULLY")
    print("=" * 52)


if __name__ == '__main__':
    seed_stages()