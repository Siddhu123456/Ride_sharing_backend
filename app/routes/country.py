from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.models.core import Country
from app.schemas.country import CountryResponse

router = APIRouter(prefix="/countries", tags=["Country"])

@router.get("/", response_model=list[CountryResponse])
def get_all_countries(db: Session = Depends(get_db)):
    countries = db.execute(select(Country)).scalars().all()
    return countries
