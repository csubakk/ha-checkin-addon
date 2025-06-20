from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
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
    existing: str = Form("0"),
    delete: str = Form("0")
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    is_existing = existing == "1"
    is_delete = delete == "1"

    if is_delete:
        cursor.execute("""
            DELETE FROM guest_bookings
            WHERE guest_house_id = ? AND checkin_time = ?
        """, (guest_house_id, checkin_time))

    elif is_existing:
        cursor.execute("""
            UPDATE guest_bookings SET
                guest_first_name = ?, guest_last_name = ?, guest_email = ?, guest_phone = ?,
                checkout_time = ?, guest_count = ?, notes = ?, created_by = ?
            WHERE guest_house_id = ? AND checkin_time = ?
        """, (
            guest_first_name, guest_last_name, guest_email, guest_phone,
            checkout_time, guest_count, notes, created_by,
            guest_house_id, checkin_time
        ))

    else:
        # Új foglalás esetén ellenőrzés, hogy van-e ütközés
        cursor.execute("""
            SELECT id FROM guest_bookings
            WHERE guest_house_id = ? AND (
                (checkin_time <= ? AND checkout_time >= ?) OR
                (checkin_time <= ? AND checkout_time >= ?) OR
                (checkin_time >= ? AND checkout_time <= ?)
            )
        """, (
            guest_house_id, checkin_time, checkin_time,
            checkout_time, checkout_time,
            checkin_time, checkout_time
        ))
        if cursor.fetchone():
            return HTMLResponse(f"""
                <html><body>
                <h2 style='color:red'>Erre a napra ({checkin_time}) már van foglalás ebben a házban.</h2>
                <a href="/calendar">Vissza</a>
                </body></html>
            """)

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
