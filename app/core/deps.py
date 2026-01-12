from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from app.core.config import settings

def get_current_user(token: str = Depends()):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
