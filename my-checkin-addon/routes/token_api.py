from fastapi import APIRouter
from datetime import datetime
import hashlib

router = APIRouter()

@router.post("/generate_token")
def generate_token():
    timestamp = str(datetime.now().timestamp()).encode("utf-8")
    token = hashlib.sha256(timestamp).hexdigest()[:32]
    return {"token": token}
