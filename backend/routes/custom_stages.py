"""
custom_stages.py — Custom Pipeline Stages API Routes
Handles: create custom stage, rename, deactivate, list all stages
Only M1 and M2 Managers can manage custom stages.
"""

from flask import Blueprint, request, jsonify, session
from firebase_config import get_firestore_client
from routes.stages import invalidate_stages_cache
from firebase_admin import firestore
import uuid

custom_stages_bp = Blueprint('custom_stages', __name__)


def require_auth():
    if 'uid' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    return None


# ── ROUTE 1: Create a custom stage ────────────────────────────────────────────
@custom_stages_bp.route('/api/custom-stages', methods=['POST'])
def create_custom_stage():
    """
    Creates a new custom pipeline stage.
    M1/M2 only.

    Request body:
    {
        "stageName":   "Proposal Sent",
        "description": "We have sent a formal proposal to the lead",
        "stageOrder":  8.5
    }
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    role = session['role']
    if role not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Only managers can create custom stages"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    stage_name  = data.get('stageName', '').strip()
    description = data.get('description', '').strip()
    stage_order = data.get('stageOrder', 99)

    if not stage_name:
        return jsonify({"error": "Stage name is required"}), 400

    try:
        db = get_firestore_client()

        # Check for duplicate stage name
        existing = db.collection('pipeline_stages')\
                     .where('stageName', '==', stage_name)\
                     .where('isActive', '==', True).get()
        if len(list(existing)) > 0:
            return jsonify({
                "error": f"A stage named '{stage_name}' already exists"
            }), 409

        stage_id = f"custom_{str(uuid.uuid4())[:8]}"

        stage = {
            "stageId":     stage_id,
            "stageNumber": f"C{stage_id[-4:]}",
            "stageName":   stage_name,
            "description": description,
            "stageOrder":  float(stage_order),
            "isDefault":   False,
            "isActive":    True,
            "isArchived":  False,
            "createdBy":   session['uid'],
            "createdAt":   firestore.SERVER_TIMESTAMP
        }

        db.collection('pipeline_stages').document(stage_id).set(stage)
        invalidate_stages_cache()


        return jsonify({
            "message": "Custom stage created successfully",
            "stage":   {
                "stageId":   stage_id,
                "stageName": stage_name,
                "stageOrder": stage_order,
                "isDefault": False,
                "isActive":  True
            }
        }), 201

    except Exception as e:
        print(f"Error creating custom stage: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 2: Update (rename) a stage ─────────────────────────────────────────
@custom_stages_bp.route('/api/custom-stages/<stage_id>', methods=['PATCH'])
def update_custom_stage(stage_id):
    """
    Renames a custom stage or updates its description.
    Cannot rename default stages.

    Request body:
    { "stageName": "New Name", "description": "Updated description" }
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    role = session['role']
    if role not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Only managers can update stages"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        db        = get_firestore_client()
        stage_ref = db.collection('pipeline_stages').document(stage_id)
        stage_doc = stage_ref.get()

        if not stage_doc.exists:
            return jsonify({"error": "Stage not found"}), 404

        stage_data = stage_doc.to_dict()

        # Cannot rename default stages
        if stage_data.get('isDefault', False):
            return jsonify({
                "error": "Default stages cannot be renamed"
            }), 403

        update_data = {}
        if 'stageName' in data and data['stageName'].strip():
            update_data['stageName']   = data['stageName'].strip()
        if 'description' in data:
            update_data['description'] = data['description'].strip()

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        stage_ref.update(update_data)

        return jsonify({
            "message": "Stage updated successfully",
            "stageId": stage_id,
            "updates": update_data
        })

    except Exception as e:
        print(f"Error updating stage: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 3: Deactivate / Reactivate a stage ──────────────────────────────────
@custom_stages_bp.route('/api/custom-stages/<stage_id>/toggle',
                        methods=['PATCH'])
def toggle_stage(stage_id):
    """
    Deactivates or reactivates a pipeline stage.
    Deactivated stages are hidden from the UI but historical data is kept.
    Default stages CAN be deactivated if not needed.

    Request body: { "isActive": false }
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    role = session['role']
    if role not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Only managers can toggle stages"}), 403

    data = request.get_json()
    if data is None:
        return jsonify({"error": "No data provided"}), 400

    is_active = data.get('isActive', True)

    try:
        db        = get_firestore_client()
        stage_ref = db.collection('pipeline_stages').document(stage_id)
        stage_doc = stage_ref.get()

        if not stage_doc.exists:
            return jsonify({"error": "Stage not found"}), 404

        stage_ref.update({"isActive": is_active})
        invalidate_stages_cache()


        action = "activated" if is_active else "deactivated"
        return jsonify({
            "message":  f"Stage {action} successfully",
            "stageId":  stage_id,
            "isActive": is_active
        })

    except Exception as e:
        print(f"Error toggling stage: {e}")
        return jsonify({"error": str(e)}), 500


# ── ROUTE 4: Get all stages (active + inactive) ───────────────────────────────
@custom_stages_bp.route('/api/custom-stages', methods=['GET'])
def get_all_stages():
    """
    Returns ALL pipeline stages including inactive ones.
    Used by the stage management UI to show which stages exist.
    /api/stages (existing) returns only active stages for the pipeline dropdown.
    """
    auth_error = require_auth()
    if auth_error:
        return auth_error

    role = session['role']
    if role not in ['m1_manager', 'm2_manager']:
        return jsonify({"error": "Only managers can view all stages"}), 403

    try:
        db         = get_firestore_client()
        stages_ref = db.collection('pipeline_stages').get()

        stages = []
        for stage_doc in stages_ref:
            s = stage_doc.to_dict()
            stages.append({
                "stageId":     s.get('stageId'),
                "stageNumber": s.get('stageNumber'),
                "stageName":   s.get('stageName'),
                "description": s.get('description', ''),
                "stageOrder":  s.get('stageOrder', 99),
                "isDefault":   s.get('isDefault', False),
                "isActive":    s.get('isActive', True),
                "isArchived":  s.get('isArchived', False),
                "createdBy":   s.get('createdBy'),
            })

        # Sort by stageOrder
        stages.sort(key=lambda x: x['stageOrder'])

        return jsonify({
            "stages":        stages,
            "total":         len(stages),
            "activeCount":   sum(1 for s in stages if s['isActive']),
            "inactiveCount": sum(1 for s in stages if not s['isActive']),
            "customCount":   sum(1 for s in stages if not s['isDefault']),
        })

    except Exception as e:
        print(f"Error fetching all stages: {e}")
        return jsonify({"error": str(e)}), 500