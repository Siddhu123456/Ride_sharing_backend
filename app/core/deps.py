from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select
from starlette import status

from app.core.database import get_db
from app.models.user_session import UserSession
from app.utils.jwt import decode_access_token

security = HTTPBearer()


def get_current_user_session(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserSession:
    token = creds.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    session_id = payload.get("session_id")
    user_id = payload.get("sub")

    if not session_id or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    session = db.execute(
        select(UserSession)
        .where(UserSession.session_id == session_id)
        .where(UserSession.logged_out_at.is_(None))
    ).scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or logged out"
        )

    return session
