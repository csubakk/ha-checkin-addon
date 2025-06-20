from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3

router = APIRouter()

DB_PATH = "/config/guestbook.db"
templates = Jinja2Templates(directory="/app/templates")

def get_booking_by_date_and_house(checkin_date: str, guest_house_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM guest_bookings
        WHERE date(checkin_time) <= date(?) AND date(checkout_time) > date(?)
          AND guest_house_id = ?
        LIMIT 1
    """, (checkin_date, checkin_date, guest_house_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

@router.get("/edit_booking", response_class=HTMLResponse)
async def edit_booking(request: Request, date: str, house_id: str, error: str = ""):
    booking = get_booking_by_date_and_house(date, house_id)
    data = {
        "guest_first_name": "",
        "guest_last_name": "",
        "birth_date": "",
        "birth_place": "",
        "nationality": "",
        "document_type": "",
        "document_number": "",
        "cnp": "",
        "address": "",
        "travel_purpose": "",
        "guest_email": "",
        "guest_phone": "",
        "guest_count": 1,
        "notes": "",
        "guest_house_id": house_id,
        "checkin_time": date,
        "checkout_time": date,
        "created_by": "Csaba",
        "id": ""
    }
    if booking:
        for key in data:
            if key in booking:
                data[key] = booking[key] or data[key]
        data["id"] = booking["id"]

    return templates.TemplateResponse("edit_booking.html", {
        "request": request,
        "data": data,
        "mode": "Foglalás szerkesztése" if booking else "Új foglalás",
        "button": "Mentés" if booking else "Létrehozás",
        "guest_house_ids": ["1", "2"],
        "original_id": data["id"],
        "existing": bool(data["id"]),
        "error": error,
    })


@router.post("/save_booking")
async def save_booking(
    request: Request,
    guest_first_name: str = Form(...),
    guest_last_name: str = Form(...),
    birth_date: str = Form(""),
    birth_place: str = Form(""),
    nationality: str = Form(""),
    document_type: str = Form(""),
    document_number: str = Form(""),
    cnp: str = Form(""),
    address: str = Form(""),
    travel_purpose: str = Form(""),
    guest_email: str = Form(""),
    guest_phone: str = Form(""),
    guest_count: int = Form(1),
    notes: str = Form(""),
    guest_house_id: str = Form(...),
    checkin_time: str = Form(...),
    checkout_time: str = Form(...),
    created_by: str = Form(""),
    original_id: str = Form("")
):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if original_id:
        cursor.execute("SELECT * FROM guest_bookings WHERE id = ?", (original_id,))
        existing = cursor.fetchone()
        if not existing:
            conn.close()
            raise HTTPException(status_code=404, detail="Nem található a foglalás azonosító alapján.")

        cursor.execute("""
            SELECT * FROM guest_bookings
            WHERE guest_house_id = ?
              AND id != ?
              AND NOT (date(checkout_time) <= date(?) OR date(checkin_time) >= date(?))
        """, (guest_house_id, original_id, checkin_time, checkout_time))
        conflict = cursor.fetchone()
        if conflict:
            conn.close()
            raise HTTPException(status_code=400, detail="Ütközés: már van foglalás ebben az időszakban.")

        cursor.execute("""
            UPDATE guest_bookings SET
                guest_first_name = ?, guest_last_name = ?, birth_date = ?, birth_place = ?,
                nationality = ?, document_type = ?, document_number = ?, cnp = ?, address = ?,
                travel_purpose = ?, guest_email = ?, guest_phone = ?, guest_count = ?,
                notes = ?, guest_house_id = ?, checkin_time = ?, checkout_time = ?,
                created_by = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (
            guest_first_name, guest_last_name, birth_date, birth_place, nationality,
            document_type, document_number, cnp, address, travel_purpose,
            guest_email, guest_phone, guest_count, notes, guest_house_id,
            checkin_time, checkout_time, created_by, original_id
        ))

    else:
        cursor.execute("""
            SELECT * FROM guest_bookings
            WHERE guest_house_id = ?
              AND NOT (date(checkout_time) <= date(?) OR date(checkin_time) >= date(?))
        """, (guest_house_id, checkin_time, checkout_time))
        conflict = cursor.fetchone()
        if conflict:
            conn.close()
            raise HTTPException(status_code=400, detail="Ütközés: már van foglalás ebben az időszakban.")

        cursor.execute("""
            INSERT INTO guest_bookings (
                guest_first_name, guest_last_name, birth_date, birth_place,
                nationality, document_type, document_number, cnp,
                address, travel_purpose, guest_email, guest_phone,
                guest_count, notes, guest_house_id,
                checkin_time, checkout_time, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            guest_first_name, guest_last_name, birth_date, birth_place, nationality,
            document_type, document_number, cnp, address, travel_purpose,
            guest_email, guest_phone, guest_count, notes, guest_house_id,
            checkin_time, checkout_time, created_by
        ))

    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/edit_booking?date={checkin_time}&house_id={guest_house_id}", status_code=303)
