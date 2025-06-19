from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime, timedelta
import locale

router = APIRouter()
DB_PATH = "/config/guestbook.db"

# Magyar lokalizáció

@router.get("/calendar", response_class=HTMLResponse)
def calendar_page(request: Request):
    today = datetime.today().date()
    start_date = today - timedelta(days=7)
    end_date = today + timedelta(weeks=6)
    days = [(start_date + timedelta(days=i)) for i in range((end_date - start_date).days + 1)]

    napok = ['H', 'K', 'Sze', 'Cs', 'P', 'Szo', 'V']
    honapok = [
        '', 'jan.', 'feb.', 'márc.', 'ápr.', 'máj.', 'jún.',
        'júl.', 'aug.', 'szep.', 'okt.', 'nov.', 'dec.'
    ]

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT guest_first_name, guest_last_name, checkin_time, checkout_time
        FROM guest_bookings
        WHERE guest_house_id = 1
    """)
    bookings = cursor.fetchall()
    conn.close()

    date_map = {}
    for row in bookings:
        fname = row["guest_first_name"] or ""
        lname = row["guest_last_name"] or ""
        name = f"{lname} {fname}".strip()
        try:
            checkin = datetime.fromisoformat(row["checkin_time"]).date()
            checkout = datetime.fromisoformat(row["checkout_time"]).date()
            for d in range((checkout - checkin).days + 1):
                day = checkin + timedelta(days=d)
                date_map[day] = name
        except:
            continue

    rows = []
    for d in days:
        iso = d.isoformat()
        day_label = f"{d.year}. {honapok[d.month]} {d.day}."
        dow = napok[d.weekday()]
        weekend = d.weekday() in [5, 6]
        is_today = (d == today)
        guest = date_map.get(d, "")
        row = f"<tr class='{'weekend' if weekend else ''} {'today' if is_today else ''}'>"
        row += f"<td>{day_label}</td><td>{dow}</td><td>{guest}</td>"
        row += f"<td><button onclick=\"window.open('/edit_booking?date={iso}')\">✏️</button></td></tr>"
        rows.append(row)

    table_html = """
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Foglalási naptár – 1 szoba</title>
        
        <style>
    body {
        font-family: sans-serif;
        margin: 20px;
        font-size: 1em;  /* alapértelmezett mindenre */
    }

    table {
        border-collapse: collapse;
        width: 100%;
        table-layout: fixed;
    }

    th, td {
        padding: 6px 8px;
        border: 1px solid #ccc;
        text-align: left;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    th:nth-child(1), td:nth-child(1) {
        width: 7em;
    }

    th:nth-child(2), td:nth-child(2) {
        width: 3em;
        text-align: center;
    }

    th:nth-child(3), td:nth-child(3) {
        max-width: 10em;
    }

    tr.weekend {
        background-color: #e0f5e0;
    }

    tr.today {
        background-color: #ffe0e0;
        font-weight: bold;
    }

    .nav {
        margin: 10px 0;
    }

    .nav a {
        text-decoration: none;
        margin-right: 10px;
        background: #eee;
        padding: 5px 10px;
        border-radius: 4px;
        color: black;
    }

    @media (max-width: 600px) {
        body {
            font-size: 1.0em;
        }
        th, td {
            padding: 6px 6px;
        }
        th:nth-child(3), td:nth-child(3) {
            max-width: 6em;
        }
    }
</style>
    </head>
    <body>
        <h2>Foglalási naptár – 1. szoba</h2>
        <div class="nav">
            <a href="#">⬅️ Vissza</a>
            <a href="#">Előre ➡️</a>
        </div>
        <table>
            <thead>
                <tr><th>Dátum</th><th>Nap</th><th>Vendég</th><th>Szerkesztés</th></tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </body>
    </html>
    """.replace("{rows}", "\n".join(rows))

    return HTMLResponse(content=table_html)
