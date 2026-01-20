from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.routes import auth,country,admin_tenant
from app.routes.admin_tenant_admin import router as tenant_admin_router
from app.routes.admin_tenant_tax_rule import router as admin_tax_router

from app.routes.fleet_owner import router as fleet_owner_router
from app.routes.tenant_admin_fleet import router as tenant_admin_fleet_router


from app.routes.fleet_owner_driver import router as fleet_owner_driver_router
from app.routes.driver_docs import router as driver_docs_router
from app.routes.tenant_admin_driver_verify import router as tenant_admin_driver_verify_router


from app.routes.fleet_owner_vehicle import router as fleet_owner_vehicle_router
from app.routes.tenant_admin_vehicle_verify import router as tenant_admin_vehicle_router

from app.routes.fleet_owner_vehicle_assignment import router as fleet_owner_vehicle_assignment_router

from app.routes.driver_shift_location import router as driver_shift_location_router

from app.routes.trip_routes import router as trip_router
from app.routes.driver_offer_routes import router as driver_offer_router

from fastapi import FastAPI

from app.routes.trip_routes import router as trip_router
from app.routes.driver_offer_routes import router as driver_offer_router
from app.routes.otp_routes import router as otp_router
from app.routes.trip_lifecycle_routes import router as lifecycle_router




app = FastAPI(
    title="Global Ride Platform",
    version="1.0.0"
)

origins = [
    "http://localhost:5173",  # Vite default
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(country.router)
app.include_router(admin_tenant.router)
app.include_router(tenant_admin_router)
app.include_router(admin_tax_router)
app.include_router(fleet_owner_router)
app.include_router(tenant_admin_fleet_router)
app.include_router(fleet_owner_driver_router)
app.include_router(driver_docs_router)
app.include_router(tenant_admin_driver_verify_router)
app.include_router(fleet_owner_vehicle_router)
app.include_router(tenant_admin_vehicle_router)
app.include_router(fleet_owner_vehicle_assignment_router)
app.include_router(driver_shift_location_router)
app.include_router(trip_router)
app.include_router(driver_offer_router)
app.include_router(trip_router)
app.include_router(driver_offer_router)
app.include_router(otp_router)
app.include_router(lifecycle_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
