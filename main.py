from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import trips, locations, auth

app = FastAPI(title="TripMate AI Production")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(trips.router)
app.include_router(locations.router)
app.include_router(auth.router)

@app.get("/")
def health_check():
    return {"status": "TripMate AI Backend Running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)