from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import sqlite3
import os
import requests
from datetime import datetime, timedelta

router = APIRouter()
DB_PATH = "/config/guestbook.db"

HA_URL = os.getenv("HA_URL")  # például: https://teszt.tapexpert.eu/api
HA_TOKEN = os.getenv("HA_TOKEN")

NAPOK = ['H', 'K', 'Sze', 'Cs', 'P', 'Szo', 'V']
HONAPOK = ['', 'jan.', 'feb.', 'márc.', 'ápr.', 'máj.', 'jún.',
           'júl.', 'aug.', 'szep.', 'okt.', 'nov.', 'dec.']


def get_guest_house_ids_from_ha():
    url = f"{HA_URL}/states/input_select.guest_house_id"
    headers = {"Authorization": f"Bearer {HA_TOKEN}"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data["attributes"]["options"]
    except Exception as e:
        print(f"HIBA: Nem sikerült lekérni a szobalistát HA-ból: {e}")
        return ["1"]  # Alapértelmezésként 1 szoba


@router.get("/calendar", response_class=HTMLResponse)
def calendar_page(request: Request):
    room_ids = get_guest_house_ids_from_ha()
    multiple_rooms = len(room_ids) > 1

    today = datetime.today().date()
    start_date = today - timedelta(days=7)
    end_date = today + timedelta(weeks=6)
    days = [(start_date + timedelta(days=i)) for i in range((end_date - start_date).days + 1)]

    # DB lekérdezés
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in room_ids)
    cursor.execute(f"""
        SELECT guest_first_name, guest_last_name, checkin_time, checkout_time, guest_house_id
        FROM guest_bookings
        WHERE guest_house_id IN ({placeholders})
    """, room_ids)
    bookings = cursor.fetchall()
    conn.close()

    # Foglalások rendezése szobánként és dátum szerint
    date_map = {rid: {} for rid in room_ids}
    for row in bookings:
        fname = row["guest_first_name"] or ""
        lname = row["guest_last_name"] or ""
        name = f"{lname} {fname}".strip()
        guest_house = str(row["guest_house_id"])
        try:
            checkin = datetime.fromisoformat(row["checkin_time"]).date()
            checkout = datetime.fromisoformat(row["checkout_time"]).date()
            for d in range((checkout - checkin).days + 1):
                day = checkin + timedelta(days=d)
                date_map[guest_house][day] = name
        except:
            continue

    # Táblázat építése
    rows = []
    for d in days:
        iso = d.isoformat()
        day_label = f"{d.year}. {HONAPOK[d.month]} {d.day}."
        dow = NAPOK[d.weekday()]
        weekend = d.weekday() in [5, 6]
        is_today = (d == today)

        row = f"<tr class='{'weekend' if weekend else ''} {'today' if is_today else ''}'>"
        row += f"<td>{day_label}</td><td>{dow}</td>"

        for rid in room_ids:
            guest = date_map.get(rid, {}).get(d, "")
            cell = f"<a href='/edit_booking?date={iso}&house_id={rid}'>{guest or '·'}</a>"
            row += f"<td>{cell}</td>"

        row += "</tr>"
        rows.append(row)

    # HTML generálás
    th_cells = "<th>Dátum</th><th>Nap</th>" + "".join(
        f"<th>{rid}. szoba</th>" for rid in room_ids)

    table_html = f"""
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Foglalási naptár</title>
        <style>
            body {{
                font-family: sans-serif;
                margin: 20px;
                font-size: 1em;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                table-layout: fixed;
            }}
            th, td {{
                padding: 6px 8px;
                border: 1px solid #ccc;
                text-align: left;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
            th:nth-child(1), td:nth-child(1) {{ width: 9em; }}
            th:nth-child(2), td:nth-child(2) {{ width: 3em; text-align: center; }}
            tr.weekend {{ background-color: #e0f5e0; }}
            tr.today {{ background-color: #ffe0e0; font-weight: bold; }}
            .nav {{
                margin: 10px 0;
            }}
            .nav a {{
                text-decoration: none;
                margin-right: 10px;
                background: #eee;
                padding: 5px 10px;
                border-radius: 4px;
                color: black;
            }}
            a {{
                color: black;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            @media (max-width: 600px) {{
                body {{ font-size: 1.0em; }}
                th, td {{ padding: 6px 6px; }}
                td a {{ font-size: 0.95em; }}
            }}
        </style>
    </head>
    <body>
        <h2>Foglalási naptár</h2>
        <div class="nav">
            <a href="#">⬅️ Vissza</a>
            <a href="#">Előre ➡️</a>
        </div>
        <table>
            <thead>
                <tr>{th_cells}</tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
    </body>
    </html>
    """

    return HTMLResponse(content=table_html)
