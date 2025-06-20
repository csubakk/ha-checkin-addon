from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse
import sqlite3

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
        # Átfedés ellenőrzése más foglalással
        cursor.execute("""
            SELECT COUNT(*) FROM guest_bookings
            WHERE guest_house_id = ?
              AND checkin_time <= ? AND checkout_time >= ?
              AND NOT (checkin_time = ? AND guest_house_id = ?)
        """, (
            guest_house_id, checkout_time, checkin_time,
            checkin_time, guest_house_id
        ))
        conflict = cursor.fetchone()[0]
        if conflict > 0:
            conn.close()
            return HTMLResponse(
                content=f"<html><body><h2>HIBA</h2><p>Ez az időszak ({checkin_time} – {checkout_time}) átfed másik foglalással.</p><a href='/calendar'>Vissza</a></body></html>",
                status_code=400
            )

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
        # Ellenőrzés új foglalásnál
        cursor.execute("""
            SELECT COUNT(*) FROM guest_bookings
            WHERE guest_house_id = ? AND checkin_time <= ? AND checkout_time >= ?
        """, (guest_house_id, checkin_time, checkin_time))
        exists = cursor.fetchone()[0]
        if exists > 0:
            conn.close()
            return HTMLResponse(
                content=f"<html><body><h2>HIBA</h2><p>Erre a napra ({checkin_time}) már van foglalás ebben a házban.</p><a href='/calendar'>Vissza</a></body></html>",
                status_code=400
            )

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
