from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime

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
          AND date(?) BETWEEN date(checkin_time) AND date(checkout_time, '-1 day')
    """, (house_id, date))
    existing = cursor.fetchone()
    conn.close()
    return existing

@router.get("/edit_booking", response_class=HTMLResponse)
async def edit_booking(request: Request, date: str, house_id: str, error: str = ""):
    data = {
        "guest_first_name": "",
        "guest_last_name": "",
        "guest_count": "1",
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

    return templates.TemplateResponse("edit_booking.html", {
        "request": request,
        "guest": data,
        "existing": bool(data['id']),
        "original_id": data['id'],
        "mode": "Módosítás" if data['id'] else "Új foglalás",
        "button": "Módosítás" if data['id'] else "Bevitel",
        "guest_house_ids": ["1", "2"],
        "error": error
    })

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
          AND NOT (
            date(?) >= date(checkout_time) OR
            date(?) < date(checkin_time)
          )
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
