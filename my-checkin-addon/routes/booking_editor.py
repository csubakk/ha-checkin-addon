from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime, timedelta
import uuid
import re
from services import notifications

router = APIRouter()

DB_PATH = "/config/guestbook.db"
templates = Jinja2Templates(directory="/app/templates")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^(?:\+|00)?\d{9,15}$")
HOUSE_IDS = ["1", "2"]

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
    checkin_dt = datetime.fromisoformat(date)
    default_checkout = (checkin_dt + timedelta(days=1)).date().isoformat()

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
        "checkout_time": default_checkout,
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
        "guest": data,
        "mode": "Foglalás szerkesztése" if booking else "Új foglalás",
        "button": "Mentés" if booking else "Létrehozás",
        "guest_house_ids": HOUSE_IDS,
        "original_id": data["id"],
        "existing": bool(data["id"]),
        "error": error,
    })

@router.get("/confirm_delete", response_class=HTMLResponse)
async def confirm_delete(request: Request, booking_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM guest_bookings WHERE id = ?", (booking_id,))
    booking = cursor.fetchone()
    conn.close()

    if not booking:
        raise HTTPException(status_code=404, detail="Foglalás nem található.")

    return templates.TemplateResponse("confirm_delete.html", {
        "request": request,
        "booking_id": booking_id,
        "guest_name": f"{booking['guest_first_name']} {booking['guest_last_name']}",
        "checkin": booking["checkin_time"],
        "checkout": booking["checkout_time"]
    })

@router.post("/delete_booking")
async def delete_booking(booking_id: int = Form(...)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM guest_bookings WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/calendar", status_code=303)

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

    cleaned_phone = re.sub(r"[^\d\+]", "", guest_phone.strip())

    if not guest_first_name.strip() or not guest_last_name.strip():
        conn.close()
        error_msg = "A vendég neve nem lehet üres."
    elif not guest_email or not EMAIL_REGEX.fullmatch(guest_email.strip()):
        conn.close()
        error_msg = "Hibás vagy hiányzó email cím!"
        with open("/config/debug.log", "a") as f:
            f.write(f"[DEBUG] Beérkezett email: '{guest_email}'\n")
    elif not cleaned_phone or not PHONE_REGEX.match(cleaned_phone):
        conn.close()
        error_msg = "Hibás telefonszám! Kérjük, adjon meg legalább 9 számjegyet, + vagy 00 előtaggal."
        with open("/config/debug.log", "a") as f:
            f.write(f"[DEBUG] Beérkezett telefonszam: '{guest_phone.strip()}'\n")
            f.write(f"[DEBUG] Tisztitott telefonszam: '{cleaned_phone}'\n")
    else:
        error_msg = None

    if error_msg:
        guest_data = {
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
        return templates.TemplateResponse("edit_booking.html", {
            "request": request,
            "guest": guest_data,
            "mode": "Foglalás szerkesztése" if original_id else "Új foglalás",
            "button": "Mentés" if original_id else "Létrehozás",
            "guest_house_ids": HOUSE_IDS,
            "original_id": original_id,
            "existing": bool(original_id),
            "error": error_msg
        })

    guest_phone = cleaned_phone

    try:
        checkin_dt = datetime.fromisoformat(checkin_time)
        checkout_dt = datetime.fromisoformat(checkout_time)
    except ValueError:
        form_data = await request.form()
        return templates.TemplateResponse("edit_booking.html", {
            "request": request,
            "guest": form_data,
            "mode": "Foglalás szerkesztése" if original_id else "Új foglalás",
            "button": "Mentés" if original_id else "Létrehozás",
            "guest_house_ids": HOUSE_IDS,
            "original_id": original_id,
            "existing": bool(original_id),
            "error": "Dátum formátuma hibás."
        })

    if checkout_dt <= checkin_dt:
        form_data = await request.form()
        return templates.TemplateResponse("edit_booking.html", {
            "request": request,
            "guest": form_data,
            "mode": "Foglalás szerkesztése" if original_id else "Új foglalás",
            "button": "Mentés" if original_id else "Létrehozás",
            "guest_house_ids": HOUSE_IDS,
            "original_id": original_id,
            "existing": bool(original_id),
            "error": "Távozás nem lehet az érkezés előtt vagy azonos nap."
        })

    conflict_days = []
    for i in range((checkout_dt - checkin_dt).days):
        d = checkin_dt + timedelta(days=i)
        d_str = d.isoformat()
        if original_id:
            cursor.execute("""
                SELECT id FROM guest_bookings
                WHERE guest_house_id = ?
                  AND id != ?
                  AND date(checkin_time) <= date(?)
                  AND date(checkout_time) > date(?)
            """, (guest_house_id, original_id, d_str, d_str))
        else:
            cursor.execute("""
                SELECT id FROM guest_bookings
                WHERE guest_house_id = ?
                  AND date(checkin_time) <= date(?)
                  AND date(checkout_time) > date(?)
            """, (guest_house_id, d_str, d_str))

        if cursor.fetchone():
            conflict_days.append(d_str)

    if conflict_days:
        formatted_days = [datetime.fromisoformat(d).strftime('%Y-%m-%d') for d in conflict_days]
        conn.close()
        guest_data = {
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

        return templates.TemplateResponse("edit_booking.html", {
            "request": request,
            "guest": guest_data,
            "mode": "Foglalás szerkesztése" if original_id else "Új foglalás",
            "button": "Mentés" if original_id else "Létrehozás",
            "guest_house_ids": HOUSE_IDS,
            "original_id": original_id,
            "existing": bool(original_id),
            "error": f"Ütközés: már van foglalás ezeken a napokon: {', '.join(formatted_days)}"
        })

    now = datetime.now().isoformat(timespec='seconds')
    access_token = str(uuid.uuid4()) if not original_id else None

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
        booking_id = original_id
    else:
        cursor.execute("""
            INSERT INTO guest_bookings (
                guest_first_name, guest_last_name, birth_date, birth_place,
                nationality, document_type, document_number, cnp,
                address, travel_purpose, guest_email, guest_phone,
                guest_count, notes, guest_house_id,
                checkin_time, checkout_time, created_by,
                created_at, updated_at, access_token
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            guest_first_name, guest_last_name, birth_date, birth_place, nationality,
            document_type, document_number, cnp, address, travel_purpose,
            guest_email, guest_phone, guest_count, notes, guest_house_id,
            checkin_time, checkout_time, created_by,
            now, now, access_token
        ))
        booking_id = cursor.lastrowid

    conn.commit()
    conn.close()

    if not original_id:
        try:
            notifications.send_guest_email(booking_id)
            notifications.send_checkin_link(booking_id)
        except Exception as e:
            with open("/config/debug.log", "a") as f:
                f.write(f"[HIBA] Emailküldés hiba: {str(e)}\n")

    return RedirectResponse(url=f"/calendar", status_code=303)
