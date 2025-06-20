from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse
import sqlite3
from datetime import datetime

router = APIRouter()
DB_PATH = "/config/guestbook.db"

def get_booking_form_html(data, is_edit=False, error_msg=""):
    mode = "Módosítás" if is_edit else "Új foglalás"
    button = "Módosít" if is_edit else "Rögzít"
    delete_button = f"<button name='delete' style='background:red;color:white'>Törlés</button>" if is_edit else ""

    error_html = f"<p style='color:red'><strong>{error_msg}</strong></p>" if error_msg else ""

    html = f"""
    <html lang='hu'><head><meta charset='UTF-8'>
    <title>{mode}</title>
    <style>
        body {{ font-family: sans-serif; margin: 2em; }}
        label {{ display: block; margin-top: 1em; }}
        input, select {{ width: 100%; padding: 0.5em; }}
        button {{ margin-top: 1em; padding: 0.5em 1em; }}
    </style></head>
    <body>
    <h2>{mode}</h2>
    {error_html}
    <form action='/save_booking' method='post'>
        <input type='hidden' name='existing' value='{data.get("id", "")}'>
        <label>Vezetéknév <input name='guest_last_name' value='{data['guest_last_name']}'></label>
        <label>Keresztnév <input name='guest_first_name' value='{data['guest_first_name']}'></label>
        <label>Email <input name='guest_email' value='{data['guest_email']}'></label>
        <label>Telefon <input name='guest_phone' value='{data['guest_phone']}'></label>
        <label>Szoba: <select name='guest_house_id'>
            <option value='1' {'selected' if int(data['guest_house_id'])==1 else ''}>1</option>
            <option value='2' {'selected' if int(data['guest_house_id'])==2 else ''}>2</option>
        </select></label>
        <label>Érkezés: <input type='date' name='checkin_time' value='{data['checkin_time']}'></label>
        <label>Távozás: <input type='date' name='checkout_time' value='{data['checkout_time']}'></label>
        <label>Vendégek száma <input type='number' name='guest_count' value='{data['guest_count']}'></label>
        <label>Megjegyzés <input name='notes' value='{data['notes']}'></label>
        <label>Rögzítő: <select name='created_by'>
            <option value='Anna' {'selected' if data['created_by']=='Anna' else ''}>Anna</option>
            <option value='Csaba' {'selected' if data['created_by']=='Csaba' else ''}>Csaba</option>
            <option value='Levente' {'selected' if data['created_by']=='Levente' else ''}>Levente</option>
            <option value='Zsolt' {'selected' if data['created_by']=='Zsolt' else ''}>Zsolt</option>
        </select></label>
        <button type='submit'>{button}</button>
        {delete_button}
    </form></body></html>
    """
    return HTMLResponse(content=html)


@router.post("/save_booking")
def save_booking(
    request: Request,
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
    existing: str = Form(""),
    delete: bool = Form(False)
):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    booking_id = int(existing) if existing else -1

    if delete:
        cursor.execute("DELETE FROM guest_bookings WHERE id = ?", (booking_id,))
        conn.commit()
        conn.close()
        return RedirectResponse(url="/calendar", status_code=303)

    # Ellenőrzés: ugyanarra a dátumra ugyanarra a házra ne legyen másik foglalás
    cursor.execute("""
        SELECT COUNT(*) FROM guest_bookings
        WHERE guest_house_id = ? AND checkin_time <= ? AND checkout_time >= ? AND id != ?
    """, (guest_house_id, checkout_time, checkin_time, booking_id))
    count = cursor.fetchone()[0]

    data = {
        "id": booking_id if booking_id > 0 else "",
        "guest_first_name": guest_first_name,
        "guest_last_name": guest_last_name,
        "guest_email": guest_email,
        "guest_phone": guest_phone,
        "guest_house_id": guest_house_id,
        "checkin_time": checkin_time,
        "checkout_time": checkout_time,
        "guest_count": guest_count,
        "notes": notes,
        "created_by": created_by,
    }

    if count > 0:
        conn.close()
        return get_booking_form_html(data, is_edit=bool(existing), error_msg=f"Erre a napra ({checkin_time}) már van foglalás ebben a házban.")

    if existing:
        cursor.execute("""
            UPDATE guest_bookings
            SET guest_first_name = ?, guest_last_name = ?, guest_email = ?, guest_phone = ?,
                guest_house_id = ?, checkin_time = ?, checkout_time = ?,
                guest_count = ?, notes = ?, created_by = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (
            guest_first_name, guest_last_name, guest_email, guest_phone,
            guest_house_id, checkin_time, checkout_time,
            guest_count, notes, created_by, booking_id
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
