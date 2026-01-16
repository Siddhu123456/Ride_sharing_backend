import os
from fastapi import Header, HTTPException
from dotenv import load_dotenv

load_dotenv()  # ✅ make sure .env loads

SUPER_ADMIN_KEY = os.getenv("SUPER_ADMIN_KEY")

def verify_admin(x_admin_key: str = Header(...)):
    if not SUPER_ADMIN_KEY:
        raise HTTPException(status_code=500, detail="SUPER_ADMIN_KEY not set in environment")

    if x_admin_key != SUPER_ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized admin")

    return True
