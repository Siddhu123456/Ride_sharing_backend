from fastapi import FastAPI
from app.routes import auth,country,admin_tenant
from app.routes.admin_tenant_admin import router as tenant_admin_router
from app.routes.admin_tenant_tax_rule import router as admin_tax_router

from app.routes.fleet_owner import router as fleet_owner_router
from app.routes.tenant_admin_fleet import router as tenant_admin_fleet_router


app = FastAPI(
    title="Global Ride Platform",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(country.router)
app.include_router(admin_tenant.router)
app.include_router(tenant_admin_router)
app.include_router(admin_tax_router)
app.include_router(fleet_owner_router)
app.include_router(tenant_admin_fleet_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
