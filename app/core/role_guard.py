from fastapi import Depends, HTTPException
from starlette import status

from app.core.deps import get_current_user_session
from app.models.user_session import UserSession
from app.schemas.enums import TenantRoleEnum  # your enum name


def require_role(required_role: TenantRoleEnum):
    def _checker(session: UserSession = Depends(get_current_user_session)):
        if session.active_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {required_role}"
            )
        return session
    return _checker
