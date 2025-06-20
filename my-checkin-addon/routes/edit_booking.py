from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import sqlite3

router = APIRouter()
DB_PATH = "/config/guestbook.db"

@router.get("/edit_booking", response_class=HTMLResponse)
def edit_booking(request: Request, date: str, house: int = 1):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM guest_bookings
        WHERE guest_house_id = ? AND checkin_time <= ? AND checkout_time >= ?
        ORDER BY checkin_time DESC LIMIT 1
    """, (house, date, date))
    booking = cursor.fetchone()
    conn.close()

    data = {
        "guest_first_name": "",
        "guest_last_name": "",
        "guest_email": "",
        "guest_phone": "",
        "guest_house_id": house,
        "checkin_time": date,
        "checkout_time": date,
        "guest_count": 1,
        "notes": "",
        "created_by": ""
    }
    if booking:
        for key in data:
            if key in booking.keys():
                data[key] = booking[key] or data[key]

    is_edit = bool(booking)
    mode = "Módosítás" if is_edit else "Új foglalás"
    button = "Módosít" if is_edit else "Rögzít"
    delete_button = "<button style='background:red;color:white'>Törlés</button>" if is_edit else ""

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
    <form action='/save_booking' method='post'>
        <input type='hidden' name='original_date' value='{date}'>
        <input type='hidden' name='is_edit' value={'1' if is_edit else '0'}>
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
