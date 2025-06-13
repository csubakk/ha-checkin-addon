import sqlite3
import json
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path

DB_PATH = "/config/guestbook.db"

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

origins = [
    "https://teszt.tapexpert.eu",
    "https://api.teszt.tapexpert.eu"
]

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
        "guest_first_name": row["guest_first_name"],
        "guest_last_name": row["guest_last_name"],
        "nationality": row["nationality"] or ""
    }

@app.post("/local/checkin_data/{token}.submit")
async def submit_guest_data(token: str, nationality: str = Form(...)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("UPDATE guest_bookings SET nationality = ?, updated_at = datetime('now') WHERE access_token = ?", (nationality, token))
    conn.commit()
    affected = cursor.rowcount
    conn.close()

    if affected == 0:
        raise HTTPException(status_code=404, detail="Token not found")

    return {"status": "ok", "message": "Adatok frissítve."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8124)
