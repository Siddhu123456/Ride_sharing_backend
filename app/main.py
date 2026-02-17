from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routes.common.router import router as common_router
from app.routes.admin.router import router as admin_router
from app.routes.driver.router import router as driver_router
from app.routes.fleet_owner.router import router as fleet_owner_router
from app.routes.tenant_admin.router import router as tenant_admin_router
from app.routes.rider.router import router as rider_router
from app.routes.trip.router import router as trip_router

from fastapi.staticfiles import StaticFiles


app = FastAPI(
    title="Global Ride Platform",
    version="1.0.0"
)

# origins = [
#     "http://localhost:5173",
#     "http://127.0.0.1:5173",
# ]

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include aggregated routers (common + domain packages)
app.include_router(common_router)
app.include_router(admin_router)
app.include_router(driver_router)
app.include_router(fleet_owner_router)
app.include_router(tenant_admin_router)
app.include_router(rider_router)
app.include_router(trip_router)

# STATIC FILES
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/health")
async def health():
    return {"status": "ok"}
