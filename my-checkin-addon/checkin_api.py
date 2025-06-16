import sqlite3
import subprocess
import os
import yaml
import requests
from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi import File, UploadFile
import uvicorn
from dotenv import load_dotenv

from checkin_meta_api import router as meta_router

# Betöltjük egyszer az .env fájlt és kiolvassuk a szükséges változókat
load_dotenv("/config/.env")
HA_TOKEN = os.getenv("HA_TOKEN")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

DB_PATH = "/config/guestbook.db"
SCRIPT_PATH = "/config/scripts/send_access_link.py"
DOOR_MAP_PATH = "/config/guest_door_map.yaml"
HA_URL = os.getenv("HA_URL", "http://homeassistant.local:8123/api/services")

app = FastAPI()
app.include_router(meta_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/local/door/{token}/state")
async def get_door_state(token: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT guest_house_id FROM guest_bookings WHERE access_token = ?", (token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Token not found")

    house_id = str(row["guest_house_id"])

    try:
        with open(DOOR_MAP_PATH, "r") as f:
            door_map = yaml.safe_load(f)
        config = door_map[house_id]
        entity_id = config.get("entity_id")

        if not entity_id:
            raise HTTPException(status_code=500, detail="Hiányos ajtókonfiguráció")

        headers = {
            "Authorization": f"Bearer {HA_TOKEN}"
        }

        response = requests.get(
            f"{HA_URL}/states/{entity_id}",
            headers=headers
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"HA válasz: {response.status_code} {response.text}")

        data = response.json()
        return {"state": data["state"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba az állapot lekérdezéskor: {str(e)}")

@app.get("/local/checkin_data/{token}.json")
async def get_guest_data(token: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM guest_bookings WHERE access_token = ?", (token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Token not found")

    return {
        "guest_first_name": row["guest_first_name"] or "",
        "guest_last_name": row["guest_last_name"] or "",
        "nationality": row["nationality"] or "",
        "birth_date": row["birth_date"] or "",
        "birth_place": row["birth_place"] or "",
        "document_type": row["document_type"] or "",
        "document_number": row["document_number"] or "",
        "cnp": row["cnp"] or "",
        "address": row["address"] or "",
        "travel_purpose": row["travel_purpose"] or "",
        "signature": row["signature"] or ""
    }

@app.post("/local/checkin_data/{token}.submit")
async def submit_guest_data(
    request: Request,
    token: str,
    document_photo: UploadFile = File(...),
    guest_first_name: str = Form(...),
    guest_last_name: str = Form(...),
    nationality: str = Form(...),
    birth_date: str = Form(""),
    birth_place: str = Form(""),
    document_type: str = Form(""),
    document_number: str = Form(""),
    cnp: str = Form(""),
    address: str = Form(""),
    travel_purpose: str = Form(""),
    signature: str = Form("")
):
    # 📁 Dokumentumfotó mentése biztonságos helyre
    save_path = f"/config/private_docs/{token}_document.jpg"
    with open(save_path, "wb") as buffer:
        buffer.write(await document_photo.read())

    # 🗃️ Adatbázis frissítés
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE guest_bookings SET
            guest_first_name = ?,
            guest_last_name = ?,
            nationality = ?,
            birth_date = ?,
            birth_place = ?,
            document_type = ?,
            document_number = ?,
            cnp = ?,
            address = ?,
            travel_purpose = ?,
            signature = ?,
            updated_at = datetime('now')
        WHERE access_token = ?
    """, (
        guest_first_name, guest_last_name, nationality, birth_date,
        birth_place, document_type, document_number, cnp,
        address, travel_purpose, signature, token
    ))

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    if affected == 0:
        raise HTTPException(status_code=404, detail="Token not found")

    # 📤 Email küldés subprocess segítségével
    try:
        env = os.environ.copy()
        env["SMTP_PASSWORD"] = SMTP_PASSWORD
        result = subprocess.run(
            ["python3", SCRIPT_PATH, token],
            capture_output=True,
            text=True,
            env=env
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Sikertelen emailküldés: {result.stderr.strip()}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba emailküldés közben: {str(e)}")

    return {"status": "ok", "message": "Adatok frissítve, email elküldve."}

@app.post("/local/door/{token}/toggle")
async def toggle_door(token: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT guest_house_id FROM guest_bookings WHERE access_token = ?", (token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Token not found")

    house_id = str(row["guest_house_id"])

    try:
        with open(DOOR_MAP_PATH, "r") as f:
            door_map = yaml.safe_load(f)
        if house_id not in door_map:
            raise HTTPException(status_code=404, detail="Nincs ajtókonfiguráció ehhez a házhoz")

        config = door_map[house_id]
        domain = config.get("domain")
        action = config.get("action")
        entity_id = config.get("entity_id")

        if not domain or not action or not entity_id:
            raise HTTPException(status_code=500, detail="Hiányos ajtókonfiguráció")

        headers = {
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{HA_URL}/services/{domain}/{action}",
            headers=headers,
            json={"entity_id": entity_id}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Home Assistant válasz: {response.status_code} {response.text}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ajtóvezérlési hiba: {str(e)}")

    return {"status": "ok", "message": "Ajtó művelet elküldve"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8124)
