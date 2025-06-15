# checkin_meta_api.py
import sqlite3
import yaml
import os
from fastapi import APIRouter, HTTPException
from datetime import datetime

DB_PATH = "/config/guestbook.db"
DOOR_MAP_PATH = "/config/guest_door_map.yaml"

router = APIRouter()

@router.get("/local/checkin_meta/{token}.json")
async def get_checkin_meta(token: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT guest_house_id, checkin_time, checkout_time FROM guest_bookings WHERE access_token = ?", (token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Token not found")

    house_id = str(row["guest_house_id"])

    try:
        with open(DOOR_MAP_PATH, "r") as f:
            door_map = yaml.safe_load(f)
        config = door_map.get(house_id, {})
    except Exception as e:
        config = {}

    return {
        "house_id": house_id,
        "checkin_time": row["checkin_time"],
        "checkout_time": row["checkout_time"],
        "door": {
            "entity_id": config.get("entity_id", ""),
            "domain": config.get("domain", ""),
            "action": config.get("action", "")
        }
    }
