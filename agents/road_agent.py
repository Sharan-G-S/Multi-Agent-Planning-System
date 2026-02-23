"""
Road Travel Agent — Specialized CrewAI agent for intercity road travel
across India, with a focus on Tamil Nadu and South India.

Covers intercity buses (government TNSTC/KSRTC/SETC and private operators
like KPN, SRS, Parveen), cabs (Ola, Uber, local operators), and
self-drive rental options with INR pricing.
"""

import json
import random

from crewai import Agent

try:
    from crewai.tools import tool as crewai_tool
except ImportError:
    from crewai_tools import tool as crewai_tool


# ─── Bus Operators ───

GOVERNMENT_OPERATORS = [
    {"name": "TNSTC", "full": "Tamil Nadu State Transport", "type": "Government"},
    {"name": "SETC", "full": "State Express Transport", "type": "Government"},
    {"name": "KSRTC", "full": "Kerala State RTC", "type": "Government"},
    {"name": "KSRTC-KA", "full": "Karnataka State RTC", "type": "Government"},
    {"name": "APSRTC", "full": "Andhra Pradesh State RTC", "type": "Government"},
    {"name": "TSRTC", "full": "Telangana State RTC", "type": "Government"},
]

PRIVATE_OPERATORS = [
    {"name": "KPN Travels", "type": "Private", "tier": "Premium"},
    {"name": "SRS Travels", "type": "Private", "tier": "Premium"},
    {"name": "Parveen Travels", "type": "Private", "tier": "Premium"},
    {"name": "SRM Travels", "type": "Private", "tier": "Standard"},
    {"name": "Kallada Travels", "type": "Private", "tier": "Premium"},
    {"name": "Orange Tours", "type": "Private", "tier": "Standard"},
    {"name": "VRL Travels", "type": "Private", "tier": "Premium"},
    {"name": "IntrCity SmartBus", "type": "Private", "tier": "Premium"},
    {"name": "Jabbar Travels", "type": "Private", "tier": "Standard"},
    {"name": "Rajesh Transports", "type": "Private", "tier": "Standard"},
]

CAB_PROVIDERS = [
    {"name": "Ola Outstation", "type": "Cab", "tier": "Premium"},
    {"name": "Uber Intercity", "type": "Cab", "tier": "Premium"},
    {"name": "Savaari Car Rental", "type": "Cab", "tier": "Standard"},
    {"name": "IntrCity Ryde", "type": "Cab", "tier": "Premium"},
    {"name": "Zoomcar (Self-drive)", "type": "Self-Drive", "tier": "Premium"},
]

BUS_TYPES = {
    "budget": [
        {"type": "Non-AC Seater", "mult": 1.0},
        {"type": "AC Seater", "mult": 1.6},
        {"type": "Non-AC Sleeper", "mult": 1.3},
    ],
    "moderate": [
        {"type": "AC Seater", "mult": 1.6},
        {"type": "AC Sleeper", "mult": 2.2},
        {"type": "Multi-Axle AC Semi-Sleeper", "mult": 2.5},
    ],
    "luxury": [
        {"type": "Volvo AC Multi-Axle", "mult": 3.0},
        {"type": "Mercedes AC Sleeper", "mult": 3.5},
        {"type": "Scania AC Multi-Axle", "mult": 3.8},
    ],
}

# Base fare per km in INR for bus
BUS_BASE_FARE_PER_KM = 0.80

# Cab fare per km
CAB_BASE_FARE_PER_KM = 10.0

# ─── Road Distances (km) — South India focus ───
ROAD_DISTANCES = {
    # ─── Coimbatore routes (Tamil Nadu hub) ───
    ("coimbatore", "chennai"): 505,
    ("coimbatore", "bangalore"): 365,
    ("coimbatore", "bengaluru"): 365,
    ("coimbatore", "madurai"): 218,
    ("coimbatore", "trichy"): 220,
    ("coimbatore", "salem"): 165,
    ("coimbatore", "erode"): 100,
    ("coimbatore", "tiruppur"): 50,
    ("coimbatore", "ooty"): 86,
    ("coimbatore", "munnar"): 160,
    ("coimbatore", "kochi"): 195,
    ("coimbatore", "palakkad"): 55,
    ("coimbatore", "mysore"): 220,
    ("coimbatore", "mysuru"): 220,
    ("coimbatore", "pollachi"): 40,
    ("coimbatore", "kodaikanal"): 175,
    ("coimbatore", "thanjavur"): 305,
    ("coimbatore", "dindigul"): 168,
    ("coimbatore", "pondicherry"): 410,
    ("coimbatore", "puducherry"): 410,
    ("coimbatore", "thiruvananthapuram"): 430,
    ("coimbatore", "hyderabad"): 790,
    ("coimbatore", "goa"): 870,

    # ─── Other Tamil Nadu routes ───
    ("chennai", "madurai"): 462,
    ("chennai", "trichy"): 330,
    ("chennai", "salem"): 340,
    ("chennai", "pondicherry"): 155,
    ("chennai", "puducherry"): 155,
    ("chennai", "thanjavur"): 340,
    ("chennai", "kanchipuram"): 72,
    ("chennai", "tirupati"): 135,
    ("chennai", "vellore"): 135,
    ("chennai", "bangalore"): 350,
    ("chennai", "bengaluru"): 350,
    ("chennai", "mysore"): 480,
    ("chennai", "kochi"): 690,
    ("madurai", "trichy"): 140,
    ("madurai", "thanjavur"): 185,
    ("madurai", "kodaikanal"): 120,
    ("madurai", "rameswaram"): 175,
    ("madurai", "kanyakumari"): 245,
    ("madurai", "chennai"): 462,
    ("trichy", "thanjavur"): 55,

    # ─── South India inter-state ───
    ("bangalore", "mysore"): 145,
    ("bangalore", "chennai"): 350,
    ("bangalore", "hyderabad"): 570,
    ("bangalore", "goa"): 560,
    ("bangalore", "kochi"): 540,
    ("bangalore", "ooty"): 280,
    ("bangalore", "pondicherry"): 310,
    ("kochi", "munnar"): 130,
    ("kochi", "thiruvananthapuram"): 205,
    ("kochi", "alleppey"): 55,
    ("hyderabad", "bangalore"): 570,
    ("hyderabad", "chennai"): 630,

    # ─── North India ───
    ("delhi", "jaipur"): 280,
    ("delhi", "agra"): 230,
    ("delhi", "chandigarh"): 250,
    ("delhi", "dehradun"): 250,
    ("delhi", "haridwar"): 230,
    ("delhi", "rishikesh"): 240,
    ("delhi", "lucknow"): 555,
    ("jaipur", "udaipur"): 395,
    ("jaipur", "jodhpur"): 340,
    ("mumbai", "pune"): 150,
    ("mumbai", "goa"): 590,
    ("mumbai", "ahmedabad"): 530,
    ("mumbai", "nashik"): 170,
}


ROAD_CITIES = {
    "coimbatore": {"name": "Coimbatore", "state": "Tamil Nadu"},
    "chennai": {"name": "Chennai", "state": "Tamil Nadu"},
    "madurai": {"name": "Madurai", "state": "Tamil Nadu"},
    "trichy": {"name": "Tiruchirappalli", "state": "Tamil Nadu"},
    "salem": {"name": "Salem", "state": "Tamil Nadu"},
    "erode": {"name": "Erode", "state": "Tamil Nadu"},
    "tiruppur": {"name": "Tiruppur", "state": "Tamil Nadu"},
    "thanjavur": {"name": "Thanjavur", "state": "Tamil Nadu"},
    "dindigul": {"name": "Dindigul", "state": "Tamil Nadu"},
    "ooty": {"name": "Ooty (Udhagamandalam)", "state": "Tamil Nadu"},
    "kodaikanal": {"name": "Kodaikanal", "state": "Tamil Nadu"},
    "pondicherry": {"name": "Pondicherry", "state": "Puducherry"},
    "puducherry": {"name": "Puducherry", "state": "Puducherry"},
    "kanchipuram": {"name": "Kanchipuram", "state": "Tamil Nadu"},
    "vellore": {"name": "Vellore", "state": "Tamil Nadu"},
    "rameswaram": {"name": "Rameswaram", "state": "Tamil Nadu"},
    "kanyakumari": {"name": "Kanyakumari", "state": "Tamil Nadu"},
    "pollachi": {"name": "Pollachi", "state": "Tamil Nadu"},
    "tirupati": {"name": "Tirupati", "state": "Andhra Pradesh"},
    "bangalore": {"name": "Bengaluru", "state": "Karnataka"},
    "bengaluru": {"name": "Bengaluru", "state": "Karnataka"},
    "mysore": {"name": "Mysuru", "state": "Karnataka"},
    "mysuru": {"name": "Mysuru", "state": "Karnataka"},
    "kochi": {"name": "Kochi", "state": "Kerala"},
    "munnar": {"name": "Munnar", "state": "Kerala"},
    "alleppey": {"name": "Alappuzha", "state": "Kerala"},
    "palakkad": {"name": "Palakkad", "state": "Kerala"},
    "thiruvananthapuram": {"name": "Thiruvananthapuram", "state": "Kerala"},
    "hyderabad": {"name": "Hyderabad", "state": "Telangana"},
    "goa": {"name": "Goa", "state": "Goa"},
    "mumbai": {"name": "Mumbai", "state": "Maharashtra"},
    "pune": {"name": "Pune", "state": "Maharashtra"},
    "delhi": {"name": "Delhi", "state": "Delhi"},
    "jaipur": {"name": "Jaipur", "state": "Rajasthan"},
    "agra": {"name": "Agra", "state": "Uttar Pradesh"},
    "udaipur": {"name": "Udaipur", "state": "Rajasthan"},
    "jodhpur": {"name": "Jodhpur", "state": "Rajasthan"},
    "ahmedabad": {"name": "Ahmedabad", "state": "Gujarat"},
    "lucknow": {"name": "Lucknow", "state": "Uttar Pradesh"},
    "haridwar": {"name": "Haridwar", "state": "Uttarakhand"},
    "rishikesh": {"name": "Rishikesh", "state": "Uttarakhand"},
    "chandigarh": {"name": "Chandigarh", "state": "Punjab"},
    "dehradun": {"name": "Dehradun", "state": "Uttarakhand"},
    "nashik": {"name": "Nashik", "state": "Maharashtra"},
}


def _get_road_distance(origin: str, destination: str) -> int:
    """Get road distance between two cities."""
    o, d = origin.lower(), destination.lower()
    dist = ROAD_DISTANCES.get((o, d)) or ROAD_DISTANCES.get((d, o))
    if dist:
        return dist
    return random.randint(150, 600)


def _get_city_info(city: str) -> dict:
    """Get city info."""
    return ROAD_CITIES.get(
        city.lower(),
        {"name": city.title(), "state": "India"}
    )


def _generate_road_options(origin: str, destination: str, date: str, budget: str) -> list:
    """Generate bus, cab, and self-drive options with INR pricing."""
    distance = _get_road_distance(origin, destination)
    origin_info = _get_city_info(origin)
    dest_info = _get_city_info(destination)

    budget_key = budget.lower() if budget.lower() in BUS_TYPES else "moderate"
    bus_types = BUS_TYPES[budget_key]

    results = []

    # ─── Generate bus options ───
    num_buses = random.randint(3, 5)
    for _ in range(num_buses):
        is_govt = random.random() < 0.35
        if is_govt:
            operator = random.choice(GOVERNMENT_OPERATORS)
        else:
            operator = random.choice(PRIVATE_OPERATORS)

        bus_type = random.choice(bus_types)
        base_fare = distance * BUS_BASE_FARE_PER_KM * bus_type["mult"]
        fare_inr = round(base_fare + random.uniform(-30, 80), 0)
        fare_inr = max(fare_inr, 80)

        # Duration: average 40-60 km/h for buses
        speed = random.choice([40, 45, 50, 55, 60])
        duration_hrs = distance / speed
        hours = int(duration_hrs)
        mins = int((duration_hrs - hours) * 60)

        dep_hour = random.choice([6, 7, 8, 9, 10, 14, 15, 20, 21, 22, 23])
        dep_min = random.choice(["00", "15", "30", "45"])

        seats_avail = random.randint(1, 35)

        results.append({
            "mode": "Bus",
            "operator": operator["name"],
            "operator_type": operator["type"],
            "vehicle_type": bus_type["type"],
            "origin": origin_info["name"],
            "origin_state": origin_info["state"],
            "destination": dest_info["name"],
            "destination_state": dest_info["state"],
            "departure_time": f"{dep_hour:02d}:{dep_min}",
            "duration": f"{hours}h {mins}m",
            "distance_km": distance,
            "fare_inr": fare_inr,

            "seats_available": seats_avail,
            "amenities": _get_bus_amenities(bus_type["type"], operator["type"]),
            "rating": round(random.uniform(3.5, 4.8), 1),
            "boarding_point": f"{origin_info['name']} Bus Stand",
            "dropping_point": f"{dest_info['name']} Bus Stand",
            "date": date,
        })

    # ─── Generate cab/ride options ───
    num_cabs = random.randint(2, 3)
    for _ in range(num_cabs):
        provider = random.choice(CAB_PROVIDERS)

        if provider["type"] == "Self-Drive":
            fare_inr = round(distance * 5.0 + random.uniform(500, 1500), 0)
            vehicle = random.choice(["Swift Dzire", "Hyundai i20", "Tata Nexon", "Maruti Baleno"])
        else:
            fare_inr = round(distance * CAB_BASE_FARE_PER_KM + random.uniform(200, 800), 0)
            vehicle = random.choice([
                "Sedan (Swift Dzire)", "SUV (Toyota Innova)",
                "Hatchback (WagonR)", "Premium (Toyota Innova Crysta)",
                "Sedan (Honda Amaze)", "SUV (Mahindra XUV700)",
            ])

        speed = random.choice([50, 60, 70, 80])
        duration_hrs = distance / speed
        hours = int(duration_hrs)
        mins = int((duration_hrs - hours) * 60)

        results.append({
            "mode": provider["type"],
            "operator": provider["name"],
            "operator_type": provider["type"],
            "vehicle_type": vehicle,
            "origin": origin_info["name"],
            "origin_state": origin_info["state"],
            "destination": dest_info["name"],
            "destination_state": dest_info["state"],
            "departure_time": "Flexible",
            "duration": f"{hours}h {mins}m (approx)",
            "distance_km": distance,
            "fare_inr": fare_inr,

            "seats_available": 4 if "SUV" in vehicle else 3,
            "amenities": _get_cab_amenities(provider["type"]),
            "rating": round(random.uniform(4.0, 4.9), 1),
            "boarding_point": "Door pickup",
            "dropping_point": "Door drop-off",
            "date": date,
        })

    results.sort(key=lambda x: x["fare_inr"])
    return results


def _get_bus_amenities(bus_type: str, operator_type: str) -> list:
    """Return amenities based on bus type."""
    base = ["Charging Point"]
    if "AC" in bus_type:
        base.append("Air Conditioning")
    if "Sleeper" in bus_type:
        base.extend(["Blanket", "Pillow"])
    if "Volvo" in bus_type or "Mercedes" in bus_type or "Scania" in bus_type:
        base.extend(["WiFi", "Water Bottle", "Entertainment"])
    if operator_type == "Private":
        base.append("Live Tracking")
    return base


def _get_cab_amenities(provider_type: str) -> list:
    """Return amenities based on cab type."""
    base = ["AC", "Door-to-Door", "Luggage Space"]
    if provider_type == "Self-Drive":
        base = ["AC", "GPS Navigation", "Fuel Included", "Insurance"]
    else:
        base.extend(["Driver", "Live Tracking"])
    return base


@crewai_tool
def search_road_options(query: str) -> str:
    """Search for road travel options (buses, cabs, self-drive) between Indian cities.
    Focuses on Tamil Nadu & South India routes. Input should be a JSON string
    with keys: origin, destination, date, budget (budget/moderate/luxury).
    Returns options with pricing in INR."""
    try:
        params = json.loads(query)
    except json.JSONDecodeError:
        parts = query.replace(",", " ").split()
        params = {
            "origin": parts[0] if len(parts) > 0 else "Coimbatore",
            "destination": parts[1] if len(parts) > 1 else "Chennai",
            "date": parts[2] if len(parts) > 2 else "2025-06-15",
            "budget": parts[3] if len(parts) > 3 else "moderate",
        }

    options = _generate_road_options(
        params.get("origin", "Coimbatore"),
        params.get("destination", "Chennai"),
        params.get("date", "2025-06-15"),
        params.get("budget", "moderate"),
    )
    return json.dumps(options, indent=2)


def create_road_agent(llm=None) -> Agent:
    """Create and return the Road Travel Specialist agent."""
    kwargs = {
        "role": "Road Travel Specialist — India",
        "goal": (
            "Find the best intercity road travel options across India, with deep "
            "expertise in Tamil Nadu and South India routes. Compare government buses "
            "(TNSTC, SETC, KSRTC), premium private operators (KPN, SRS, Parveen), "
            "outstation cabs (Ola, Uber), and self-drive rentals to recommend the "
            "most comfortable and cost-effective road journey."
        ),
        "backstory": (
            "You are a seasoned road travel expert who has traveled every highway "
            "and back-road across Tamil Nadu and South India. From the bustling "
            "Coimbatore-Chennai corridor to the scenic Coimbatore-Ooty Ghat Road, "
            "you know which bus operators provide the smoothest ride, which cab "
            "services offer the best value, and the perfect departure times to "
            "avoid traffic. You have a special expertise in Tamil Nadu State "
            "Transport Corporation routes and private operators running out of "
            "Coimbatore, Madurai, and Chennai. Your travelers always arrive "
            "refreshed and on-budget."
        ),
        "tools": [search_road_options],
        "verbose": True,
        "allow_delegation": False,
    }
    if llm:
        kwargs["llm"] = llm
    return Agent(**kwargs)
