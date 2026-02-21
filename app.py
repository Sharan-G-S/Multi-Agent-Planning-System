"""
Multi-Agent Travel Planning System — Flask API Server

Provides REST endpoints that bridge the web frontend with the
LangGraph + CrewAI agent orchestration backend.
"""

import os
import json
import traceback
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)


# ────────────────────────────────────────────────────────────
# Static file serving
# ────────────────────────────────────────────────────────────

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")


# ────────────────────────────────────────────────────────────
# API Endpoints
# ────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Multi-Agent Travel Planning System",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    })


@app.route("/api/agents", methods=["GET"])
def get_agents():
    """Return information about available agents."""
    return jsonify({
        "agents": [
            {
                "id": "flight_agent",
                "name": "Flight Search Specialist",
                "role": "Flight Search",
                "description": "Finds optimal flight options by comparing airlines, prices, and travel times.",
                "icon": "plane",
                "status": "ready",
            },
            {
                "id": "hotel_agent",
                "name": "Hotel & Accommodation Concierge",
                "role": "Hotel Search",
                "description": "Discovers the best hotels and accommodations based on location, amenities, and ratings.",
                "icon": "building",
                "status": "ready",
            },
            {
                "id": "itinerary_agent",
                "name": "Itinerary Architect",
                "role": "Itinerary Builder",
                "description": "Crafts day-by-day travel itineraries with attractions, dining, and local tips.",
                "icon": "map",
                "status": "ready",
            },
        ]
    })


@app.route("/api/plan", methods=["POST"])
def create_plan():
    """
    Main planning endpoint. Accepts travel preferences and runs
    the LangGraph orchestration pipeline.

    Request body (JSON):
        - origin: str (departure city)
        - destination: str (arrival city)
        - departure_date: str (YYYY-MM-DD)
        - return_date: str (YYYY-MM-DD)
        - budget: str (budget/moderate/luxury)
        - travelers: int
        - interests: str (comma-separated)
        - special_requests: str
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        if not data.get("destination"):
            return jsonify({"success": False, "error": "Destination is required"}), 400

        # ─── Run the LangGraph pipeline ───
        from orchestrator.graph_orchestrator import run_planning_pipeline

        params = {
            "origin": data.get("origin", "NYC"),
            "destination": data.get("destination", "London"),
            "departure_date": data.get("departure_date", "2025-06-15"),
            "return_date": data.get("return_date", "2025-06-20"),
            "budget": data.get("budget", "moderate"),
            "travelers": data.get("travelers", 1),
            "interests": data.get("interests", "culture,food,history"),
            "special_requests": data.get("special_requests", ""),
        }

        result = run_planning_pipeline(params)

        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@app.route("/api/plan/crew", methods=["POST"])
def create_plan_crew():
    """
    Alternative endpoint using CrewAI orchestration (requires API key).
    Falls back to LangGraph pipeline if CrewAI execution fails.
    """
    try:
        data = request.get_json()

        if not data or not data.get("destination"):
            return jsonify({"success": False, "error": "Destination is required"}), 400

        from orchestrator.crew_manager import run_crew

        params = {
            "origin": data.get("origin", "NYC"),
            "destination": data.get("destination", "London"),
            "departure_date": data.get("departure_date", "2025-06-15"),
            "return_date": data.get("return_date", "2025-06-20"),
            "budget": data.get("budget", "moderate"),
            "num_days": data.get("num_days", 3),
            "interests": data.get("interests", "culture,food,history"),
        }

        result = run_crew(params)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


# ────────────────────────────────────────────────────────────
# Run
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    print(f"\n{'='*60}")
    print(f"  Multi-Agent Travel Planning System")
    print(f"  Running on http://localhost:{port}")
    print(f"  Debug mode: {debug}")
    print(f"{'='*60}\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
