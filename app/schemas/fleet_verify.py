from pydantic import BaseModel

class VerifyFleetDocumentRequest(BaseModel):
    approve: bool
