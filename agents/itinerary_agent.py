"""
Itinerary Architect Agent — Specialized CrewAI agent for building
day-by-day travel itineraries.

This agent synthesizes flight and hotel data with local attraction
knowledge to create comprehensive, personalized travel plans.
"""

import json
import random

from crewai import Agent

try:
    from crewai.tools import tool as crewai_tool
except ImportError:
    from crewai_tools import tool as crewai_tool


ATTRACTIONS_DB = {
    "paris": [
        "Eiffel Tower", "Louvre Museum", "Notre-Dame Cathedral",
        "Champs-Elysees", "Montmartre & Sacre-Coeur", "Seine River Cruise",
        "Musee d'Orsay", "Palace of Versailles", "Luxembourg Gardens",
    ],
    "london": [
        "Tower of London", "British Museum", "Buckingham Palace",
        "London Eye", "Westminster Abbey", "Camden Market",
        "Hyde Park", "Borough Market", "Thames River Walk",
    ],
    "tokyo": [
        "Senso-ji Temple", "Shibuya Crossing", "Meiji Shrine",
        "Tsukiji Outer Market", "Akihabara", "Shinjuku Gyoen",
        "Tokyo Skytree", "Harajuku", "Ueno Park",
    ],
    "new york": [
        "Statue of Liberty", "Central Park", "Times Square",
        "Metropolitan Museum of Art", "Brooklyn Bridge", "Broadway Show",
        "Empire State Building", "High Line", "Grand Central Terminal",
    ],
    "default": [
        "City Center Walking Tour", "Local Food Market Visit",
        "Historical District Exploration", "Museum & Art Gallery Day",
        "Nature Park or Botanical Garden", "Local Cuisine Cooking Class",
        "Sunset Viewpoint Experience", "Cultural Heritage Site",
    ],
}

RESTAURANT_TYPES = [
    "Local Street Food", "Fine Dining", "Traditional Cuisine",
    "Waterfront Restaurant", "Rooftop Bar & Grill", "Cafe & Bakery",
    "Farm-to-Table Bistro", "Night Market Stalls",
]


@crewai_tool
def build_itinerary(query: str) -> str:
    """Build a day-by-day itinerary for a destination. Input should be a JSON string
    with keys: destination, num_days, interests (comma-separated), budget."""
    try:
        params = json.loads(query)
    except json.JSONDecodeError:
        params = {
            "destination": "London",
            "num_days": 3,
            "interests": "culture,food,history",
            "budget": "moderate",
        }

    destination = params.get("destination", "London").lower()
    num_days = min(int(params.get("num_days", 3)), 7)
    interests = params.get("interests", "culture,food,history")
    if isinstance(interests, str):
        interests = [i.strip() for i in interests.split(",")]

    attractions = ATTRACTIONS_DB.get(destination, ATTRACTIONS_DB["default"])
    random.shuffle(attractions)

    itinerary = []
    for day in range(1, num_days + 1):
        day_attractions = attractions[(day - 1) * 3 : day * 3]
        if not day_attractions:
            day_attractions = random.sample(ATTRACTIONS_DB["default"], 3)

        itinerary.append({
            "day": day,
            "theme": f"Day {day}: {random.choice(['Discovery', 'Adventure', 'Culture', 'Exploration', 'Leisure'])}",
            "morning": {
                "activity": day_attractions[0] if len(day_attractions) > 0 else "Free morning",
                "time": "09:00 - 12:00",
                "tip": f"Arrive early to avoid crowds at {day_attractions[0]}" if day_attractions else "",
            },
            "afternoon": {
                "activity": day_attractions[1] if len(day_attractions) > 1 else "Explore the neighborhood",
                "time": "13:00 - 17:00",
                "tip": "Take a break at a local cafe between visits",
            },
            "evening": {
                "activity": day_attractions[2] if len(day_attractions) > 2 else "Sunset walk",
                "time": "18:00 - 21:00",
                "tip": "Perfect time for photos with golden hour lighting",
            },
            "dining": {
                "lunch": random.choice(RESTAURANT_TYPES),
                "dinner": random.choice(RESTAURANT_TYPES),
            },
        })

    return json.dumps(itinerary, indent=2)


def create_itinerary_agent(llm=None) -> Agent:
    """Create and return the Itinerary Architect agent."""
    kwargs = {
        "role": "Itinerary Architect",
        "goal": (
            "Create comprehensive, day-by-day travel itineraries that maximize "
            "the traveler's experience. Combine top attractions, local hidden gems, "
            "dining recommendations, and practical travel tips into a seamless plan."
        ),
        "backstory": (
            "You are a master travel planner and storyteller who has crafted over "
            "10,000 personalized itineraries for travelers worldwide. You have an "
            "extraordinary ability to weave together cultural experiences, culinary "
            "adventures, and must-see landmarks into perfectly paced journeys. "
            "Your itineraries are legendary for their balance of exploration and "
            "relaxation, always leaving travelers with unforgettable memories."
        ),
        "tools": [build_itinerary],
        "verbose": True,
        "allow_delegation": False,
    }
    if llm:
        kwargs["llm"] = llm
    return Agent(**kwargs)
