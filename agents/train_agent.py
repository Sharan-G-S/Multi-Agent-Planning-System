"""
Indian Railways Agent — Specialized CrewAI agent for searching
train routes across India's vast railway network.

India has one of the world's largest railway systems with over
13,000 trains running daily. This agent provides comprehensive
train search with IRCTC-style data including train classes,
pantry availability, and pricing in INR.

Train assignments are route-aware:
  - Rajdhani Express only runs to/from Delhi
  - Shatabdi / Vande Bharat on specific corridors
  - Nilgiri Mountain Railway for Ooty ↔ Mettupalayam
  - Hill stations without mainline access return helpful guidance
"""

import json
import random

from crewai import Agent

try:
    from crewai.tools import tool as crewai_tool
except ImportError:
    from crewai_tools import tool as crewai_tool


# ─── Indian Railway Station Data ───

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
    "cochin": {"code": "ERS", "name": "Ernakulam Junction", "zone": "Southern"},
    "amritsar": {"code": "ASR", "name": "Amritsar Junction", "zone": "Northern"},
    "patna": {"code": "PNBE", "name": "Patna Junction", "zone": "East Central"},
    "bhopal": {"code": "BPL", "name": "Bhopal Junction", "zone": "West Central"},
    "coimbatore": {"code": "CBE", "name": "Coimbatore Junction", "zone": "Southern"},
    "mysore": {"code": "MYS", "name": "Mysuru Junction", "zone": "South Western"},
    "mysuru": {"code": "MYS", "name": "Mysuru Junction", "zone": "South Western"},
    "thiruvananthapuram": {"code": "TVC", "name": "Trivandrum Central", "zone": "Southern"},
    "trivandrum": {"code": "TVC", "name": "Trivandrum Central", "zone": "Southern"},
    "udaipur": {"code": "UDZ", "name": "Udaipur City", "zone": "North Western"},
    "jodhpur": {"code": "JU", "name": "Jodhpur Junction", "zone": "North Western"},
    "chandigarh": {"code": "CDG", "name": "Chandigarh Junction", "zone": "Northern"},
    "indore": {"code": "INDB", "name": "Indore Junction", "zone": "Western"},
    "visakhapatnam": {"code": "VSKP", "name": "Visakhapatnam", "zone": "East Coast"},
    "vizag": {"code": "VSKP", "name": "Visakhapatnam", "zone": "East Coast"},
    "madurai": {"code": "MDU", "name": "Madurai Junction", "zone": "Southern"},
    "dehradun": {"code": "DDN", "name": "Dehradun", "zone": "Northern"},
    "mettupalayam": {"code": "MTP", "name": "Mettupalayam", "zone": "Southern"},
    "salem": {"code": "SA", "name": "Salem Junction", "zone": "Southern"},
    "erode": {"code": "ED", "name": "Erode Junction", "zone": "Southern"},
    "trichy": {"code": "TPJ", "name": "Tiruchirappalli Jn", "zone": "Southern"},
    "tiruchirappalli": {"code": "TPJ", "name": "Tiruchirappalli Jn", "zone": "Southern"},
    "rameswaram": {"code": "RMM", "name": "Rameswaram", "zone": "Southern"},
    "kanyakumari": {"code": "CAPE", "name": "Kanyakumari", "zone": "Southern"},
    "pondicherry": {"code": "PDY", "name": "Puducherry", "zone": "Southern"},
    "puducherry": {"code": "PDY", "name": "Puducherry", "zone": "Southern"},
    "nagpur": {"code": "NGP", "name": "Nagpur Junction", "zone": "Central"},
    "ranchi": {"code": "RNC", "name": "Ranchi Junction", "zone": "South Eastern"},
    "bhubaneswar": {"code": "BBS", "name": "Bhubaneswar", "zone": "East Coast"},
    "guwahati": {"code": "GHY", "name": "Guwahati", "zone": "NF Railway"},
    "shimla": {"code": "SML", "name": "Shimla", "zone": "Northern"},
    "jammu": {"code": "JAT", "name": "Jammu Tawi", "zone": "Northern"},
}

# Cities that do NOT have mainline railway stations
NO_RAIL_CITIES = {
    "ooty": {"nearest": "mettupalayam", "note": "Ooty has no mainline station. The Nilgiri Mountain Railway (UNESCO heritage) runs from Mettupalayam to Ooty (46 km, ~5 hrs). Take a train to Mettupalayam/Coimbatore first."},
    "kodaikanal": {"nearest": "kodai road", "note": "Kodaikanal has no railway station. The nearest station is Kodai Road (80 km away). Take a train to Kodai Road and then a bus/taxi to Kodaikanal."},
    "munnar": {"nearest": "aluva", "note": "Munnar has no railway station. The nearest stations are Aluva/Ernakulam (130 km). Take a train to Kochi/Ernakulam and then a bus/taxi."},
    "wayanad": {"nearest": "kozhikode", "note": "Wayanad has no direct rail access. The nearest station is Kozhikode/Calicut (85 km). Take a train to Kozhikode and then a bus/taxi."},
    "alleppey": {"nearest": "alleppey", "note": "Alleppey (Alappuzha) has a railway station with limited trains."},
    "manali": {"nearest": "chandigarh", "note": "Manali has no railway station. The nearest major station is Chandigarh (310 km) or Ambala. Take a train to Chandigarh and then a bus."},
    "leh": {"nearest": "jammu", "note": "Leh has no railway station. The nearest station is Jammu Tawi (700 km). Most travelers fly to Leh or take a road trip from Manali/Srinagar."},
    "srinagar": {"nearest": "jammu", "note": "Srinagar's railway (Banihal) has limited connectivity. Most travelers take a train to Jammu Tawi and then road transport."},
    "darjeeling": {"nearest": "new jalpaiguri", "note": "Darjeeling has the Darjeeling Himalayan Railway (toy train) from New Jalpaiguri/Siliguri. Take a mainline train to NJP first."},
    "gangtok": {"nearest": "new jalpaiguri", "note": "Gangtok has no railway station. The nearest station is New Jalpaiguri (125 km). Take a train to NJP and a taxi/shared jeep."},
}


# ─── Route-Aware Train Definitions ───

# Trains that ONLY run to/from Delhi (NDLS)
DELHI_ONLY_TRAINS = [
    {"name": "Rajdhani Express", "type": "Superfast", "speed": "Premium", "pantry": True},
    {"name": "Duronto Express", "type": "Non-Stop", "speed": "Premium", "pantry": True},
    {"name": "Sampark Kranti Express", "type": "Superfast", "speed": "Standard", "pantry": True},
    {"name": "Garib Rath Express", "type": "Superfast", "speed": "Standard", "pantry": False},
]

# Shatabdi / Vande Bharat corridors (set of city pairs)
SHATABDI_VANDE_BHARAT_CORRIDORS = {
    frozenset({"delhi", "chandigarh"}),
    frozenset({"delhi", "amritsar"}),
    frozenset({"delhi", "lucknow"}),
    frozenset({"delhi", "varanasi"}),
    frozenset({"delhi", "dehradun"}),
    frozenset({"delhi", "jaipur"}),
    frozenset({"delhi", "agra"}),
    frozenset({"delhi", "bhopal"}),
    frozenset({"chennai", "bangalore"}),
    frozenset({"chennai", "bengaluru"}),
    frozenset({"chennai", "mysore"}),
    frozenset({"chennai", "mysuru"}),
    frozenset({"mumbai", "ahmedabad"}),
    frozenset({"mumbai", "goa"}),
    frozenset({"kolkata", "patna"}),
    frozenset({"chennai", "coimbatore"}),
    frozenset({"bangalore", "mysore"}),
    frozenset({"bangalore", "mysuru"}),
    frozenset({"hyderabad", "visakhapatnam"}),
    frozenset({"hyderabad", "vizag"}),
}

SHATABDI_TRAINS = [
    {"name": "Shatabdi Express", "type": "Superfast", "speed": "Premium", "pantry": True},
    {"name": "Vande Bharat Express", "type": "Semi-High Speed", "speed": "Premium", "pantry": True},
    {"name": "Jan Shatabdi Express", "type": "Superfast", "speed": "Standard", "pantry": False},
]

# Gatimaan only on Delhi-Agra
GATIMAAN_CORRIDOR = frozenset({"delhi", "agra"})

# Tejas corridors
TEJAS_CORRIDORS = {
    frozenset({"mumbai", "goa"}),
    frozenset({"mumbai", "ahmedabad"}),
    frozenset({"delhi", "lucknow"}),
    frozenset({"chennai", "madurai"}),
}

# Nilgiri Mountain Railway
NMR_CORRIDOR = frozenset({"mettupalayam", "ooty"})
NMR_CORRIDOR_CBE = frozenset({"coimbatore", "ooty"})

# Generic trains for all other routes
GENERIC_TRAINS = [
    {"name": "Superfast Express", "type": "Superfast", "speed": "Standard", "pantry": True},
    {"name": "Express", "type": "Mail/Express", "speed": "Standard", "pantry": False},
    {"name": "Mail Express", "type": "Mail/Express", "speed": "Standard", "pantry": False},
    {"name": "Intercity Express", "type": "Intercity", "speed": "Standard", "pantry": False},
    {"name": "Humsafar Express", "type": "Superfast", "speed": "Standard", "pantry": True},
    {"name": "Weekly Express", "type": "Mail/Express", "speed": "Standard", "pantry": True},
]


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
    ("delhi", "bhopal"): 700,
    ("delhi", "hyderabad"): 1550,
    ("delhi", "ahmedabad"): 940,
    ("mumbai", "pune"): 192,
    ("mumbai", "goa"): 588,
    ("mumbai", "ahmedabad"): 524,
    ("mumbai", "bangalore"): 984,
    ("mumbai", "chennai"): 1330,
    ("mumbai", "hyderabad"): 711,
    ("mumbai", "nagpur"): 840,
    ("chennai", "bangalore"): 346,
    ("chennai", "bengaluru"): 346,
    ("chennai", "hyderabad"): 627,
    ("chennai", "kochi"): 690,
    ("chennai", "coimbatore"): 507,
    ("chennai", "madurai"): 460,
    ("chennai", "trichy"): 330,
    ("chennai", "mysore"): 480,
    ("chennai", "mysuru"): 480,
    ("chennai", "salem"): 340,
    ("bangalore", "hyderabad"): 570,
    ("bangalore", "mysore"): 145,
    ("bangalore", "mysuru"): 145,
    ("bangalore", "goa"): 560,
    ("bangalore", "kochi"): 540,
    ("bangalore", "coimbatore"): 370,
    ("kolkata", "patna"): 530,
    ("kolkata", "varanasi"): 680,
    ("kolkata", "bhubaneswar"): 440,
    ("kolkata", "guwahati"): 1080,
    ("jaipur", "udaipur"): 395,
    ("jaipur", "jodhpur"): 340,
    ("hyderabad", "visakhapatnam"): 625,
    ("coimbatore", "madurai"): 210,
    ("coimbatore", "kochi"): 190,
    ("coimbatore", "mettupalayam"): 40,
    ("coimbatore", "salem"): 165,
    ("coimbatore", "erode"): 105,
    ("coimbatore", "trichy"): 210,
    ("madurai", "trichy"): 140,
    ("madurai", "rameswaram"): 170,
    ("madurai", "kanyakumari"): 240,
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


def _get_distance(origin: str, destination: str) -> int:
    """Get approximate distance between two cities."""
    o, d = _normalize_city(origin), _normalize_city(destination)
    dist = CITY_DISTANCES.get((o, d)) or CITY_DISTANCES.get((d, o))
    if dist:
        return dist
    return random.randint(400, 1200)


def _get_station(city: str) -> dict:
    """Get station info for a city."""
    return INDIAN_STATIONS.get(
        city.lower().strip(),
        {"code": city[:3].upper(), "name": city.title(), "zone": "Unknown"}
    )


def _get_trains_for_route(origin: str, destination: str) -> list:
    """Select trains that are realistic for a given route."""
    o = _normalize_city(origin)
    d = _normalize_city(destination)
    route_pair = frozenset({o, d})

    available_trains = []

    # Rajdhani / Duronto / Sampark Kranti — only if one end is Delhi
    if "delhi" in (o, d):
        available_trains.extend(DELHI_ONLY_TRAINS)

    # Gatimaan — Delhi-Agra only
    if route_pair == GATIMAAN_CORRIDOR:
        available_trains.append(
            {"name": "Gatimaan Express", "type": "Semi-High Speed", "speed": "Premium", "pantry": True}
        )

    # Shatabdi / Vande Bharat / Jan Shatabdi — specific corridors
    if route_pair in SHATABDI_VANDE_BHARAT_CORRIDORS:
        available_trains.extend(SHATABDI_TRAINS)

    # Tejas — specific corridors
    if route_pair in TEJAS_CORRIDORS:
        available_trains.append(
            {"name": "Tejas Express", "type": "Premium", "speed": "Premium", "pantry": True}
        )

    # Always add generic trains (every route has some Express/Mail trains)
    available_trains.extend(GENERIC_TRAINS)

    return available_trains


def _generate_nmr_train(origin: str, destination: str, date: str) -> list:
    """Generate Nilgiri Mountain Railway data (Mettupalayam ↔ Ooty)."""
    origin_station = _get_station(origin)
    dest_station = {"code": "UAM", "name": "Udagamandalam (Ooty)", "zone": "Southern"}
    if _normalize_city(origin) == "ooty":
        origin_station = dest_station
        dest_station = _get_station(destination)

    return [{
        "train_name": "Nilgiri Mountain Railway",
        "train_number": "56136",
        "train_type": "Heritage / Narrow Gauge",
        "origin_station": origin_station["name"],
        "origin_code": origin_station.get("code", origin[:3].upper()),
        "destination_station": dest_station["name"],
        "destination_code": dest_station.get("code", destination[:3].upper()),
        "departure_time": "07:10",
        "arrival_time": "12:15",
        "duration": "5h 5m",
        "distance_km": 46,
        "class": "First Class / Second Class",
        "class_code": "FC",
        "fare_inr": 250,
        "availability": "Available",
        "pantry": False,
        "runs_on": "Daily",
        "date": date,
        "zone": "Southern",
        "note": "UNESCO World Heritage rack railway. Scenic journey through tea plantations and 16 tunnels.",
    }]


def _generate_mock_trains(origin: str, destination: str, date: str, budget: str) -> list:
    """Generate realistic Indian Railways train data with INR pricing."""
    o = _normalize_city(origin)
    d = _normalize_city(destination)
    route_pair = frozenset({o, d})

    # ── Handle cities without mainline rail ──
    if o in NO_RAIL_CITIES:
        info = NO_RAIL_CITIES[o]
        # Special: Ooty ↔ Mettupalayam/Coimbatore → show NMR
        if o == "ooty" and d in ("mettupalayam", "coimbatore"):
            return _generate_nmr_train(origin, destination, date)
        return [{
            "train_name": "No Direct Trains",
            "train_number": "—",
            "train_type": "Info",
            "origin_station": origin.title(),
            "origin_code": "—",
            "destination_station": destination.title(),
            "destination_code": "—",
            "departure_time": "—",
            "arrival_time": "—",
            "duration": "—",
            "distance_km": 0,
            "class": "—",
            "class_code": "—",
            "fare_inr": 0,
            "availability": "N/A",
            "pantry": False,
            "runs_on": "—",
            "date": date,
            "zone": "—",
            "note": info["note"],
        }]

    if d in NO_RAIL_CITIES:
        info = NO_RAIL_CITIES[d]
        # Special: Coimbatore/Mettupalayam → Ooty → show NMR
        if d == "ooty" and o in ("mettupalayam", "coimbatore"):
            return _generate_nmr_train(origin, destination, date)
        return [{
            "train_name": "No Direct Trains",
            "train_number": "—",
            "train_type": "Info",
            "origin_station": origin.title(),
            "origin_code": "—",
            "destination_station": destination.title(),
            "destination_code": "—",
            "departure_time": "—",
            "arrival_time": "—",
            "duration": "—",
            "distance_km": 0,
            "class": "—",
            "class_code": "—",
            "fare_inr": 0,
            "availability": "N/A",
            "pantry": False,
            "runs_on": "—",
            "date": date,
            "zone": "—",
            "note": info["note"],
        }]

    # ── Normal mainline route ──
    distance = _get_distance(origin, destination)
    origin_station = _get_station(origin)
    dest_station = _get_station(destination)

    classes = TRAIN_CLASSES.get(budget.lower(), TRAIN_CLASSES["moderate"])
    route_trains = _get_trains_for_route(origin, destination)

    trains = []
    num_trains = random.randint(3, 5)

    # Pick trains without duplicate names
    used_names = set()
    for _ in range(num_trains):
        # Try to pick a unique train
        attempts = 0
        while attempts < 15:
            template = random.choice(route_trains)
            if template["name"] not in used_names:
                break
            attempts += 1
        used_names.add(template["name"])

        train_class = random.choice(classes)

        # Calculate fare in INR
        base_fare = distance * BASE_FARE_PER_KM * train_class["price_mult"]
        # Premium trains cost more
        if template["speed"] == "Premium":
            base_fare *= 1.4
        fare_inr = round(base_fare + random.uniform(-50, 200), 0)
        fare_inr = max(fare_inr, 150)

        # Duration based on distance & train speed
        if template["speed"] == "Premium":
            speed_kmh = random.choice([80, 90, 110, 130])
        else:
            speed_kmh = random.choice([50, 55, 60, 70])
        duration_hrs = distance / speed_kmh
        hours = int(duration_hrs)
        mins = int((duration_hrs - hours) * 60)

        departure_hour = random.randint(4, 23)
        arrival_hour = (departure_hour + hours) % 24

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
