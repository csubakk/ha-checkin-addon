# routes/token_aip.py
from fastapi import APIRouter, HTTPException
from datetime import datetime
import hashlib
import os
import requests

token_api = APIRouter()

ENV_PATH = "/config/.env"  # vagy ahova ténylegesen írsz
HA_URL = os.getenv("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")

@token_api.post("/generate_token")
def generate_token():
    # Új token generálása
    timestamp = str(datetime.now().timestamp()).encode("utf-8")
    token = hashlib.sha256(timestamp).hexdigest()[:32]

    # 🔹 1. .env fájl frissítése
    try:
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, "r") as f:
                lines = f.readlines()
        else:
            lines = []

        updated = False
        for i, line in enumerate(lines):
            if line.startswith("OWNER_TOKEN="):
                lines[i] = f"OWNER_TOKEN={token}\n"
                updated = True
                break
        if not updated:
            lines.append(f"OWNER_TOKEN={token}\n")

        with open(ENV_PATH, "w") as f:
            f.writelines(lines)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nem sikerült .env fájlt írni: {e}")

    # 🔹 2. Home Assistant input_text frissítés
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    ha_url = f"{HA_URL}/api/states/input_text.owner_token"

    try:
        requests.post(ha_url, headers=headers, json={"state": token}, timeout=5)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nem sikerült frissíteni a Home Assistant input_text-et: {e}")

    return {"token": token}
