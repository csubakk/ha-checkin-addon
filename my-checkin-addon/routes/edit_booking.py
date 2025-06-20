from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Template
import sqlite3
from datetime import datetime
import os

router = APIRouter()

DB_PATH = "/config/guestbook.db"
templates = Jinja2Templates(directory="templates") 

def get_existing_booking(house_id: str, date: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM guest_bookings
        WHERE guest_house_id = ?
          AND date(?) BETWEEN date(checkin_time) AND date(checkout_time)
    """, (house_id, date))
    existing = cursor.fetchone()
    conn.close()
    return existing

@router.get("/edit_booking", response_class=HTMLResponse)
async def edit_booking(request: Request, date: str, house_id: str, error: str = ""):
    data = {
        "guest_first_name": "",
        "guest_last_name": "",
        "guest_count": "",
        "checkin_time": date,
        "checkout_time": date,
        "notes": "",
        "created_by": "Csaba",
        "guest_house_id": house_id,
        "id": "",
    }

    existing = get_existing_booking(house_id, date)
    if existing:
        for key in data:
            if key in existing.keys():
                data[key] = existing[key] or data[key]
        data["id"] = existing["id"]

    html = f"""
    <html>
    <head><meta charset='utf-8'><title>Foglalás szerkesztése</title></head>
    <body>
        <h2>Foglalás szerkesztése</h2>
        {'<p style="color:red;">' + error + '</p>' if error else ''}
        <form method='post' action='/save_booking'>
            <input type='hidden' name='id' value='{data["id"]}'>
            <label>Vendég neve:</label>
            <input type='text' name='guest_first_name' value='{data["guest_first_name"]}' required>
            <input type='text' name='guest_last_name' value='{data["guest_last_name"]}' required><br>

            <label>Érkezés:</label>
            <input type='date' name='checkin_time' value='{data["checkin_time"]}' required>
            <label>Távozás:</label>
            <input type='date' name='checkout_time' value='{data["checkout_time"]}' required><br>

            <label>Vendégek száma:</label>
            <input type='number' name='guest_count' value='{data["guest_count"]}' min='1'><br>

            <label>Ház/szoba azonosító:</label>
            <select name='guest_house_id'>
                <option value='1' {'selected' if data["guest_house_id"] == '1' else ''}>1</option>
                <option value='2' {'selected' if data["guest_house_id"] == '2' else ''}>2</option>
            </select><br>

            <label>Megjegyzés:</label>
            <input type='text' name='notes' value='{data["notes"]}'><br>

            <label>Rögzítette:</label>
            <select name='created_by'>
                <option value='Anna' {'selected' if data["created_by"] == 'Anna' else ''}>Anna</option>
                <option value='Csaba' {'selected' if data["created_by"] == 'Csaba' else ''}>Csaba</option>
                <option value='Levente' {'selected' if data["created_by"] == 'Levente' else ''}>Levente</option>
                <option value='Zsolt' {'selected' if data["created_by"] == 'Zsolt' else ''}>Zsolt</option>
            </select><br><br>

            {'<button type="submit">Módosítás</button><a href="/calendar">Vissza</a>' if data['id'] else '<button type="submit">Bevitel</button>'}
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@router.post("/save_booking")
async def save_booking(
    request: Request,
    id: str = Form(""),
    guest_first_name: str = Form(...),
    guest_last_name: str = Form(...),
    guest_count: int = Form(...),
    checkin_time: str = Form(...),
    checkout_time: str = Form(...),
    guest_house_id: str = Form(...),
    notes: str = Form(""),
    created_by: str = Form("Csaba")
):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Ütközésellenőrzés
    cursor.execute("""
        SELECT * FROM guest_bookings
        WHERE guest_house_id = ?
          AND id != ?
          AND date(checkin_time) <= date(?)
          AND date(?) < date(checkout_time)
    """, (guest_house_id, id or 0, checkin_time, checkout_time))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return RedirectResponse(f"/edit_booking?date={checkin_time}&house_id={guest_house_id}&error=Erre a napra ({checkin_time}) már van foglalás ebben a házban.", status_code=303)

    if id:
        cursor.execute("""
            UPDATE guest_bookings SET
              guest_first_name = ?, guest_last_name = ?, guest_count = ?,
              checkin_time = ?, checkout_time = ?, guest_house_id = ?,
              notes = ?, created_by = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (guest_first_name, guest_last_name, guest_count, checkin_time,
              checkout_time, guest_house_id, notes, created_by, id))
    else:
        cursor.execute("""
            INSERT INTO guest_bookings (
              guest_first_name, guest_last_name, guest_count,
              checkin_time, checkout_time, guest_house_id,
              notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (guest_first_name, guest_last_name, guest_count, checkin_time,
              checkout_time, guest_house_id, notes, created_by))

    conn.commit()
    conn.close()
    return RedirectResponse("/calendar", status_code=303)
