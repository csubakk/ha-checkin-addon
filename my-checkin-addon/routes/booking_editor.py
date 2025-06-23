#booking_editor.py
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime, timedelta
import uuid
import re
import os
import requests
import httpx
from services import notifications
from translations.translations import get_translations, tr

router = APIRouter()

HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")
lang = os.getenv("HOST_LANGUAGE", "hu")

DB_PATH = "/config/guestbook.db"
templates = Jinja2Templates(directory="/app/templates")

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^(?:\+|00|07)\d{7,13}$")

async def get_owner_token():
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            f"{HA_URL}/states/input_text.owner_token",
            headers={"Authorization": f"Bearer {HA_TOKEN}"}
        )
        response.raise_for_status()
        return response.json()["state"]

def get_input_select_options(entity_id: str):
    url = f"{HA_URL}/states/{entity_id}"
    headers = {"Authorization": f"Bearer {HA_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("attributes", {}).get("options", [])
    return []


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
async def edit_booking(request: Request, date: str, house_id: str, token: str = "", error: str = ""):
    owner_token = await get_owner_token()
    if token != owner_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    booking = get_booking_by_date_and_house(date, house_id)
    checkin_dt = datetime.fromisoformat(date)
    default_checkout = (checkin_dt + timedelta(days=1)).date().isoformat()
    created_by_options = get_input_select_options("input_select.created_by")
    guest_house_ids = get_input_select_options("input_select.guest_house_id")

    data = {
        "guest_first_name": "",
        "guest_last_name": "",
        "guest_email": "",
        "guest_phone": "",
        "guest_count": 1,
        "notes": "",
        "guest_house_id": house_id,
        "checkin_time": date,
        "checkout_time": default_checkout,
        "created_by": "",
        "id": "",
        "lang": lang
    }
    if booking:
        for key in data:
            if key in booking:
                data[key] = booking[key] or data[key]
        data["id"] = booking["id"]
    
    return templates.TemplateResponse("edit_booking.html", {
        "request": request,
        "guest": data,
        "mode": tr("edit_booking") if booking else tr("new_booking"),
        "button": tr("save") if booking else tr("create"),
        "guest_house_ids": guest_house_ids,
        "created_by_options": created_by_options,
        "lang": lang,
        "original_id": data["id"],
        "existing": bool(data["id"]),
        "error": error,
        "token": token,
        "tr": tr
    })

@router.get("/confirm_delete", response_class=HTMLResponse)
async def confirm_delete(request: Request, booking_id: int, token: str = ""):
    owner_token = await get_owner_token()
    if token != owner_token:
        raise HTTPException(status_code=403, detail="Invalid token")
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
        "checkout": booking["checkout_time"],
        "lang": lang,
        "token": token,
        "tr": tr
    })


@router.post("/delete_booking")
async def delete_booking(booking_id: int = Form(...), token: str = Form(...)):
    owner_token = await get_owner_token()
    if token != owner_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM guest_bookings WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/calendar?token={token}", status_code=303)

@router.post("/save_booking")
async def save_booking(
    request: Request,
    guest_first_name: str = Form(...),
    guest_last_name: str = Form(...),
    guest_email: str = Form(""),
    guest_phone: str = Form(""),
    guest_count: int = Form(1),
    notes: str = Form(""),
    guest_house_id: str = Form(...),
    checkin_time: str = Form(...),
    checkout_time: str = Form(...),
    created_by: str = Form(""),
    original_id: str = Form(""),
    lang: str = Form("hu"),
    guest_lang: str = Form("en"),
    token: str = Form("")
):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cleaned_phone = re.sub(r"[^\d\+]", "", guest_phone.strip())

    guest_house_ids = get_input_select_options("input_select.guest_house_id")
    created_by_options = get_input_select_options("input_select.created_by")

    if not guest_first_name.strip() or not guest_last_name.strip():
        conn.close()
        error_msg = tr("empty_name", lang=lang)
    elif not guest_email or not EMAIL_REGEX.fullmatch(guest_email.strip()):
        conn.close()
        error_msg = tr("invalid_email", lang=lang)
    elif not cleaned_phone or not PHONE_REGEX.match(cleaned_phone):
        conn.close()
        error_msg = tr("invalid_phone", lang=lang)
    else:
        error_msg = None

    if error_msg:
        guest_data = {
            "guest_first_name": guest_first_name,
            "guest_last_name": guest_last_name,
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
            "mode": tr("edit_booking", lang=lang) if original_id else tr("new_booking", lang=lang),
            "button": tr("save", lang=lang) if original_id else tr("create", lang=lang),
            "guest_house_ids": guest_house_ids,
            "created_by_options": created_by_options,
            "original_id": original_id,
            "lang": lang,
            "existing": bool(original_id),
            "error": error_msg,
            "token": token,
            "tr": tr
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
            "mode": tr("edit_booking", lang=lang) if original_id else tr("new_booking", lang=lang),
            "button": tr("save", lang=lang) if original_id else tr("create", lang=lang),
            "guest_house_ids": guest_house_ids,
            "created_by_options": created_by_options,
            "lang": lang,
            "original_id": original_id,
            "existing": bool(original_id),
            "error": tr("date_format_error", ", ".join(formatted_days), lang=lang),
            "token": token,
            "tr": tr
        })

    
    # ✅ Múltbéli check-in tiltása
    if checkin_dt.date() < datetime.now().date():
        guest_data = {
            "guest_first_name": guest_first_name,
            "guest_last_name": guest_last_name,
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
            "mode": tr("edit_booking", lang=lang) if original_id else tr("new_booking", lang=lang),
            "button": tr("save", lang=lang) if original_id else tr("create", lang=lang),
            "guest_house_ids": guest_house_ids,
            "created_by_options": created_by_options,
            "original_id": original_id,
            "lang": lang,
            "existing": bool(original_id),
            "error": tr("checkin_past_error", lang=lang),
            "token": token,
            "tr": tr
        })
    
    if checkout_dt <= checkin_dt:
        form_data = await request.form()
        return templates.TemplateResponse("edit_booking.html", {
            "request": request,
            "guest": form_data,
            "mode": tr("edit_booking", lang=lang) if original_id else tr("new_booking", lang=lang),
            "button": tr("save", lang=lang) if original_id else tr("create", lang=lang),
            "guest_house_ids": guest_house_ids,
            "created_by_options": created_by_options,
            "original_id": original_id,
            "lang": lang,
            "existing": bool(original_id),
            "error": tr("invalid_dates", ", ".join(formatted_days), lang=lang),
            "token": token,
            "tr": tr
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
            "mode": tr("edit_booking", lang=lang) if original_id else tr("new_booking", lang=lang),
            "button": tr("save", lang=lang) if original_id else tr("create", lang=lang),
            "guest_house_ids": guest_house_ids,
            "created_by_options": created_by_options,
            "original_id": original_id,
            "lang": lang,
            "existing": bool(original_id),
            "error": tr("conflict", ", ".join(formatted_days), lang=lang),
            "token": token,
            "tr": tr
        })

    now = datetime.now().isoformat(timespec='seconds')
    access_token = str(uuid.uuid4()) if not original_id else None

    if original_id:
        cursor.execute("""
            UPDATE guest_bookings SET
                guest_first_name = ?, guest_last_name = ?, guest_email = ?, guest_phone = ?,
                guest_count = ?, notes = ?, guest_house_id = ?, checkin_time = ?, checkout_time = ?,
                created_by = ?, lang = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (
            guest_first_name, guest_last_name, guest_email, guest_phone,
            guest_count, notes, guest_house_id, checkin_time, checkout_time,
            created_by, guest_lang, original_id
        ))
        booking_id = original_id
    else:
#        with open("/config/debug.log", "a") as f:
#            f.write("=== ÚJ FOGLALÁS BESZÚRÁSA ===\n")
#            f.write(f"guest_lang: {repr(guest_lang)}\n")
#            f.write(f"access_token: {repr(access_token)}\n")
#            values = (
#                guest_first_name, guest_last_name, None, None, None,
#                None, None, None, None, None, None, 
#                checkin_time, checkout_time, guest_count, notes, None,
#                0, now, now, guest_email, guest_phone,
#                guest_house_id, access_token, created_by, None,
#                guest_lang
#            )
#            f.write(f"Paraméterek száma: {len(values)}\n")
#            f.write(f"Paraméterek: {repr(values)}\n")
#            f.write("==============================\n")
        
        cursor.execute("""
            INSERT INTO guest_bookings (
                guest_first_name, guest_last_name, birth_date, birth_place, nationality,
                document_type, document_number, cnp, address, travel_purpose, signature,
                checkin_time, checkout_time, guest_count, notes, checkin_email_sent_at,
                checkout_completed, created_at, updated_at, guest_email, guest_phone,
                guest_house_id, access_token, created_by, access_email_sent_at, lang
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            guest_first_name, guest_last_name, None, None, None,
            None, None, None, None, None, None, 
            checkin_time, checkout_time, guest_count, notes, None,
            0, now, now, guest_email, guest_phone,
            guest_house_id, access_token, created_by, None,
            guest_lang
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

    return RedirectResponse(url=f"/calendar?token={token}", status_code=303)
