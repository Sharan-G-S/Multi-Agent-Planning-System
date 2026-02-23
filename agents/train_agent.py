"""
Indian Railways Agent — Specialized CrewAI agent for searching
train routes across India's vast railway network.

India has one of the world's largest railway systems with over
13,000 trains running daily. This agent provides comprehensive
train search with IRCTC-style data including train classes,
pantry availability, and pricing in INR.
"""

import json
import random

from crewai import Agent

try:
    from crewai.tools import tool as crewai_tool
except ImportError:
    from crewai_tools import tool as crewai_tool


# ─── Indian Railway Data ───

INDIAN_TRAINS = [
    {"name": "Rajdhani Express", "type": "Superfast", "speed": "Premium", "pantry": True},
    {"name": "Shatabdi Express", "type": "Superfast", "speed": "Premium", "pantry": True},
    {"name": "Vande Bharat Express", "type": "Semi-High Speed", "speed": "Premium", "pantry": True},
    {"name": "Duronto Express", "type": "Non-Stop", "speed": "Premium", "pantry": True},
    {"name": "Garib Rath Express", "type": "Superfast", "speed": "Standard", "pantry": False},
    {"name": "Humsafar Express", "type": "Superfast", "speed": "Standard", "pantry": True},
    {"name": "Tejas Express", "type": "Premium", "speed": "Premium", "pantry": True},
    {"name": "Jan Shatabdi Express", "type": "Superfast", "speed": "Standard", "pantry": False},
    {"name": "Sampark Kranti Express", "type": "Superfast", "speed": "Standard", "pantry": True},
    {"name": "Gatimaan Express", "type": "Semi-High Speed", "speed": "Premium", "pantry": True},
]

INDIAN_STATIONS = {
    "delhi": {"code": "NDLS", "name": "New Delhi", "zone": "Northern"},
    "new delhi": {"code": "NDLS", "name": "New Delhi", "zone": "Northern"},
    "mumbai": {"code": "CSTM", "name": "Mumbai CST", "zone": "Central"},
    "chennai": {"code": "MAS", "name": "Chennai Central", "zone": "Southern"},
    "kolkata": {"code": "HWH", "name": "Howrah Junction", "zone": "Eastern"},
    "bangalore": {"code": "SBC", "name": "KSR Bengaluru", "zone": "South Western"},
    "bengaluru": {"code": "SBC", "name": "KSR Bengaluru", "zone": "South Western"},
    "hyderabad": {"code": "SC", "name": "Secunderabad Jn", "zone": "South Central"},
    "jaipur": {"code": "JP", "name": "Jaipur Junction", "zone": "North Western"},
    "ahmedabad": {"code": "ADI", "name": "Ahmedabad Junction", "zone": "Western"},
    "pune": {"code": "PUNE", "name": "Pune Junction", "zone": "Central"},
    "lucknow": {"code": "LKO", "name": "Lucknow Charbagh", "zone": "Northern"},
    "varanasi": {"code": "BSB", "name": "Varanasi Junction", "zone": "Northern"},
    "goa": {"code": "MAO", "name": "Madgaon Junction", "zone": "South Western"},
    "agra": {"code": "AGC", "name": "Agra Cantt", "zone": "North Central"},
    "kochi": {"code": "ERS", "name": "Ernakulam Junction", "zone": "Southern"},
    "amritsar": {"code": "ASR", "name": "Amritsar Junction", "zone": "Northern"},
    "patna": {"code": "PNBE", "name": "Patna Junction", "zone": "East Central"},
    "bhopal": {"code": "BPL", "name": "Bhopal Junction", "zone": "West Central"},
    "coimbatore": {"code": "CBE", "name": "Coimbatore Junction", "zone": "Southern"},
    "mysore": {"code": "MYS", "name": "Mysuru Junction", "zone": "South Western"},
    "mysuru": {"code": "MYS", "name": "Mysuru Junction", "zone": "South Western"},
    "thiruvananthapuram": {"code": "TVC", "name": "Trivandrum Central", "zone": "Southern"},
    "udaipur": {"code": "UDZ", "name": "Udaipur City", "zone": "North Western"},
    "jodhpur": {"code": "JU", "name": "Jodhpur Junction", "zone": "North Western"},
    "chandigarh": {"code": "CDG", "name": "Chandigarh Junction", "zone": "Northern"},
    "indore": {"code": "INDB", "name": "Indore Junction", "zone": "Western"},
    "visakhapatnam": {"code": "VSKP", "name": "Visakhapatnam", "zone": "East Coast"},
    "madurai": {"code": "MDU", "name": "Madurai Junction", "zone": "Southern"},
    "dehradun": {"code": "DDN", "name": "Dehradun", "zone": "Northern"},
}

TRAIN_CLASSES = {
    "budget": [
        {"code": "SL", "name": "Sleeper Class", "price_mult": 1.0},
        {"code": "3A", "name": "AC 3-Tier", "price_mult": 2.5},
    ],
    "moderate": [
        {"code": "3A", "name": "AC 3-Tier", "price_mult": 2.5},
        {"code": "2A", "name": "AC 2-Tier", "price_mult": 3.8},
        {"code": "CC", "name": "AC Chair Car", "price_mult": 2.0},
    ],
    "luxury": [
        {"code": "2A", "name": "AC 2-Tier", "price_mult": 3.8},
        {"code": "1A", "name": "AC First Class", "price_mult": 6.0},
        {"code": "EC", "name": "Executive Chair Car", "price_mult": 4.5},
    ],
}

# Base fare per km in INR (approx)
BASE_FARE_PER_KM = 0.55

# Approximate distances between major cities (km)
CITY_DISTANCES = {
    ("delhi", "mumbai"): 1384,
    ("delhi", "kolkata"): 1530,
    ("delhi", "chennai"): 2175,
    ("delhi", "bangalore"): 2150,
    ("delhi", "jaipur"): 310,
    ("delhi", "agra"): 230,
    ("delhi", "varanasi"): 820,
    ("delhi", "lucknow"): 555,
    ("delhi", "amritsar"): 450,
    ("delhi", "chandigarh"): 245,
    ("delhi", "dehradun"): 255,
    ("mumbai", "pune"): 192,
    ("mumbai", "goa"): 588,
    ("mumbai", "ahmedabad"): 524,
    ("mumbai", "bangalore"): 984,
    ("mumbai", "chennai"): 1330,
    ("mumbai", "hyderabad"): 711,
    ("chennai", "bangalore"): 346,
    ("chennai", "hyderabad"): 627,
    ("chennai", "kochi"): 690,
    ("chennai", "coimbatore"): 507,
    ("chennai", "madurai"): 460,
    ("bangalore", "hyderabad"): 570,
    ("bangalore", "mysore"): 145,
    ("bangalore", "goa"): 560,
    ("bangalore", "kochi"): 540,
    ("kolkata", "patna"): 530,
    ("kolkata", "varanasi"): 680,
    ("jaipur", "udaipur"): 395,
    ("jaipur", "jodhpur"): 340,
    ("hyderabad", "visakhapatnam"): 625,
}


def _get_distance(origin: str, destination: str) -> int:
    """Get approximate distance between two cities."""
    o, d = origin.lower(), destination.lower()
    dist = CITY_DISTANCES.get((o, d)) or CITY_DISTANCES.get((d, o))
    if dist:
        return dist
    # Default distance for unknown routes
    return random.randint(400, 1200)


def _get_station(city: str) -> dict:
    """Get station info for a city."""
    return INDIAN_STATIONS.get(
        city.lower(),
        {"code": city[:3].upper(), "name": city.title(), "zone": "Unknown"}
    )


def _generate_mock_trains(origin: str, destination: str, date: str, budget: str) -> list:
    """Generate realistic Indian Railways train data with INR pricing."""
    distance = _get_distance(origin, destination)
    origin_station = _get_station(origin)
    dest_station = _get_station(destination)

    classes = TRAIN_CLASSES.get(budget.lower(), TRAIN_CLASSES["moderate"])

    trains = []
    num_trains = random.randint(3, 6)

    for _ in range(num_trains):
        template = random.choice(INDIAN_TRAINS)
        train_class = random.choice(classes)

        # Calculate fare in INR
        base_fare = distance * BASE_FARE_PER_KM * train_class["price_mult"]
        fare_inr = round(base_fare + random.uniform(-50, 200), 0)
        fare_inr = max(fare_inr, 150)  # Minimum fare

        # Duration based on distance & train speed
        speed_kmh = random.choice([60, 70, 80, 90, 110, 130]) if template["speed"] == "Premium" else random.choice([45, 55, 60, 70])
        duration_hrs = distance / speed_kmh
        hours = int(duration_hrs)
        mins = int((duration_hrs - hours) * 60)

        departure_hour = random.randint(4, 23)
        arrival_hour = (departure_hour + hours) % 24

        # Availability
        avail_statuses = ["Available", "RAC", "Waitlist", "Available", "Available"]

        train_number = f"{random.randint(10000, 99999)}"

        trains.append({
            "train_name": template["name"],
            "train_number": train_number,
            "train_type": template["type"],
            "origin_station": origin_station["name"],
            "origin_code": origin_station["code"],
            "destination_station": dest_station["name"],
            "destination_code": dest_station["code"],
            "departure_time": f"{departure_hour:02d}:{random.choice(['00', '10', '15', '25', '30', '40', '45', '55'])}",
            "arrival_time": f"{arrival_hour:02d}:{random.choice(['00', '10', '15', '25', '30', '40', '45', '55'])}",
            "duration": f"{hours}h {mins}m",
            "distance_km": distance,
            "class": train_class["name"],
            "class_code": train_class["code"],
            "fare_inr": fare_inr,
            "availability": random.choice(avail_statuses),
            "pantry": template["pantry"],
            "runs_on": random.choice(["Daily", "Mon/Wed/Fri", "Tue/Thu/Sat", "Daily except Sun"]),
            "date": date,
            "zone": origin_station["zone"],
        })

    trains.sort(key=lambda x: x["fare_inr"])
    return trains


@crewai_tool
def search_trains(query: str) -> str:
    """Search for Indian Railways trains between cities. Input should be a JSON string
    with keys: origin, destination, date, budget (budget/moderate/luxury).
    Returns train options with Indian Railways classes and pricing in INR."""
    try:
        params = json.loads(query)
    except json.JSONDecodeError:
        parts = query.replace(",", " ").split()
        params = {
            "origin": parts[0] if len(parts) > 0 else "Delhi",
            "destination": parts[1] if len(parts) > 1 else "Mumbai",
            "date": parts[2] if len(parts) > 2 else "2025-06-15",
            "budget": parts[3] if len(parts) > 3 else "moderate",
        }

    trains = _generate_mock_trains(
        params.get("origin", "Delhi"),
        params.get("destination", "Mumbai"),
        params.get("date", "2025-06-15"),
        params.get("budget", "moderate"),
    )
    return json.dumps(trains, indent=2)


def create_train_agent(llm=None) -> Agent:
    """Create and return the Indian Railways Specialist agent."""
    kwargs = {
        "role": "Indian Railways Travel Specialist",
        "goal": (
            "Find the best Indian Railways train options for travelers within India. "
            "Compare train types (Rajdhani, Shatabdi, Vande Bharat, Duronto, etc.), "
            "coach classes (Sleeper, AC 3-Tier, AC 2-Tier, First Class), fares in INR, "
            "travel times, and availability status to recommend the optimal choices."
        ),
        "backstory": (
            "You are a veteran Indian Railways expert with deep knowledge of the "
            "entire Indian rail network spanning over 68,000 km. You know every "
            "major route, the best trains for each corridor, tatkal booking tricks, "
            "and which class offers the best value. From the Rajdhani Express rushing "
            "through the Deccan Plateau to the Vande Bharat zipping between Delhi and "
            "Varanasi, you can recommend the perfect train for any journey across India. "
            "You also understand IRCTC booking patterns and can advise on ticket availability."
        ),
        "tools": [search_trains],
        "verbose": True,
        "allow_delegation": False,
    }
    if llm:
        kwargs["llm"] = llm
    return Agent(**kwargs)
