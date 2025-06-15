import sqlite3
import os
from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import paho.mqtt.publish as publish

DB_PATH = "/config/guestbook.db"
MQTT_HOST = "core-mosquitto"  # vagy pl. "localhost", ha nem Docker
MQTT_PORT = 1883
MQTT_TOPIC = "checkin/success"
MQTT_USER = os.environ.get("MQTT_USER", "")  # opcionális
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")  # opcionális

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    token: str,
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

    # ✅ MQTT publish – sikeres checkin után
    try:
        publish.single(
            topic=MQTT_TOPIC,
            payload=token,
            hostname=MQTT_HOST,
            port=MQTT_PORT,
            auth={"username": MQTT_USER, "password": MQTT_PASSWORD} if MQTT_USER else None
        )
        print(f"✅ MQTT üzenet elküldve a checkin/success topicra: {token}")
    except Exception as e:
        print(f"❌ MQTT hiba: {e}")

    return {"status": "ok", "message": "Adatok frissítve és MQTT elküldve."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8124)
