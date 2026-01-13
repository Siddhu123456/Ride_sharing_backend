from fastapi import FastAPI
from app.routers import auth,country

app = FastAPI(
    title="Global Ride Platform",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(country.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
