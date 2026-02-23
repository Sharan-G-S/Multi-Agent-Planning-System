"""
Flight Search Agent — Specialized CrewAI agent for finding optimal flights.

Uses realistic Indian airline data. Handles cities without airports
(Ooty, Kodaikanal, Munnar, etc.) by returning helpful guidance.
"""

import json
import random

from crewai import Agent

try:
    from crewai.tools import tool as crewai_tool
except ImportError:
    from crewai_tools import tool as crewai_tool


# ─── Indian Airlines ───

AIRLINES = [
    {"name": "IndiGo", "code": "6E", "rating": 4.2, "type": "LCC"},
    {"name": "Air India", "code": "AI", "rating": 4.0, "type": "FSC"},
    {"name": "Air India Express", "code": "IX", "rating": 3.8, "type": "LCC"},
    {"name": "Vistara", "code": "UK", "rating": 4.5, "type": "FSC"},
    {"name": "SpiceJet", "code": "SG", "rating": 3.7, "type": "LCC"},
    {"name": "Akasa Air", "code": "QP", "rating": 4.1, "type": "LCC"},
    {"name": "Alliance Air", "code": "9I", "rating": 3.5, "type": "Regional"},
    {"name": "Star Air", "code": "S5", "rating": 3.6, "type": "Regional"},
]

# Airlines filtered by budget
BUDGET_AIRLINES = [a for a in AIRLINES if a["type"] == "LCC"]
PREMIUM_AIRLINES = [a for a in AIRLINES if a["type"] == "FSC"]
ALL_MAINLINE_AIRLINES = [a for a in AIRLINES if a["type"] in ("LCC", "FSC")]


# ─── Airport Data ───

AIRPORTS = {
    "delhi": {"code": "DEL", "name": "Indira Gandhi International Airport"},
    "new delhi": {"code": "DEL", "name": "Indira Gandhi International Airport"},
    "mumbai": {"code": "BOM", "name": "Chhatrapati Shivaji Maharaj International Airport"},
    "bangalore": {"code": "BLR", "name": "Kempegowda International Airport"},
    "bengaluru": {"code": "BLR", "name": "Kempegowda International Airport"},
    "chennai": {"code": "MAA", "name": "Chennai International Airport"},
    "hyderabad": {"code": "HYD", "name": "Rajiv Gandhi International Airport"},
    "kolkata": {"code": "CCU", "name": "Netaji Subhas Chandra Bose International Airport"},
    "kochi": {"code": "COK", "name": "Cochin International Airport"},
    "cochin": {"code": "COK", "name": "Cochin International Airport"},
    "goa": {"code": "GOI", "name": "Manohar International Airport"},
    "pune": {"code": "PNQ", "name": "Pune Airport"},
    "jaipur": {"code": "JAI", "name": "Jaipur International Airport"},
    "ahmedabad": {"code": "AMD", "name": "Sardar Vallabhbhai Patel International Airport"},
    "lucknow": {"code": "LKO", "name": "Chaudhary Charan Singh International Airport"},
    "varanasi": {"code": "VNS", "name": "Lal Bahadur Shastri International Airport"},
    "coimbatore": {"code": "CJB", "name": "Coimbatore International Airport"},
    "madurai": {"code": "IXM", "name": "Madurai Airport"},
    "trichy": {"code": "TRZ", "name": "Tiruchirappalli International Airport"},
    "tiruchirappalli": {"code": "TRZ", "name": "Tiruchirappalli International Airport"},
    "thiruvananthapuram": {"code": "TRV", "name": "Trivandrum International Airport"},
    "trivandrum": {"code": "TRV", "name": "Trivandrum International Airport"},
    "visakhapatnam": {"code": "VTZ", "name": "Visakhapatnam Airport"},
    "vizag": {"code": "VTZ", "name": "Visakhapatnam Airport"},
    "bhubaneswar": {"code": "BBI", "name": "Biju Patnaik International Airport"},
    "patna": {"code": "PAT", "name": "Jay Prakash Narayan International Airport"},
    "chandigarh": {"code": "IXC", "name": "Chandigarh International Airport"},
    "amritsar": {"code": "ATQ", "name": "Sri Guru Ram Dass Jee International Airport"},
    "indore": {"code": "IDR", "name": "Devi Ahilyabai Holkar Airport"},
    "bhopal": {"code": "BHO", "name": "Raja Bhoj Airport"},
    "nagpur": {"code": "NAG", "name": "Dr. Babasaheb Ambedkar International Airport"},
    "ranchi": {"code": "IXR", "name": "Birsa Munda Airport"},
    "guwahati": {"code": "GAU", "name": "Lokpriya Gopinath Bordoloi International Airport"},
    "dehradun": {"code": "DED", "name": "Jolly Grant Airport"},
    "udaipur": {"code": "UDR", "name": "Maharana Pratap Airport"},
    "jodhpur": {"code": "JDH", "name": "Jodhpur Airport"},
    "jammu": {"code": "IXJ", "name": "Jammu Airport"},
    "srinagar": {"code": "SXR", "name": "Sheikh ul-Alam International Airport"},
    "leh": {"code": "IXL", "name": "Kushok Bakula Rimpochee Airport"},
    "pondicherry": {"code": "PNY", "name": "Pondicherry Airport"},
    "puducherry": {"code": "PNY", "name": "Pondicherry Airport"},
    "salem": {"code": "SXV", "name": "Salem Airport"},
    "mysore": {"code": "MYQ", "name": "Mysore Airport"},
    "mysuru": {"code": "MYQ", "name": "Mysore Airport"},
    "tuticorin": {"code": "TCR", "name": "Tuticorin Airport"},
}

# Cities with NO airport — show helpful info
NO_AIRPORT_CITIES = {
    "ooty": "Ooty has no airport. The nearest airport is Coimbatore (CJB), about 88 km away. Take a flight to Coimbatore and then a cab/bus (2-3 hrs via Mettupalayam Ghat Road).",
    "kodaikanal": "Kodaikanal has no airport. The nearest airport is Madurai (IXM), about 120 km away. Take a flight to Madurai and then a cab/bus (3-4 hrs).",
    "munnar": "Munnar has no airport. The nearest airport is Cochin/Kochi (COK), about 130 km away. Take a flight to Kochi and then a cab (4 hrs).",
    "wayanad": "Wayanad has no airport. The nearest airport is Calicut/Kozhikode (CCJ), about 100 km away. Alternatively, fly to Mysore (MYQ) or Bangalore (BLR).",
    "manali": "Manali has no airport. The nearest airport is Kullu-Bhuntar (KUU), about 50 km away, with limited flights. Alternatively, fly to Chandigarh (IXC) and take a bus (10 hrs).",
    "darjeeling": "Darjeeling has no airport. The nearest airport is Bagdogra (IXB), about 67 km away. Take a flight to Bagdogra and then a cab (3 hrs).",
    "gangtok": "Gangtok has no airport. The nearest airport is Bagdogra (IXB), about 125 km away. Take a flight to Bagdogra and then a cab (4-5 hrs).",
    "shimla": "Shimla has a small airport (SLV) at Jubbarhatti with very limited flights. Most travelers fly to Chandigarh (IXC) and drive 4-5 hrs.",
    "alleppey": "Alleppey (Alappuzha) has no airport. The nearest airport is Cochin/Kochi (COK), about 75 km away (1.5 hrs by road).",
    "rameswaram": "Rameswaram has no airport. The nearest airport is Madurai (IXM), about 175 km away. Take a flight to Madurai and then a bus/cab (3-4 hrs).",
    "kanyakumari": "Kanyakumari has no airport. The nearest airport is Trivandrum (TRV), about 90 km away. Alternatively, Tuticorin (TCR) is 85 km.",
    "rishikesh": "Rishikesh has no airport. The nearest airport is Dehradun/Jolly Grant (DED), about 35 km away.",
    "haridwar": "Haridwar has no airport. The nearest airport is Dehradun/Jolly Grant (DED), about 40 km away.",
    "mettupalayam": "Mettupalayam has no airport. The nearest airport is Coimbatore (CJB), about 40 km away.",
    "pollachi": "Pollachi has no airport. The nearest airport is Coimbatore (CJB), about 40 km away.",
}

# Approximate flight distances (km) for duration calculation
FLIGHT_DISTANCES = {
    ("delhi", "mumbai"): 1140, ("delhi", "bangalore"): 1740, ("delhi", "chennai"): 1760,
    ("delhi", "kolkata"): 1300, ("delhi", "hyderabad"): 1260, ("delhi", "goa"): 1500,
    ("delhi", "kochi"): 2060, ("delhi", "jaipur"): 260, ("delhi", "lucknow"): 420,
    ("delhi", "varanasi"): 670, ("delhi", "coimbatore"): 1920, ("delhi", "chandigarh"): 240,
    ("delhi", "amritsar"): 400, ("delhi", "dehradun"): 230, ("delhi", "ahmedabad"): 760,
    ("delhi", "pune"): 1180, ("delhi", "srinagar"): 640, ("delhi", "leh"): 580,
    ("delhi", "bhopal"): 620, ("delhi", "indore"): 700, ("delhi", "patna"): 840,
    ("delhi", "guwahati"): 1530, ("delhi", "udaipur"): 570, ("delhi", "jodhpur"): 520,
    ("mumbai", "bangalore"): 840, ("mumbai", "chennai"): 1030, ("mumbai", "goa"): 440,
    ("mumbai", "hyderabad"): 620, ("mumbai", "kolkata"): 1650, ("mumbai", "kochi"): 1070,
    ("mumbai", "pune"): 120, ("mumbai", "ahmedabad"): 450, ("mumbai", "jaipur"): 920,
    ("mumbai", "coimbatore"): 920, ("mumbai", "delhi"): 1140,
    ("chennai", "bangalore"): 290, ("chennai", "hyderabad"): 520, ("chennai", "kolkata"): 1370,
    ("chennai", "kochi"): 530, ("chennai", "coimbatore"): 430, ("chennai", "madurai"): 430,
    ("chennai", "trichy"): 320, ("chennai", "goa"): 740,
    ("bangalore", "hyderabad"): 490, ("bangalore", "kochi"): 380, ("bangalore", "goa"): 440,
    ("bangalore", "coimbatore"): 310, ("bangalore", "madurai"): 420, ("bangalore", "chennai"): 290,
    ("bangalore", "kolkata"): 1560, ("bangalore", "mumbai"): 840,
    ("hyderabad", "visakhapatnam"): 500, ("hyderabad", "bangalore"): 490,
    ("hyderabad", "chennai"): 520, ("hyderabad", "kolkata"): 1180,
    ("kolkata", "guwahati"): 510, ("kolkata", "patna"): 470, ("kolkata", "bhubaneswar"): 390,
    ("kochi", "coimbatore"): 160, ("kochi", "madurai"): 260,
    ("coimbatore", "chennai"): 430, ("coimbatore", "bangalore"): 310, ("coimbatore", "hyderabad"): 770,
    ("coimbatore", "madurai"): 200, ("coimbatore", "delhi"): 1920,
}


def _normalize_city(city: str) -> str:
    """Normalize city name for lookups."""
    c = city.lower().strip()
    aliases = {
        "bengaluru": "bangalore", "mysuru": "mysore",
        "vizag": "visakhapatnam", "cochin": "kochi",
        "trivandrum": "thiruvananthapuram", "new delhi": "delhi",
        "tiruchirappalli": "trichy", "puducherry": "pondicherry",
    }
    return aliases.get(c, c)


def _get_flight_distance(origin: str, destination: str) -> int:
    """Get approximate flight distance between two cities."""
    o, d = _normalize_city(origin), _normalize_city(destination)
    dist = FLIGHT_DISTANCES.get((o, d)) or FLIGHT_DISTANCES.get((d, o))
    if dist:
        return dist
    return random.randint(500, 1500)


def _get_airport(city: str) -> dict:
    """Get airport info for a city."""
    return AIRPORTS.get(
        city.lower().strip(),
        {"code": city[:3].upper(), "name": f"{city.title()} Airport"}
    )


def _generate_mock_flights(origin: str, destination: str, date: str, budget: str) -> list:
    """Generate realistic mock flight data with Indian airlines."""
    o = _normalize_city(origin)
    d = _normalize_city(destination)

    # ── Handle cities without airports ──
    if o in NO_AIRPORT_CITIES:
        return [{
            "airline": "No Airport",
            "airline_code": "—",
            "airline_rating": 0,
            "flight_number": "—",
            "origin": origin.title(),
            "destination": destination.title(),
            "departure_time": "—",
            "duration": "—",
            "stops": 0,
            "stop_type": "—",
            "price_inr": 0,
            "class": "—",
            "date": date,
            "note": NO_AIRPORT_CITIES[o],
        }]

    if d in NO_AIRPORT_CITIES:
        return [{
            "airline": "No Airport",
            "airline_code": "—",
            "airline_rating": 0,
            "flight_number": "—",
            "origin": origin.title(),
            "destination": destination.title(),
            "departure_time": "—",
            "duration": "—",
            "stops": 0,
            "stop_type": "—",
            "price_inr": 0,
            "class": "—",
            "date": date,
            "note": NO_AIRPORT_CITIES[d],
        }]

    # ── Normal airport route ──
    origin_airport = _get_airport(origin)
    dest_airport = _get_airport(destination)
    flight_dist = _get_flight_distance(origin, destination)

    # Calculate realistic duration (cruise speed ~800 km/h + 30-45 min ground/taxi)
    flight_time_hrs = flight_dist / 800
    total_hrs = flight_time_hrs + random.uniform(0.5, 0.75)  # add taxi/boarding time
    duration_hours = int(total_hrs)
    duration_mins = int((total_hrs - duration_hours) * 60)
    # Round to nearest 5 min
    duration_mins = (duration_mins // 5) * 5

    budget_map = {"budget": (4500, 10000), "moderate": (7000, 18000), "luxury": (15000, 45000)}
    price_range = budget_map.get(budget.lower(), (5500, 14000))

    # Scale price by distance
    dist_factor = flight_dist / 1000  # normalize around 1000 km
    price_min = int(price_range[0] * max(0.6, dist_factor))
    price_max = int(price_range[1] * max(0.6, dist_factor))

    # Select airlines based on budget
    if budget.lower() == "luxury":
        airline_pool = PREMIUM_AIRLINES + BUDGET_AIRLINES[:1]
    elif budget.lower() == "budget":
        airline_pool = BUDGET_AIRLINES
    else:
        airline_pool = ALL_MAINLINE_AIRLINES

    flights = []
    used_airlines = set()
    for _ in range(random.randint(3, 5)):
        # Try to pick unique airlines
        attempts = 0
        while attempts < 10:
            airline = random.choice(airline_pool)
            if airline["name"] not in used_airlines or attempts > 6:
                break
            attempts += 1
        used_airlines.add(airline["name"])

        departure_hour = random.randint(5, 22)
        price = round(random.uniform(price_min, price_max), 0)
        stops = random.choices([0, 1], weights=[65, 35])[0]

        # Stops only make sense for shorter routes (connecting flights)
        if flight_dist < 400:
            stops = 0  # No connecting flights for short routes

        if stops > 0:
            price *= 0.8  # connecting flights are cheaper
            adj_hrs = duration_hours + random.randint(1, 3)
            adj_mins = duration_mins
        else:
            adj_hrs = duration_hours
            adj_mins = duration_mins

        # Flight class
        if budget.lower() == "budget":
            flight_class = "Economy"
        elif budget.lower() == "luxury":
            flight_class = random.choice(["Business", "Premium Economy"])
        else:
            flight_class = random.choice(["Economy", "Premium Economy"])

        flights.append({
            "airline": airline["name"],
            "airline_code": airline["code"],
            "airline_rating": airline["rating"],
            "flight_number": f"{airline['code']}-{random.randint(100, 999)}",
            "origin": origin_airport["code"],
            "destination": dest_airport["code"],
            "departure_time": f"{departure_hour:02d}:{random.choice(['00', '15', '30', '45'])}",
            "duration": f"{adj_hrs}h {adj_mins}m",
            "stops": stops,
            "stop_type": "Non-stop" if stops == 0 else f"{stops} stop",
            "price_inr": price,
            "class": flight_class,
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
            "origin": parts[0] if len(parts) > 0 else "Delhi",
            "destination": parts[1] if len(parts) > 1 else "Mumbai",
            "date": parts[2] if len(parts) > 2 else "2025-06-15",
            "budget": parts[3] if len(parts) > 3 else "moderate",
        }

    flights = _generate_mock_flights(
        params.get("origin", "Delhi"),
        params.get("destination", "Mumbai"),
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
            "You are a seasoned aviation expert with deep knowledge of Indian "
            "domestic airlines — IndiGo, Air India, Vistara, SpiceJet, Akasa Air, "
            "and regional carriers. You know which routes have direct flights, "
            "the best time slots to fly, and how to find the best deals. You can "
            "instantly tell a traveler whether a city has an airport and suggest "
            "the nearest alternative if it doesn't."
        ),
        "tools": [search_flights],
        "verbose": True,
        "allow_delegation": False,
    }
    if llm:
        kwargs["llm"] = llm
    return Agent(**kwargs)
