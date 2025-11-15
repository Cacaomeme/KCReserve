"""Blueprint exposing health-check style endpoints."""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/api/health")
def health_check():
    """Simple readiness endpoint used by monitors and tests."""
    return jsonify({"status": "ok"})
