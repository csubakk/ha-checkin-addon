from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template
import sqlite3
from datetime import datetime

router = APIRouter()

DB_PATH = "/config/guestbook.db"

html_template = Template(open("/config/templates/edit_booking.html").read())

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
async def edit_booking(date: str, house_id: str):
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
    return html_template.render(data=data)

@router.post("/save_booking")
async def save_booking(
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
    booking_id: str = Form("")
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    conn.row_factory = sqlite3.Row

    if booking_id:
        # update
        cursor.execute("""
            SELECT * FROM guest_bookings
            WHERE id = ?
        """, (booking_id,))
        existing = cursor.fetchone()
        if not existing:
            conn.close()
            raise HTTPException(status_code=404, detail="Nem található a foglalás azonosító alapján.")

        # ellenőrzés: van-e másik foglalás ugyanarra a szobára, átfedéssel
        cursor.execute("""
            SELECT * FROM guest_bookings
            WHERE guest_house_id = ?
              AND id != ?
              AND NOT (date(checkout_time) <= date(?) OR date(checkin_time) >= date(?))
        """, (guest_house_id, booking_id, checkin_time, checkout_time))
        conflict = cursor.fetchone()
        if conflict:
            conn.close()
            raise HTTPException(status_code=400, detail="Erre az időszakra már van másik foglalás ebben a házban.")

        cursor.execute("""
            UPDATE guest_bookings SET
                guest_first_name = ?,
                guest_last_name = ?,
                birth_date = ?,
                birth_place = ?,
                nationality = ?,
                document_type = ?,
                document_number = ?,
                cnp = ?,
                address = ?,
                travel_purpose = ?,
                guest_email = ?,
                guest_phone = ?,
                guest_count = ?,
                notes = ?,
                guest_house_id = ?,
                checkin_time = ?,
                checkout_time = ?,
                created_by = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (
            guest_first_name, guest_last_name, birth_date, birth_place, nationality,
            document_type, document_number, cnp, address, travel_purpose,
            guest_email, guest_phone, guest_count, notes, guest_house_id,
            checkin_time, checkout_time, created_by, booking_id
        ))
    else:
        # új foglalásnál: ellenőrizzük van-e átfedés
        cursor.execute("""
            SELECT * FROM guest_bookings
            WHERE guest_house_id = ?
              AND NOT (date(checkout_time) <= date(?) OR date(checkin_time) >= date(?))
        """, (guest_house_id, checkin_time, checkout_time))
        conflict = cursor.fetchone()
        if conflict:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Erre az időszakra már van foglalás a kiválasztott házban.")

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
