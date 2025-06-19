from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
import sqlite3
from datetime import datetime

router = APIRouter()
DB_PATH = "/config/guestbook.db"

@router.post("/save_booking")
def save_booking(
    guest_first_name: str = Form(...),
    guest_last_name: str = Form(...),
    guest_email: str = Form(""),
    guest_phone: str = Form(""),
    guest_house_id: int = Form(...),
    checkin_time: str = Form(...),
    checkout_time: str = Form(...),
    guest_count: int = Form(...),
    notes: str = Form(""),
    created_by: str = Form(...),
    existing: bool = Form(False),
    delete: bool = Form(False)
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if delete:
        cursor.execute("""
            DELETE FROM guest_bookings
            WHERE guest_house_id = ? AND checkin_time = ?
        """, (guest_house_id, checkin_time))

    elif existing:
        cursor.execute("""
            UPDATE guest_bookings
            SET guest_first_name = ?, guest_last_name = ?, guest_email = ?, guest_phone = ?,
                checkout_time = ?, guest_count = ?, notes = ?, created_by = ?
            WHERE guest_house_id = ? AND checkin_time = ?
        """, (
            guest_first_name, guest_last_name, guest_email, guest_phone,
            checkout_time, guest_count, notes, created_by,
            guest_house_id, checkin_time
        ))

    else:
        cursor.execute("""
            INSERT INTO guest_bookings (
                guest_first_name, guest_last_name, guest_email, guest_phone,
                guest_house_id, checkin_time, checkout_time,
                guest_count, notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            guest_first_name, guest_last_name, guest_email, guest_phone,
            guest_house_id, checkin_time, checkout_time,
            guest_count, notes, created_by
        ))

    conn.commit()
    conn.close()

    return RedirectResponse(url="/calendar", status_code=303)
