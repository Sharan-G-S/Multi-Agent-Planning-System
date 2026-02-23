"""
Graph Orchestrator — LangGraph stateful orchestration layer.

Implements a StateGraph that manages the travel planning pipeline
through discrete nodes: input collection → flight search → hotel search →
itinerary building → result compilation.

This provides stateful, graph-based workflow management on top of
the CrewAI agent layer.
"""

import json
import traceback
from typing import Dict, Any

from langgraph.graph import StateGraph, END

from orchestrator.state import PlannerState
from agents.flight_agent import search_flights
from agents.hotel_agent import search_hotels
from agents.train_agent import search_trains
from agents.road_agent import search_road_options
from agents.itinerary_agent import build_itinerary


# ────────────────────────────────────────────────────────────
# Graph Nodes — each function takes & returns PlannerState
# ────────────────────────────────────────────────────────────


def collect_input(state: PlannerState) -> Dict[str, Any]:
    """Validate and normalize user inputs."""
    errors = []

    if not state.get("destination"):
        errors.append("Destination is required")
    if not state.get("departure_date"):
        errors.append("Departure date is required")

    origin = state.get("origin", "NYC")
    budget = state.get("budget", "moderate").lower()
    if budget not in ("budget", "moderate", "luxury"):
        budget = "moderate"

    return {
        "origin": origin,
        "budget": budget,
        "current_step": "collect_input",
        "steps_completed": ["collect_input"],
        "errors": errors,
        "status": "planning" if not errors else "error",
    }


def search_flights_node(state: PlannerState) -> Dict[str, Any]:
    """Run the flight search tool and parse results."""
    try:
        query = json.dumps({
            "origin": state.get("origin", "NYC"),
            "destination": state.get("destination", "London"),
            "date": state.get("departure_date", "2025-06-15"),
            "budget": state.get("budget", "moderate"),
        })

        # Call the tool function directly (bypass CrewAI agent for graph mode)
        raw_result = search_flights.run(query)
        flights = json.loads(raw_result) if isinstance(raw_result, str) else raw_result

        steps = list(state.get("steps_completed", []))
        steps.append("search_flights")

        return {
            "flight_results": flights,
            "current_step": "search_flights",
            "steps_completed": steps,
            "status": "searching",
        }
    except Exception as e:
        steps = list(state.get("steps_completed", []))
        steps.append("search_flights")
        errors = list(state.get("errors", []))
        errors.append(f"Flight search error: {str(e)}")
        return {
            "flight_results": [],
            "current_step": "search_flights",
            "steps_completed": steps,
            "errors": errors,
        }


def search_hotels_node(state: PlannerState) -> Dict[str, Any]:
    """Run the hotel search tool and parse results."""
    try:
        query = json.dumps({
            "destination": state.get("destination", "London"),
            "checkin": state.get("departure_date", "2025-06-15"),
            "checkout": state.get("return_date", "2025-06-20"),
            "budget": state.get("budget", "moderate"),
        })

        raw_result = search_hotels.run(query)
        hotels = json.loads(raw_result) if isinstance(raw_result, str) else raw_result

        steps = list(state.get("steps_completed", []))
        steps.append("search_hotels")

        return {
            "hotel_results": hotels,
            "current_step": "search_hotels",
            "steps_completed": steps,
            "status": "searching",
        }
    except Exception as e:
        steps = list(state.get("steps_completed", []))
        steps.append("search_hotels")
        errors = list(state.get("errors", []))
        errors.append(f"Hotel search error: {str(e)}")
        return {
            "hotel_results": [],
            "current_step": "search_hotels",
            "steps_completed": steps,
            "errors": errors,
        }


def search_trains_node(state: PlannerState) -> Dict[str, Any]:
    """Run the Indian Railways search tool and parse results."""
    try:
        query = json.dumps({
            "origin": state.get("origin", "Delhi"),
            "destination": state.get("destination", "Mumbai"),
            "date": state.get("departure_date", "2025-06-15"),
            "budget": state.get("budget", "moderate"),
        })

        raw_result = search_trains.run(query)
        trains = json.loads(raw_result) if isinstance(raw_result, str) else raw_result

        steps = list(state.get("steps_completed", []))
        steps.append("search_trains")

        return {
            "train_results": trains,
            "current_step": "search_trains",
            "steps_completed": steps,
            "status": "searching",
        }
    except Exception as e:
        steps = list(state.get("steps_completed", []))
        steps.append("search_trains")
        errors = list(state.get("errors", []))
        errors.append(f"Train search error: {str(e)}")
        return {
            "train_results": [],
            "current_step": "search_trains",
            "steps_completed": steps,
            "errors": errors,
        }


def search_road_node(state: PlannerState) -> Dict[str, Any]:
    """Run the road travel search tool and parse results."""
    try:
        query = json.dumps({
            "origin": state.get("origin", "Coimbatore"),
            "destination": state.get("destination", "Chennai"),
            "date": state.get("departure_date", "2025-06-15"),
            "budget": state.get("budget", "moderate"),
        })

        raw_result = search_road_options.run(query)
        road_opts = json.loads(raw_result) if isinstance(raw_result, str) else raw_result

        steps = list(state.get("steps_completed", []))
        steps.append("search_road")

        return {
            "road_results": road_opts,
            "current_step": "search_road",
            "steps_completed": steps,
            "status": "searching",
        }
    except Exception as e:
        steps = list(state.get("steps_completed", []))
        steps.append("search_road")
        errors = list(state.get("errors", []))
        errors.append(f"Road search error: {str(e)}")
        return {
            "road_results": [],
            "current_step": "search_road",
            "steps_completed": steps,
            "errors": errors,
        }


def build_itinerary_node(state: PlannerState) -> Dict[str, Any]:
    """Run the itinerary builder tool and parse results."""
    try:
        # Calculate number of days
        num_days = 3
        try:
            from datetime import datetime
            dep = datetime.strptime(state.get("departure_date", "2025-06-15"), "%Y-%m-%d")
            ret = datetime.strptime(state.get("return_date", "2025-06-20"), "%Y-%m-%d")
            num_days = max((ret - dep).days, 1)
        except (ValueError, TypeError):
            pass

        query = json.dumps({
            "destination": state.get("destination", "London"),
            "num_days": num_days,
            "interests": state.get("interests", "culture,food,history"),
            "budget": state.get("budget", "moderate"),
        })

        raw_result = build_itinerary.run(query)
        itinerary = json.loads(raw_result) if isinstance(raw_result, str) else raw_result

        steps = list(state.get("steps_completed", []))
        steps.append("build_itinerary")

        return {
            "itinerary": itinerary,
            "current_step": "build_itinerary",
            "steps_completed": steps,
        }
    except Exception as e:
        steps = list(state.get("steps_completed", []))
        steps.append("build_itinerary")
        errors = list(state.get("errors", []))
        errors.append(f"Itinerary build error: {str(e)}")
        return {
            "itinerary": [],
            "current_step": "build_itinerary",
            "steps_completed": steps,
            "errors": errors,
        }


def compile_results(state: PlannerState) -> Dict[str, Any]:
    """Compile all agent outputs into a final summary."""
    flights = state.get("flight_results", [])
    hotels = state.get("hotel_results", [])
    trains = state.get("train_results", [])
    road_opts = state.get("road_results", [])
    itinerary = state.get("itinerary", [])

    best_flight = flights[0] if flights else None
    best_hotel = hotels[0] if hotels else None
    best_train = trains[0] if trains else None
    best_road = road_opts[0] if road_opts else None

    summary_parts = [
        f"Travel Plan: {state.get('origin', 'NYC')} → {state.get('destination', 'London')}",
        f"Dates: {state.get('departure_date', 'TBD')} to {state.get('return_date', 'TBD')}",
        f"Budget: {state.get('budget', 'moderate').title()}",
        f"Found {len(flights)} flights, {len(hotels)} hotels, {len(trains)} trains, {len(road_opts)} road options",
        f"Generated {len(itinerary)}-day itinerary",
    ]

    if best_flight and best_flight.get('airline') != 'No Airport':
        summary_parts.append(
            f"Best flight: {best_flight.get('airline', 'N/A')} at ₹{best_flight.get('price_inr', 'N/A')}"
        )
    if best_hotel:
        summary_parts.append(
            f"Top hotel: {best_hotel.get('name', 'N/A')} at ₹{best_hotel.get('price_per_night_inr', 'N/A')}/night"
        )
    if best_train and best_train.get('train_name') != 'No Direct Trains':
        summary_parts.append(
            f"Best train: {best_train.get('train_name', 'N/A')} at ₹{best_train.get('fare_inr', 'N/A')}"
        )
    if best_road:
        summary_parts.append(
            f"Best road: {best_road.get('operator', 'N/A')} ({best_road.get('mode', 'Bus')}) at ₹{best_road.get('fare_inr', 'N/A')}"
        )

    steps = list(state.get("steps_completed", []))
    steps.append("compile_results")

    return {
        "summary": " | ".join(summary_parts),
        "current_step": "compile_results",
        "steps_completed": steps,
        "status": "complete",
    }


# ────────────────────────────────────────────────────────────
# Should continue or stop
# ────────────────────────────────────────────────────────────


def should_continue(state: PlannerState) -> str:
    """Determine if the pipeline should continue or abort on errors."""
    errors = state.get("errors", [])
    if errors and state.get("current_step") == "collect_input":
        return "end"
    return "continue"


# ────────────────────────────────────────────────────────────
# Build the LangGraph StateGraph
# ────────────────────────────────────────────────────────────


def create_planning_graph() -> StateGraph:
    """
    Create and compile the travel planning StateGraph.

    Pipeline:
        collect_input → search_flights → search_hotels → build_itinerary → compile_results → END

    Returns:
        A compiled LangGraph that accepts PlannerState as input.
    """
    graph = StateGraph(PlannerState)

    # Add nodes
    graph.add_node("collect_input", collect_input)
    graph.add_node("search_flights", search_flights_node)
    graph.add_node("search_hotels", search_hotels_node)
    graph.add_node("search_trains", search_trains_node)
    graph.add_node("search_road", search_road_node)
    graph.add_node("build_itinerary", build_itinerary_node)
    graph.add_node("compile_results", compile_results)

    # Set entry point
    graph.set_entry_point("collect_input")

    # Add conditional edge after input collection
    graph.add_conditional_edges(
        "collect_input",
        should_continue,
        {
            "continue": "search_flights",
            "end": END,
        },
    )

    # Sequential flow
    graph.add_edge("search_flights", "search_hotels")
    graph.add_edge("search_hotels", "search_trains")
    graph.add_edge("search_trains", "search_road")
    graph.add_edge("search_road", "build_itinerary")
    graph.add_edge("build_itinerary", "compile_results")
    graph.add_edge("compile_results", END)

    return graph.compile()


def run_planning_pipeline(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the full planning pipeline through LangGraph.

    Args:
        params: User's travel planning parameters.

    Returns:
        The final PlannerState with all results.
    """
    graph = create_planning_graph()

    initial_state: PlannerState = {
        "origin": params.get("origin", "NYC"),
        "destination": params.get("destination", "London"),
        "departure_date": params.get("departure_date", "2025-06-15"),
        "return_date": params.get("return_date", "2025-06-20"),
        "budget": params.get("budget", "moderate"),
        "travelers": params.get("travelers", 1),
        "interests": params.get("interests", "culture,food,history"),
        "special_requests": params.get("special_requests", ""),
        "flight_results": [],
        "hotel_results": [],
        "train_results": [],
        "road_results": [],
        "itinerary": [],
        "current_step": "",
        "steps_completed": [],
        "errors": [],
        "status": "planning",
        "summary": "",
    }

    try:
        result = graph.invoke(initial_state)
        return {
            "success": True,
            "data": {
                "flights": result.get("flight_results", []),
                "hotels": result.get("hotel_results", []),
                "trains": result.get("train_results", []),
                "road_options": result.get("road_results", []),
                "itinerary": result.get("itinerary", []),
                "summary": result.get("summary", ""),
                "steps_completed": result.get("steps_completed", []),
            },
            "status": result.get("status", "complete"),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "status": "error",
        }
