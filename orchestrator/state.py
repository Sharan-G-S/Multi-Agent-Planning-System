"""
Planner State — Shared state schema for the LangGraph orchestrator.

Defines the TypedDict that flows through all nodes in the planning graph,
carrying user inputs and intermediate results from each agent.
"""

from typing import TypedDict, Optional, List, Dict, Any


class PlannerState(TypedDict, total=False):
    """Shared state for the multi-agent travel planning pipeline."""

    # ─── User Inputs ───
    origin: str
    destination: str
    departure_date: str
    return_date: str
    budget: str                     # "budget" | "moderate" | "luxury"
    travelers: int
    interests: str                  # comma-separated interests
    special_requests: str

    # ─── Agent Outputs ───
    flight_results: List[Dict[str, Any]]
    hotel_results: List[Dict[str, Any]]
    train_results: List[Dict[str, Any]]       # Indian Railways results
    road_results: List[Dict[str, Any]]        # Road travel (bus/cab) results
    itinerary: List[Dict[str, Any]]

    # ─── Orchestration Metadata ───
    current_step: str
    steps_completed: List[str]
    errors: List[str]
    status: str                     # "planning" | "searching" | "complete" | "error"
    summary: str
