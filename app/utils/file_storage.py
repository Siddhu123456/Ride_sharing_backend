import os
import uuid
from fastapi import UploadFile
from app.core.config import settings


def save_upload_file(file: UploadFile, folder: str) -> str:
    base_dir = settings.UPLOAD_BASE

    os.makedirs(os.path.join(base_dir, folder), exist_ok=True)

    ext = os.path.splitext(file.filename)[-1]
    safe_name = f"{uuid.uuid4().hex}{ext}"

    relative_path = os.path.join(base_dir, folder, safe_name)

    with open(relative_path, "wb") as f:
        f.write(file.file.read())

    return relative_path
