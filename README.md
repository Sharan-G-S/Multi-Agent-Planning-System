# Multi-Agent Travel Planning System

An intelligent AI-powered travel planning platform that leverages **multi-agent orchestration** to coordinate specialized tasks — flight search, hotel booking, and itinerary generation. Each agent is an expert in its domain, working together through a stateful pipeline to craft personalized, comprehensive travel plans.

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
│              LangGraph Orchestrator                      │
│   StateGraph: collect → flights → hotels → itinerary     │
│              → compile → END                             │
└──────────────────────┬───────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────┐
│                  CrewAI Agent Layer                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │ Flight Agent  │ │ Hotel Agent  │ │ Itinerary Agent  │ │
│  │  Specialist   │ │  Concierge   │ │   Architect      │ │
│  └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘ │
│         │                │                   │           │
│         └────────────────┼───────────────────┘           │
│                          │ Mock Search Tools             │
└──────────────────────────┴───────────────────────────────┘
```

## Key Frameworks

| Framework | Version | Role |
|-----------|---------|------|
| **CrewAI** | ≥0.28 | Multi-agent orchestration — defines agents, tasks, and crew collaboration |
| **LangGraph** | ≥0.0.20 | Stateful graph-based workflow — manages the planning pipeline with typed state transitions |
| **Flask** | ≥3.0 | REST API server — bridges the frontend UI with the agent backend |
| **Google Gemini** | ≥0.3 | LLM backend (optional) — powers intelligent agent reasoning when API key is configured |

## Specialized Agents

### Flight Search Specialist
> Compares airlines, pricing strategies, and travel routes to find optimal flight options. Equipped with a search tool that generates realistic fare data with airline ratings, stop types, and cabin classes.

### Hotel & Accommodation Concierge
> Discovers top properties by analyzing star ratings, guest reviews, amenities, and location proximity. Generates detailed hotel comparisons with pricing, cancellation policies, and breakfast options.

### Itinerary Architect
> Crafts day-by-day travel plans combining top attractions, hidden gems, and dining recommendations. Features a curated attractions database for major cities with time-slotted activities and insider tips.

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

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check & system status |
| `GET` | `/api/agents` | List available agents and their status |
| `POST` | `/api/plan` | Run the LangGraph planning pipeline |
| `POST` | `/api/plan/crew` | Run the CrewAI crew (requires API key) |

### Example Request

```json
POST /api/plan
{
    "origin": "New York",
    "destination": "Paris",
    "departure_date": "2025-06-15",
    "return_date": "2025-06-20",
    "budget": "moderate",
    "travelers": 2,
    "interests": "culture, food, history"
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
│   └── itinerary_agent.py          # Itinerary Architect
├── orchestrator/
│   ├── __init__.py
│   ├── state.py                    # PlannerState TypedDict
│   ├── crew_manager.py             # CrewAI Crew orchestration
│   └── graph_orchestrator.py       # LangGraph StateGraph pipeline
└── static/
    ├── index.html                  # Premium web interface
    ├── css/style.css               # Dark glassmorphism theme
    └── js/app.js                   # Frontend logic & rendering
```

## How It Works

1. **User submits travel preferences** via the web interface (origin, destination, dates, budget, interests)
2. **Flask API** receives the request and passes it to the LangGraph orchestrator
3. **LangGraph StateGraph** manages the pipeline:
   - **Validate Input** — normalizes and validates user parameters
   - **Search Flights** — Flight Agent finds optimal air travel options
   - **Search Hotels** — Hotel Agent discovers top accommodations
   - **Build Itinerary** — Itinerary Agent crafts a day-by-day plan
   - **Compile Results** — aggregates all outputs with a summary
4. **Results** are displayed in a tabbed interface (Flights / Hotels / Itinerary)

## Technologies

- **Backend:** Python, Flask, CrewAI, LangGraph, LangChain
- **Frontend:** HTML5, CSS3 (Glassmorphism), JavaScript (Vanilla)
- **LLM:** Google Gemini (optional, falls back to mock data)
- **Design:** Inter font, Font Awesome icons, CSS animations

---

<p align="center">Made with 💚 by Sharan G S</p>
