"""
Flight Search Agent — Specialized CrewAI agent for finding optimal flights.

This agent uses mock data to simulate flight search results,
providing realistic fare comparisons and route options.
"""

import json
import random
from datetime import datetime, timedelta

from crewai import Agent

try:
    from crewai.tools import tool as crewai_tool
except ImportError:
    from crewai_tools import tool as crewai_tool


AIRLINES = [
    {"name": "SkyVista Airways", "code": "SVA", "rating": 4.5},
    {"name": "AeroConnect", "code": "ACN", "rating": 4.2},
    {"name": "GlobalWing Airlines", "code": "GWA", "rating": 4.7},
    {"name": "PacificStar", "code": "PST", "rating": 4.0},
    {"name": "TransWorld Express", "code": "TWE", "rating": 4.3},
    {"name": "NorthSky Aviation", "code": "NSA", "rating": 4.6},
]


def _generate_mock_flights(origin: str, destination: str, date: str, budget: str) -> list:
    """Generate realistic mock flight data."""
    budget_map = {"budget": (12000, 33000), "moderate": (25000, 58000), "luxury": (50000, 125000)}
    price_range = budget_map.get(budget.lower(), (16000, 66000))

    flights = []
    for _ in range(random.randint(3, 6)):
        airline = random.choice(AIRLINES)
        departure_hour = random.randint(5, 22)
        duration_hours = random.randint(2, 14)
        duration_mins = random.choice([0, 15, 30, 45])
        stops = random.choices([0, 1, 2], weights=[40, 45, 15])[0]
        price = round(random.uniform(*price_range), 2)

        if stops > 0:
            price *= 0.85

        flights.append({
            "airline": airline["name"],
            "airline_code": airline["code"],
            "airline_rating": airline["rating"],
            "flight_number": f"{airline['code']}{random.randint(100, 999)}",
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_time": f"{departure_hour:02d}:{random.choice(['00','15','30','45'])}",
            "duration": f"{duration_hours}h {duration_mins}m",
            "stops": stops,
            "stop_type": "Non-stop" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}",
            "price_inr": round(price, 2),
            "class": "Economy" if budget.lower() == "budget" else "Business" if budget.lower() == "luxury" else "Premium Economy",
            "date": date,
        })

    flights.sort(key=lambda x: x["price_inr"])
    return flights


@crewai_tool
def search_flights(query: str) -> str:
    """Search for available flights between cities. Input should be a JSON string
    with keys: origin, destination, date, budget (budget/moderate/luxury)."""
    try:
        params = json.loads(query)
    except json.JSONDecodeError:
        parts = query.replace(",", " ").split()
        params = {
            "origin": parts[0] if len(parts) > 0 else "NYC",
            "destination": parts[1] if len(parts) > 1 else "LON",
            "date": parts[2] if len(parts) > 2 else "2025-06-15",
            "budget": parts[3] if len(parts) > 3 else "moderate",
        }

    flights = _generate_mock_flights(
        params.get("origin", "NYC"),
        params.get("destination", "LON"),
        params.get("date", "2025-06-15"),
        params.get("budget", "moderate"),
    )
    return json.dumps(flights, indent=2)


def create_flight_agent(llm=None) -> Agent:
    """Create and return the Flight Search Specialist agent."""
    kwargs = {
        "role": "Flight Search Specialist",
        "goal": (
            "Find the best flight options for travelers based on their origin, "
            "destination, preferred dates, and budget. Compare airlines, prices, "
            "and travel times to recommend optimal choices."
        ),
        "backstory": (
            "You are a seasoned aviation expert with over 15 years of experience in "
            "the travel industry. You have an encyclopedic knowledge of airline routes, "
            "pricing strategies, and travel hacks. You are known for finding the best "
            "deals and most convenient flight options for any route in the world."
        ),
        "tools": [search_flights],
        "verbose": True,
        "allow_delegation": False,
    }
    if llm:
        kwargs["llm"] = llm
    return Agent(**kwargs)
