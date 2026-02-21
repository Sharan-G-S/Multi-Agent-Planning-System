# Multi-Agent Travel Planning System

An intelligent AI-powered travel planning platform that leverages **multi-agent orchestration** to coordinate specialized tasks — flight search, hotel booking, Indian Railways, road travel (buses/cabs), and itinerary generation. Each agent is an expert in its domain, working together through a stateful **7-node pipeline** to craft personalized, comprehensive travel plans.

**Special Focus:** Deep coverage of **Indian travel** — Tamil Nadu routes from Coimbatore, IRCTC-style train booking, TNSTC/SETC government buses, and private operators like KPN & SRS Travels.

---
# Sharan G S

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Web Frontend (JS)                     │
│         Premium Dark UI · Glassmorphism · Tabs           │
└──────────────────────┬───────────────────────────────────┘
                       │ REST API
┌──────────────────────▼───────────────────────────────────┐
│                   Flask API Server                       │
│           /api/plan · /api/agents · /api/health          │
└──────────────────────┬───────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────┐
│              LangGraph Orchestrator (7 nodes)            │
│   collect → flights → hotels → trains → road            │
│              → itinerary → compile → END                 │
└──────────────────────┬───────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────┐
│                  CrewAI Agent Layer (5 agents)            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │
│  │ Flight   │ │ Hotel    │ │ Railway  │ │ Road       │ │
│  │ Agent    │ │ Agent    │ │ Agent    │ │ Agent      │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬──────┘ │
│       │             │            │              │        │
│  ┌────┴─────────────┴────────────┴──────────────┘        │
│  │              Itinerary Architect Agent                 │
│  └───────────────────────────────────────────────────────┘ │
│                     Mock Search Tools                     │
└──────────────────────────────────────────────────────────┘
```

## Key Frameworks

| Framework | Version | Role |
|-----------|---------|------|
| **CrewAI** | ≥0.28 | Multi-agent orchestration — defines agents, tasks, and crew collaboration |
| **LangGraph** | ≥0.0.20 | Stateful graph-based workflow — manages the 7-node planning pipeline |
| **Flask** | ≥3.0 | REST API server — bridges the frontend UI with the agent backend |
| **Google Gemini** | ≥0.3 | LLM backend (optional) — powers intelligent agent reasoning |

## Specialized Agents

### ✈️ Flight Search Specialist
> Compares airlines, pricing strategies, and travel routes to find optimal flight options. Generates realistic fare data with airline ratings, stop types, and cabin classes.

### 🏨 Hotel & Accommodation Concierge
> Discovers top properties by analyzing star ratings, guest reviews, amenities, and location proximity. Generates detailed hotel comparisons with pricing and cancellation policies.

### 🚂 Indian Railways Specialist
> Searches train routes across India with **30+ stations**, **10 train types** (Rajdhani, Vande Bharat, Shatabdi, Duronto, Tejas), **IRCTC-style classes** (SL, 3A, 2A, 1A, CC, EC), **INR pricing**, and availability status (Available / RAC / Waitlist).

### 🚌 Road Travel Specialist (Tamil Nadu Focus)
> Finds the best intercity road travel options — government buses (TNSTC, SETC, KSRTC), premium private operators (KPN, SRS, Parveen, VRL), outstation cabs (Ola, Uber), and self-drive rentals. **50+ routes centered on Coimbatore** with 3 bus tiers from Non-AC Seater to Volvo Multi-Axle.

### 🗺️ Itinerary Architect
> Crafts day-by-day travel plans combining top attractions, hidden gems, and dining recommendations. Features a curated **attractions database for 28+ cities** including 8 Tamil Nadu destinations.

## Indian Travel Coverage

### Coimbatore Routes (Road & Rail)
| Route | Distance | Bus (approx) | Train |
|-------|----------|--------------|-------|
| Coimbatore → Chennai | 505 km | ₹400–1,500 | ₹300–2,000 |
| Coimbatore → Bangalore | 365 km | ₹300–1,200 | ₹250–1,500 |
| Coimbatore → Madurai | 218 km | ₹200–800 | ₹150–900 |
| Coimbatore → Ooty | 86 km | ₹80–400 | ₹50–300 |
| Coimbatore → Kochi | 195 km | ₹200–900 | ₹180–800 |
| Coimbatore → Mysore | 220 km | ₹250–1,000 | ₹200–1,000 |

### Supported Tamil Nadu Destinations
Coimbatore, Chennai, Madurai, Trichy, Salem, Erode, Tiruppur, Thanjavur, Ooty, Kodaikanal, Pondicherry, Rameswaram, Kanyakumari, Vellore, Kanchipuram, Pollachi, Dindigul

### Bus Operators
| Type | Operators |
|------|-----------|
| **Government** | TNSTC, SETC, KSRTC, KSRTC-KA, APSRTC, TSRTC |
| **Private Premium** | KPN Travels, SRS Travels, Parveen Travels, Kallada, VRL, IntrCity SmartBus |
| **Private Standard** | SRM Travels, Orange Tours, Jabbar Travels, Rajesh Transports |

### Train Types
Rajdhani Express, Vande Bharat, Shatabdi Express, Duronto Express, Tejas Express, Garib Rath, Humsafar Express, Sampark Kranti, Jan Shatabdi, Superfast Express

## Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/Sharan-G-S/Multi-Agent-Planning-System.git
cd Multi-Agent-Planning-System

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure API key for live LLM-powered agents
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Run the Application

```bash
python app.py
```

Open your browser at **http://localhost:5000**

### Example Searches
- **Coimbatore → Chennai** — Flights, TNSTC buses, KPN sleepers, trains, and Chennai itinerary
- **Coimbatore → Ooty** — Road options with scenic ghat road route
- **Delhi → Mumbai** — Full suite: flights, Rajdhani Express, Volvo buses, hotels
- **Madurai → Rameswaram** — Temple circuit with local buses

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check & system status |
| `GET` | `/api/agents` | List available agents and their status |
| `POST` | `/api/plan` | Run the LangGraph planning pipeline (7 nodes) |
| `POST` | `/api/plan/crew` | Run the CrewAI crew (requires API key) |

### Example Request

```json
POST /api/plan
{
    "origin": "Coimbatore",
    "destination": "Chennai",
    "departure_date": "2025-06-15",
    "return_date": "2025-06-20",
    "budget": "moderate",
    "travelers": 2,
    "interests": "temples, culture, food"
}
```

## Project Structure

```
Multi-Agent-Planning-System/
├── app.py                          # Flask API server
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── agents/
│   ├── __init__.py
│   ├── flight_agent.py             # Flight Search Specialist
│   ├── hotel_agent.py              # Hotel Concierge
│   ├── train_agent.py              # Indian Railways Specialist
│   ├── road_agent.py               # Road Travel (Buses/Cabs/Self-Drive)
│   └── itinerary_agent.py          # Itinerary Architect
├── orchestrator/
│   ├── __init__.py
│   ├── state.py                    # PlannerState TypedDict
│   ├── crew_manager.py             # CrewAI Crew orchestration
│   └── graph_orchestrator.py       # LangGraph StateGraph pipeline (7 nodes)
└── static/
    ├── index.html                  # Premium web interface
    ├── css/style.css               # Dark glassmorphism theme
    └── js/app.js                   # Frontend logic & rendering
```

## How It Works

1. **User submits travel preferences** via the web interface (origin, destination, dates, budget, interests)
2. **Flask API** receives the request and passes it to the LangGraph orchestrator
3. **LangGraph StateGraph** manages the 7-node pipeline:
   - **Validate Input** — normalizes and validates user parameters
   - **Search Flights** — Flight Agent finds optimal air travel options
   - **Search Hotels** — Hotel Agent discovers top accommodations
   - **Search Trains** — Railway Agent searches Indian Railways routes with INR pricing
   - **Search Road** — Road Agent finds bus, cab, and self-drive options
   - **Build Itinerary** — Itinerary Agent crafts a day-by-day plan
   - **Compile Results** — aggregates all outputs with a summary
4. **Results** are displayed in a tabbed interface (Flights / Hotels / Trains / Road / Itinerary)

## Technologies

- **Backend:** Python, Flask, CrewAI, LangGraph, LangChain
- **Frontend:** HTML5, CSS3 (Glassmorphism), JavaScript (Vanilla)
- **LLM:** Google Gemini (optional, falls back to mock data)
- **Design:** Inter font, Font Awesome icons, CSS animations

---

<p align="center">Made with 💚 from Sharan G S</p>
