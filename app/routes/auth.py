from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, select
from starlette import status

from app.core.database import get_db
from app.core.deps import get_current_user_session
from app.core.security import hash_password, verify_password
from app.models.country import Country
from app.models.user import AppUser, UserAuth
from app.models.user_session import UserSession
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, SelectRoleRequest, TokenResponse
from app.utils.jwt import create_access_token
from app.schemas.enums import UserRoleEnum
from app.models.user_role import UserRole

router = APIRouter(prefix="/auth", tags=["Auth"])

# ✅ LOGIN: verify password + return roles list
@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):

    user = db.execute(
        select(AppUser).where(AppUser.email == payload.email)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    auth = db.execute(
        select(UserAuth).where(UserAuth.user_id == user.user_id)
    ).scalar_one_or_none()

    if not auth:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if auth.is_locked:
        raise HTTPException(status_code=403, detail="Account is locked")

    # ✅ Verify password
    if not verify_password(payload.password, auth.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ✅ Fetch roles from user_roles table
    db_roles = db.execute(
        select(UserRole.user_role)
        .where(UserRole.user_id == user.user_id)
        .where(UserRole.is_active == True)
    ).scalars().all()

    # ✅ Ensure RIDER is always available
    roles = set(db_roles)
    roles.add(UserRoleEnum.RIDER)

    return LoginResponse(
        user_id=user.user_id,
        roles=list(roles)
    )


@router.post("/select-role", response_model=TokenResponse)
def select_role(payload: SelectRoleRequest, db: Session = Depends(get_db)):

    # ✅ Check user exists
    user = db.execute(
        select(AppUser).where(AppUser.user_id == payload.user_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Validate role selection (only for non-RIDER)
    if payload.role != UserRoleEnum.RIDER:
        role_exists = db.execute(
            select(UserRole)
            .where(UserRole.user_id == payload.user_id)
            .where(UserRole.user_role == payload.role)
            .where(UserRole.is_active == True)
        ).scalar_one_or_none()

        if not role_exists:
            raise HTTPException(status_code=403, detail="Role not assigned to this user")

    # ✅ 1) Check for existing active session for same user + role
    existing_session = db.execute(
        select(UserSession)
        .where(UserSession.user_id == payload.user_id)
        .where(UserSession.active_role == payload.role)
        .where(UserSession.logged_out_at.is_(None))
    ).scalar_one_or_none()

    # ✅ 2) If exists → logout old session (force single login)
    if existing_session:
        existing_session.logged_out_at = datetime.now(timezone.utc)

    # ✅ 3) Create new session
    session = UserSession(
        user_id=payload.user_id,
        active_role=payload.role
    )
    db.add(session)
    db.flush()  # ✅ gets session_id

    # ✅ 4) Create JWT
    token = create_access_token({
        "sub": str(payload.user_id),
        "session_id": str(session.session_id),
        "role": payload.role.value
    })

    db.commit()

    return TokenResponse(access_token=token)



@router.post("/register", response_model=RegisterResponse, status_code=201)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):

    try:
        new_user = AppUser(
            full_name=payload.full_name,
            phone=payload.phone,
            email=str(payload.email),
            gender=payload.gender.value,
            country_code=payload.country_code
        )
        db.add(new_user)
        db.flush()  # generates user_id

        auth = UserAuth(
            user_id=new_user.user_id,
            password_hash=hash_password(payload.password)
        )
        db.add(auth)

        default_role = UserRole(
            user_id=new_user.user_id,
            user_role=UserRoleEnum.RIDER
        )
        db.add(default_role)

        db.commit()
        db.refresh(new_user)

        return RegisterResponse(user_id=new_user.user_id, message="User registered successfully")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    current_session: UserSession = Depends(get_current_user_session),
    db: Session = Depends(get_db)
):
    current_session.logged_out_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Logged out successfully"}

