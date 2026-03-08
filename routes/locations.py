from fastapi import APIRouter
from lib.ai_engine import df_locs

router = APIRouter(prefix="/api/locations", tags=["Locations"])

@router.get("/")
def list_locations():
    return {"locations": df_locs[['POI_ID', 'Name', 'City', 'Type']].to_dict(orient='records')}