"""
stages.py — Pipeline Stages API Routes
Provides the list of active pipeline stages to the frontend.
Includes simple in-memory caching to reduce Firestore reads.
"""

from flask import Blueprint, jsonify, session
from firebase_config import get_firestore_client
import time

stages_bp = Blueprint('stages', __name__)

# ── SIMPLE IN-MEMORY CACHE ─────────────────────────────────────────────────────
_stages_cache      = None
_stages_cache_time = 0
CACHE_TTL          = 300  # 5 minutes in seconds


def get_cached_stages(db):
    """
    Returns stages from cache if fresh, otherwise fetches from Firestore.
    Stages change rarely so 5-minute caching is safe.
    """
    global _stages_cache, _stages_cache_time

    now = time.time()
    if _stages_cache and (now - _stages_cache_time) < CACHE_TTL:
        return _stages_cache

    # Fetch from Firestore
    all_stages_ref = db.collection('pipeline_stages').get()
    stages = sorted(
        [s for s in all_stages_ref
         if s.to_dict().get('isActive', True)],
        key=lambda x: x.to_dict().get('stageOrder', 0)
    )

    stages_list = []
    for stage in stages:
        data = stage.to_dict()
        stages_list.append({
            "stageId":     data.get('stageId'),
            "stageNumber": data.get('stageNumber'),
            "stageName":   data.get('stageName'),
            "description": data.get('description'),
            "stageOrder":  data.get('stageOrder'),
            "isArchived":  data.get('isArchived', False),
        })

    _stages_cache      = stages_list
    _stages_cache_time = now
    return stages_list


def invalidate_stages_cache():
    """Call this whenever stages are created/updated/deleted."""
    global _stages_cache, _stages_cache_time
    _stages_cache      = None
    _stages_cache_time = 0


@stages_bp.route('/api/stages', methods=['GET'])
def get_stages():
    """
    Returns all active pipeline stages ordered by stageOrder.
    Cached for 5 minutes to reduce Firestore reads.
    """
    if 'uid' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        db          = get_firestore_client()
        stages_list = get_cached_stages(db)

        return jsonify({
            "stages": stages_list,
            "total":  len(stages_list)
        })

    except Exception as e:
        print(f"Error fetching stages: {e}")
        return jsonify({"error": str(e)}), 500