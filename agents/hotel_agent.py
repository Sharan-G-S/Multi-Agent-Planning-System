"""
Hotel Search Agent — Specialized CrewAI agent for finding accommodations.

This agent uses mock data to simulate hotel search results,
providing realistic property comparisons and pricing.
"""

import json
import random

from crewai import Agent

try:
    from crewai.tools import tool as crewai_tool
except ImportError:
    from crewai_tools import tool as crewai_tool


HOTEL_CHAINS = [
    {"name": "Taj", "type": "Luxury Hotel", "stars": 5},
    {"name": "ITC Hotels", "type": "Luxury Hotel", "stars": 5},
    {"name": "The Leela", "type": "Luxury Hotel", "stars": 5},
    {"name": "Lemon Tree", "type": "Business Hotel", "stars": 4},
    {"name": "FabHotel", "type": "Budget Hotel", "stars": 3},
    {"name": "Treebo", "type": "Budget Hotel", "stars": 3},
    {"name": "OYO Rooms", "type": "Budget Hotel", "stars": 2},
    {"name": "Radisson", "type": "Premium Hotel", "stars": 4},
    {"name": "Novotel", "type": "Business Hotel", "stars": 4},
    {"name": "The Residency", "type": "Business Hotel", "stars": 3},
    {"name": "Fortune Hotel", "type": "Business Hotel", "stars": 4},
    {"name": "Zostel", "type": "Hostel", "stars": 2},
]

AMENITIES_POOL = [
    "Free WiFi", "Swimming Pool", "Spa & Wellness", "Fitness Center",
    "Restaurant", "Room Service", "Airport Shuttle", "Parking",
    "Business Center", "Concierge", "Rooftop Bar", "Laundry Service",
    "Pet Friendly", "EV Charging", "Kids Club", "Beach Access",
]


def _generate_mock_hotels(destination: str, checkin: str, checkout: str, budget: str) -> list:
    """Generate realistic mock hotel data."""
    budget_map = {
        "budget": (3000, 10000, [2, 3]),
        "moderate": (8000, 25000, [3, 4]),
        "luxury": (20000, 65000, [4, 5]),
    }
    price_range_min, price_range_max, star_range = budget_map.get(
        budget.lower(), (6500, 29000, [3, 4])
    )

    hotels = []
    for _ in range(random.randint(4, 7)):
        hotel_template = random.choice(HOTEL_CHAINS)
        stars = random.choice(star_range)
        price = round(random.uniform(price_range_min, price_range_max), 2)
        num_amenities = random.randint(4, 10)
        amenities = random.sample(AMENITIES_POOL, min(num_amenities, len(AMENITIES_POOL)))
        rating = round(random.uniform(3.5, 5.0), 1)
        reviews = random.randint(120, 5000)

        hotels.append({
            "name": f"{hotel_template['name']} {destination}",
            "type": hotel_template["type"],
            "stars": stars,
            "location": f"Downtown {destination}",
            "price_per_night_inr": price,
            "total_price_inr": round(price * 3, 2),
            "checkin": checkin,
            "checkout": checkout,
            "rating": rating,
            "reviews_count": reviews,
            "amenities": amenities,
            "cancellation": random.choice(["Free cancellation", "Non-refundable", "Flexible"]),
            "breakfast_included": random.choice([True, False]),
            "distance_to_center": f"{round(random.uniform(0.2, 5.0), 1)} km",
        })

    hotels.sort(key=lambda x: x["price_per_night_inr"])
    return hotels


@crewai_tool
def search_hotels(query: str) -> str:
    """Search for available hotels in a destination. Input should be a JSON string
    with keys: destination, checkin, checkout, budget (budget/moderate/luxury)."""
    try:
        params = json.loads(query)
    except json.JSONDecodeError:
        parts = query.replace(",", " ").split()
        params = {
            "destination": parts[0] if len(parts) > 0 else "London",
            "checkin": parts[1] if len(parts) > 1 else "2025-06-15",
            "checkout": parts[2] if len(parts) > 2 else "2025-06-20",
            "budget": parts[3] if len(parts) > 3 else "moderate",
        }

    hotels = _generate_mock_hotels(
        params.get("destination", "London"),
        params.get("checkin", "2025-06-15"),
        params.get("checkout", "2025-06-20"),
        params.get("budget", "moderate"),
    )
    return json.dumps(hotels, indent=2)


def create_hotel_agent(llm=None) -> Agent:
    """Create and return the Hotel Concierge agent."""
    kwargs = {
        "role": "Hotel & Accommodation Concierge",
        "goal": (
            "Find the best hotel and accommodation options for travelers based on "
            "their destination, travel dates, budget, and preferences. Compare "
            "properties by price, location, amenities, and guest ratings."
        ),
        "backstory": (
            "You are a world-class hotel concierge who has personally visited and "
            "reviewed thousands of properties across the globe. Your deep knowledge "
            "of hospitality trends, hidden gems, and value-for-money options makes "
            "you the go-to expert for accommodation recommendations. You always "
            "consider the traveler's unique needs and preferences."
        ),
        "tools": [search_hotels],
        "verbose": True,
        "allow_delegation": False,
    }
    if llm:
        kwargs["llm"] = llm
    return Agent(**kwargs)
