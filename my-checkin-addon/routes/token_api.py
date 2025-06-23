# from fastapi import APIRouter
# from datetime import datetime
# import hashlib

# token_api = APIRouter()

# @token_api.post("/generate_token")
# def generate_token():
#     timestamp = str(datetime.now().timestamp()).encode("utf-8")
#     token = hashlib.sha256(timestamp).hexdigest()[:32]
#     return {"token": token}
