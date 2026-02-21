"""
Crew Manager — CrewAI orchestration layer.

Creates and configures the multi-agent crew with specialized agents
for flight search, hotel search, and itinerary building. Defines
tasks and runs the crew sequentially.
"""

import json
import os
from typing import Dict, Any

from crewai import Crew, Task

from agents.flight_agent import create_flight_agent
from agents.hotel_agent import create_hotel_agent
from agents.itinerary_agent import create_itinerary_agent


def _get_llm():
    """Attempt to create a Gemini LLM; return None if unavailable."""
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key or api_key == "your_google_api_key_here":
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.7,
        )
    except Exception:
        return None


def create_crew(params: Dict[str, Any]) -> Crew:
    """
    Create a fully configured CrewAI crew with all three agents.

    Args:
        params: Travel planning parameters (origin, destination, dates, budget, etc.)

    Returns:
        A configured Crew ready to be kicked off.
    """
    llm = _get_llm()

    flight_agent = create_flight_agent(llm=llm)
    hotel_agent = create_hotel_agent(llm=llm)
    itinerary_agent = create_itinerary_agent(llm=llm)

    # ─── Task Definitions ───
    flight_task = Task(
        description=(
            f"Search for the best flight options from {params.get('origin', 'NYC')} "
            f"to {params.get('destination', 'London')} on {params.get('departure_date', '2025-06-15')}. "
            f"The traveler's budget level is '{params.get('budget', 'moderate')}'. "
            f"Find at least 3 options and compare prices, airlines, and travel times. "
            f"Present the results in a clear, organized format."
        ),
        expected_output=(
            "A JSON-formatted list of flight options with airline, price, departure time, "
            "duration, number of stops, and a recommendation for the best value option."
        ),
        agent=flight_agent,
    )

    hotel_task = Task(
        description=(
            f"Find the best hotel and accommodation options in {params.get('destination', 'London')} "
            f"for check-in on {params.get('departure_date', '2025-06-15')} and "
            f"check-out on {params.get('return_date', '2025-06-20')}. "
            f"The traveler's budget level is '{params.get('budget', 'moderate')}'. "
            f"Find at least 4 options and compare prices, ratings, amenities, and locations."
        ),
        expected_output=(
            "A JSON-formatted list of hotel options with name, price per night, star rating, "
            "amenities, guest rating, and a recommendation for the best overall choice."
        ),
        agent=hotel_agent,
    )

    itinerary_task = Task(
        description=(
            f"Create a detailed day-by-day itinerary for a trip to {params.get('destination', 'London')}. "
            f"The trip will be approximately {params.get('num_days', 3)} days long. "
            f"The traveler's interests include: {params.get('interests', 'culture, food, history')}. "
            f"Budget level is '{params.get('budget', 'moderate')}'. "
            f"Include morning, afternoon, and evening activities, plus dining recommendations. "
            f"Consider the flight and hotel information from previous agents."
        ),
        expected_output=(
            "A JSON-formatted day-by-day itinerary with themed days, timed activities "
            "(morning/afternoon/evening), dining recommendations, and helpful travel tips."
        ),
        agent=itinerary_agent,
    )

    crew = Crew(
        agents=[flight_agent, hotel_agent, itinerary_agent],
        tasks=[flight_task, hotel_task, itinerary_task],
        verbose=True,
    )

    return crew


def run_crew(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the full planning crew and return results.

    Args:
        params: Travel planning parameters.

    Returns:
        Dict with keys 'flights', 'hotels', 'itinerary', and 'summary'.
    """
    try:
        crew = create_crew(params)
        result = crew.kickoff()

        return {
            "success": True,
            "raw_output": str(result),
            "agents_used": ["Flight Search Specialist", "Hotel Concierge", "Itinerary Architect"],
            "status": "complete",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": "error",
        }
