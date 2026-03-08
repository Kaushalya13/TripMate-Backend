from fastapi import APIRouter
from pydantic import BaseModel
from lib.ai_engine import get_route_plan, get_nearby

router = APIRouter(prefix="/api/trips", tags=["AI Engines"])

class TripReq(BaseModel):
    start_location: str
    end_location: str = ""
    age: int
    budget: int
    days: int
    interest_beach: int
    interest_nature: int
    interest_history: int
    interest_religious: int

@router.post("/generate")
def plan_trip(req: TripReq):
    u_prof = [req.age, req.budget, req.interest_beach, req.interest_nature, req.interest_history, req.interest_religious]
    plan = get_route_plan(req.start_location, req.end_location or req.start_location, u_prof, req.days)
    return {"itinerary": plan}

@router.post("/discover")
def discover(req: TripReq):
    u_prof = [req.age, req.budget, req.interest_beach, req.interest_nature, req.interest_history, req.interest_religious]
    return {"recommendations": get_nearby(req.start_location, u_prof)}