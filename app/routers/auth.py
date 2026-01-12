from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, select
from starlette import status

from app.core.database import get_db
from app.core.security import hash_password
from app.models.user import AppUser, UserAuth
from app.schemas.auth import LoginRequest, RegisterRequest, RegisterResponse, TokenResponse
from app.utils.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.execute(
        select(AppUser).where(AppUser.phone == payload.phone)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.user_id)})

    return {"access_token": token}



@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    payload: RegisterRequest,
    db: Session = Depends(get_db)
):
    # 1️⃣ Check phone or email uniqueness
    existing_user = db.execute(
        select(AppUser).where(
            or_(
                AppUser.phone == payload.phone,
                AppUser.email == payload.email
            )
        )
    ).scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this phone or email already exists"
        )

    # 2️⃣ Create app_user
    new_user = AppUser(
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        gender=payload.gender
    )

    db.add(new_user)
    db.flush()  # generates user_id

    # 3️⃣ Create user_auth
    auth = UserAuth(
        user_id=new_user.user_id,
        password_hash=hash_password(payload.password)
    )

    db.add(auth)

    # 4️⃣ Commit transaction
    db.commit()

    return {
        "user_id": new_user.user_id,
        "message": "User registered successfully"
    }