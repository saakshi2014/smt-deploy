"""
seed_all.py — Runs ALL seeders in the correct order
Run this from the project root:
    python backend/seed_all.py

Order:
    1. seed_users.py   — creates user documents (already done on Day 3)
    2. seed_stages.py  — creates 13 pipeline stages
    3. seed_teams.py   — creates test team and members

"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from seed_stages import seed_stages
from seed_teams  import seed_teams

if __name__ == '__main__':
    print("\n" + "=" * 52)
    print("   RUNNING ALL SEEDERS")
    print("=" * 52)

    print("\n📦 Step 1: Pipeline Stages")
    seed_stages()

    print("\n📦 Step 2: Teams")
    seed_teams()

    print("\n" + "=" * 52)
    print("   ✅ ALL SEEDERS COMPLETE")
    print("=" * 52)