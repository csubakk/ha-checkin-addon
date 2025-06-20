from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime, timedelta

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
async def edit_booking(request: Request, date: str, house_id: str, error: str = "", guest: dict = None):
    booking = get_booking_by_date_and_house(date, house_id)
    checkin_dt = datetime.fromisoformat(date)
    default_checkout = (checkin_dt + timedelta(days=1)).date().isoformat()

    data = guest or {
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
        "checkout_time": default_checkout,
        "created_by": "Csaba",
        "id": ""
    }
    if booking and not guest:
        for key in data:
            if key in booking:
                data[key] = booking[key] or data[key]
        data["id"] = booking["id"]

    return templates.TemplateResponse("edit_booking.html", {
        "request": request,
        "guest": data,
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

    form_data = {
        "guest_first_name": guest_first_name,
        "guest_last_name": guest_last_name,
        "birth_date": birth_date,
        "birth_place": birth_place,
        "nationality": nationality,
        "document_type": document_type,
        "document_number": document_number,
        "cnp": cnp,
        "address": address,
        "travel_purpose": travel_purpose,
        "guest_email": guest_email,
        "guest_phone": guest_phone,
        "guest_count": guest_count,
        "notes": notes,
        "guest_house_id": guest_house_id,
        "checkin_time": checkin_time,
        "checkout_time": checkout_time,
        "created_by": created_by,
        "id": original_id
    }

    try:
        checkin_dt = datetime.fromisoformat(checkin_time)
        checkout_dt = datetime.fromisoformat(checkout_time)
    except ValueError:
        return await edit_booking(request, checkin_time, guest_house_id, error="Dátum formátuma hibás.", guest=form_data)

    if checkout_dt <= checkin_dt:
        return await edit_booking(request, checkin_time, guest_house_id, error="Távozás nem lehet az érkezés előtt vagy azonos nap.", guest=form_data)

    cursor.execute("""
        SELECT * FROM guest_bookings
        WHERE guest_house_id = ?
          AND id != ?
          AND NOT (date(checkout_time) <= date(?) OR date(checkin_time) >= date(?))
    """, (guest_house_id, original_id or 0, checkin_time, checkout_time))
    conflicts = cursor.fetchall()
    if conflicts:
        conflict_days = []
        for row in conflicts:
            existing_start = datetime.fromisoformat(row["checkin_time"]).date()
            existing_end = datetime.fromisoformat(row["checkout_time"]).date()
            for d in range((checkout_dt - checkin_dt).days):
                day = checkin_dt + timedelta(days=d)
                if existing_start <= day < existing_end:
                    conflict_days.append(day.isoformat())
        conn.close()
        return await edit_booking(request, checkin_time, guest_house_id, error=f"Ütközés: az alábbi napokon már van foglalás: {', '.join(conflict_days)}", guest=form_data)

    if original_id:
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

    return RedirectResponse(url=f"/calendar", status_code=303)
