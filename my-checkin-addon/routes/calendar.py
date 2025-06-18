from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import sqlite3
import datetime

router = APIRouter()

@router.get("/admin/foglalasok", response_class=HTMLResponse)
def booking_calendar():
    db_path = "/config/guestbook.db"  # módosítsd, ha máshol van
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    today = datetime.date.today()
    days = [today + datetime.timedelta(days=i) for i in range(70)]  # 10 hét

    # Lekérjük az összes foglalást a tartományban
    cursor.execute("""
        SELECT guest_first_name, guest_last_name, guest_house_id, checkin_time, checkout_time
        FROM guest_bookings
        WHERE DATE(checkout_time) >= ? AND DATE(checkin_time) <= ?
    """, (days[0].isoformat(), days[-1].isoformat()))
    bookings = cursor.fetchall()

    # Szobák listája
    room_ids = sorted(set(str(row[2]) for row in bookings))
    if not room_ids:
        room_ids = ["1", "2", "3"]  # fallback tesztadat esetén

    # Inicializáljuk a táblát
    table = {
        room: {d.isoformat(): "" for d in days}
        for room in room_ids
    }

    for first, last, room, checkin, checkout in bookings:
        name = f"{last} {first[0]}."
        d1 = datetime.date.fromisoformat(checkin[:10])
        d2 = datetime.date.fromisoformat(checkout[:10])
        for d in days:
            if d1 <= d < d2:
                table[str(room)][d.isoformat()] = name

    conn.close()

    # HTML táblázat
    html = """
    <html><head>
    <style>
    table { border-collapse: collapse; font-family: sans-serif; }
    th, td { border: 1px solid #999; padding: 4px 6px; text-align: center; white-space: nowrap; }
    th { background: #eee; position: sticky; top: 0; z-index: 2; }
    tr:first-child td { position: sticky; left: 0; background: #fff; z-index: 1; }
    .occupied { background-color: #fdd; }
    </style></head><body>
    <table><tr><th>Szoba</th>""" + "".join(f"<th>{d.strftime('%m-%d')}</th>" for d in days) + "</tr>\n"

    for room in room_ids:
        html += f"<tr><td><b>{room}</b></td>"
        for d in days:
            guest = table[room][d.isoformat()]
            css = "occupied" if guest else ""
            html += f"<td class='{css}'>{guest}</td>"
        html += "</tr>\n"

    html += "</table></body></html>"
    return HTMLResponse(content=html)
