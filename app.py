"""
Multi-Agent Travel Planning System — Flask API Server

Provides REST endpoints that bridge the web frontend with the
LangGraph + CrewAI agent orchestration backend.
"""

import os
import re
import json
import traceback
from datetime import datetime, timedelta

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
                "id": "train_agent",
                "name": "Indian Railways Specialist",
                "role": "Train Search",
                "description": "Searches Indian Railways routes with IRCTC classes and INR fares.",
                "icon": "train",
                "status": "ready",
            },
            {
                "id": "road_agent",
                "name": "Road Travel Specialist",
                "role": "Road Search",
                "description": "Finds buses, cabs, and self-drive options across Tamil Nadu and India.",
                "icon": "bus",
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
# Chat Endpoint — Natural Language Interface
# ────────────────────────────────────────────────────────────

INDIAN_CITIES = [
    "coimbatore", "chennai", "bangalore", "bengaluru", "mumbai", "delhi",
    "new delhi", "hyderabad", "kolkata", "pune", "jaipur", "goa",
    "madurai", "ooty", "mysore", "mysuru", "kochi", "cochin",
    "trivandrum", "thiruvananthapuram", "pondicherry", "puducherry",
    "trichy", "tiruchirappalli", "salem", "erode", "tiruppur",
    "thanjavur", "rameswaram", "kanyakumari", "kodaikanal",
    "varanasi", "agra", "udaipur", "lucknow", "ahmedabad",
    "chandigarh", "shimla", "manali", "darjeeling", "gangtok",
    "srinagar", "leh", "amritsar", "vellore", "pollachi",
    "dindigul", "munnar", "alleppey", "wayanad", "vizag",
    "visakhapatnam", "bhopal", "indore", "nagpur", "patna",
    "ranchi", "bhubaneswar", "guwahati",
    # International
    "new york", "london", "paris", "tokyo", "dubai", "singapore",
    "bangkok", "hong kong", "sydney", "los angeles", "san francisco",
    "rome", "barcelona", "amsterdam", "berlin", "toronto",
    "kuala lumpur", "bali", "maldives", "colombo", "kathmandu",
]


def parse_travel_query(message):
    """Extract travel parameters from a natural language message."""
    msg = message.lower().strip()
    result = {
        "origin": None,
        "destination": None,
        "budget": "moderate",
        "travelers": 2,
        "interests": "",
        "departure_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "return_date": (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d"),
    }

    # ─── Extract origin and destination ───
    # Pattern: "from X to Y"
    from_to = re.search(r'from\s+([a-z\s]+?)\s+to\s+([a-z\s]+?)(?:\s+(?:on|in|for|with|budget|next|this|tomorrow|\d|$))', msg)
    if from_to:
        result["origin"] = from_to.group(1).strip().title()
        result["destination"] = from_to.group(2).strip().title()
    else:
        # Pattern: "X to Y"
        x_to_y = re.search(r'([a-z\s]+?)\s+to\s+([a-z\s]+?)(?:\s+(?:on|in|for|with|budget|next|this|tomorrow|\d|$))', msg)
        if x_to_y:
            origin_candidate = x_to_y.group(1).strip()
            dest_candidate = x_to_y.group(2).strip()
            # Take last word(s) that match a city for origin
            for city in sorted(INDIAN_CITIES, key=len, reverse=True):
                if origin_candidate.endswith(city) or origin_candidate == city:
                    result["origin"] = city.title()
                    break
            for city in sorted(INDIAN_CITIES, key=len, reverse=True):
                if dest_candidate.startswith(city) or dest_candidate == city:
                    result["destination"] = city.title()
                    break

    # If still no match, try finding any two cities mentioned
    if not result["origin"] or not result["destination"]:
        found_cities = []
        for city in sorted(INDIAN_CITIES, key=len, reverse=True):
            if city in msg and city.title() not in found_cities:
                found_cities.append(city.title())
            if len(found_cities) == 2:
                break
        if len(found_cities) >= 2:
            result["origin"] = found_cities[0]
            result["destination"] = found_cities[1]
        elif len(found_cities) == 1:
            result["destination"] = found_cities[0]
            result["origin"] = "Coimbatore"  # Default origin

    # ─── Budget ───
    if any(w in msg for w in ["cheap", "budget", "low cost", "affordable", "economy"]):
        result["budget"] = "budget"
    elif any(w in msg for w in ["luxury", "premium", "expensive", "high-end", "5 star", "five star"]):
        result["budget"] = "luxury"

    # ─── Travelers ───
    travelers_match = re.search(r'(\d+)\s*(?:traveler|passenger|person|people|pax)', msg)
    if travelers_match:
        result["travelers"] = min(int(travelers_match.group(1)), 10)
    elif "solo" in msg:
        result["travelers"] = 1
    elif "couple" in msg:
        result["travelers"] = 2
    elif "family" in msg:
        result["travelers"] = 4
    elif "group" in msg:
        result["travelers"] = 6

    # ─── Dates ───
    if "tomorrow" in msg:
        result["departure_date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        result["return_date"] = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")
    elif "next week" in msg:
        result["departure_date"] = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        result["return_date"] = (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d")
    elif "next month" in msg:
        result["departure_date"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        result["return_date"] = (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")
    elif "this weekend" in msg:
        days_until_sat = (5 - datetime.now().weekday()) % 7
        if days_until_sat == 0:
            days_until_sat = 7
        result["departure_date"] = (datetime.now() + timedelta(days=days_until_sat)).strftime("%Y-%m-%d")
        result["return_date"] = (datetime.now() + timedelta(days=days_until_sat + 2)).strftime("%Y-%m-%d")

    # Date pattern: YYYY-MM-DD
    date_match = re.findall(r'\d{4}-\d{2}-\d{2}', msg)
    if len(date_match) >= 2:
        result["departure_date"] = date_match[0]
        result["return_date"] = date_match[1]
    elif len(date_match) == 1:
        result["departure_date"] = date_match[0]
        dep = datetime.strptime(date_match[0], "%Y-%m-%d")
        result["return_date"] = (dep + timedelta(days=5)).strftime("%Y-%m-%d")

    # ─── Days ───
    days_match = re.search(r'(\d+)\s*(?:day|night)', msg)
    if days_match:
        num_days = int(days_match.group(1))
        dep = datetime.strptime(result["departure_date"], "%Y-%m-%d")
        result["return_date"] = (dep + timedelta(days=num_days)).strftime("%Y-%m-%d")

    # ─── Interests ───
    interest_keywords = {
        "temple": "temples", "temples": "temples", "spiritual": "temples",
        "beach": "beaches", "beaches": "beaches", "sea": "beaches",
        "food": "food", "cuisine": "food", "restaurant": "food",
        "culture": "culture", "history": "history", "museum": "history",
        "nature": "nature", "hill": "nature", "hills": "nature",
        "mountain": "nature", "trek": "adventure", "trekking": "adventure",
        "adventure": "adventure", "shopping": "shopping",
        "nightlife": "nightlife", "party": "nightlife",
        "wildlife": "wildlife", "safari": "wildlife",
        "pilgrimage": "temples", "heritage": "history",
    }
    found_interests = set()
    for keyword, interest in interest_keywords.items():
        if keyword in msg:
            found_interests.add(interest)
    result["interests"] = ", ".join(found_interests) if found_interests else "culture, sightseeing"

    return result


def format_chat_response(data, params):
    """Build a conversational response from pipeline results."""
    flights = data.get("flights", [])
    hotels = data.get("hotels", [])
    trains = data.get("trains", [])
    road_options = data.get("road_options", [])
    itinerary = data.get("itinerary", [])

    lines = []
    lines.append(f"Here's your travel plan for **{params['origin']} to {params['destination']}** ({params['departure_date']} to {params['return_date']}):\n")

    if flights:
        if len(flights) == 1 and flights[0].get('airline') == 'No Airport':
            lines.append(f"**Flights** — {flights[0].get('note', 'No airport at this destination')}\n")
        else:
            best_f = min(flights, key=lambda x: x.get("price_inr", 999999))
            lines.append(f"**Flights** — {len(flights)} options found")
            lines.append(f"  Best: {best_f['airline']} at \u20b9{best_f['price_inr']:,.0f}/person\n")

    if trains:
        if len(trains) == 1 and trains[0].get('train_name') == 'No Direct Trains':
            lines.append(f"**Trains** — {trains[0].get('note', 'No direct trains on this route')}\n")
        else:
            best_t = min(trains, key=lambda x: x.get("fare_inr", 99999))
            lines.append(f"**Trains** — {len(trains)} options found")
            lines.append(f"  Best: {best_t['train_name']} ({best_t.get('class', '')}) at \u20b9{best_t['fare_inr']:,.0f}\n")

    if road_options:
        best_r = min(road_options, key=lambda x: x.get("fare_inr", 99999))
        lines.append(f"**Road Travel** — {len(road_options)} options found")
        lines.append(f"  Best: {best_r['operator']} ({best_r['mode']}) at \u20b9{best_r['fare_inr']:,.0f}\n")

    if hotels:
        best_h = min(hotels, key=lambda x: x.get("price_per_night_inr", 999999))
        lines.append(f"**Hotels** — {len(hotels)} options found")
        lines.append(f"  Best: {best_h['name']} at \u20b9{best_h['price_per_night_inr']:,.0f}/night\n")

    if itinerary:
        lines.append(f"**Itinerary** — {len(itinerary)}-day plan generated with local attractions\n")

    lines.append("Check the tabs above for full details on each category!")
    return "\n".join(lines)


@app.route("/api/chat", methods=["POST"])
def chat():
    """Chat endpoint — parses natural language and runs the agent pipeline."""
    try:
        data = request.get_json()
        message = (data or {}).get("message", "").strip()

        if not message:
            return jsonify({
                "success": True,
                "reply": "Hello! I'm your AI Travel Assistant. Tell me where you'd like to go!\n\nTry: *'Plan a trip from Coimbatore to Ooty for 3 days'*",
                "has_results": False,
            })

        # ─── Quick greetings ───
        greetings = ["hi", "hello", "hey", "good morning", "good evening", "good afternoon"]
        if message.lower().strip().rstrip('!.') in greetings:
            return jsonify({
                "success": True,
                "reply": "Hello! I'm your AI Travel Planner. I can find flights, trains, buses, hotels, and build itineraries for you.\n\nJust tell me something like:\n- *'Find buses from Coimbatore to Chennai'*\n- *'Plan a luxury trip from Delhi to Goa for 5 days'*\n- *'Trains from Madurai to Ooty this weekend'*",
                "has_results": False,
            })

        # ─── Help messages ───
        if any(w in message.lower() for w in ["help", "what can you do", "how to", "guide"]):
            return jsonify({
                "success": True,
                "reply": "I can help you plan trips across India and the world! Here's what I search:\n\n**5 Specialized Agents:**\n- Flights — airlines, prices & routes\n- Hotels — ratings, amenities & pricing\n- Trains — Indian Railways with IRCTC classes\n- Road — Buses (TNSTC/KPN), cabs (Ola/Uber), self-drive\n- Itinerary — Day-by-day plans with local attractions\n\n**Example queries:**\n- *'Coimbatore to Chennai budget trip for 3 days'*\n- *'Family trip from Bangalore to Ooty next week'*\n- *'Solo travel to Pondicherry this weekend'*",
                "has_results": False,
            })

        # ─── Parse & run pipeline ───
        params = parse_travel_query(message)

        if not params["destination"]:
            return jsonify({
                "success": True,
                "reply": "I couldn't identify a destination from your message. Could you try again with something like:\n\n*'Plan a trip from Coimbatore to Chennai'*\nor\n*'Find buses to Ooty for this weekend'*",
                "has_results": False,
            })

        if not params["origin"]:
            params["origin"] = "Coimbatore"

        from orchestrator.graph_orchestrator import run_planning_pipeline
        result = run_planning_pipeline(params)

        if result.get("success"):
            reply = format_chat_response(result["data"], params)
            return jsonify({
                "success": True,
                "reply": reply,
                "has_results": True,
                "data": result["data"],
                "params": params,
            })
        else:
            return jsonify({
                "success": True,
                "reply": f"I encountered an issue while planning: {result.get('error', 'Unknown error')}. Please try again.",
                "has_results": False,
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "reply": f"Sorry, something went wrong: {str(e)}. Please try again.",
            "has_results": False,
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
