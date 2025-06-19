from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime, timedelta
import locale
import os
import requests

router = APIRouter()
DB_PATH = "/config/guestbook.db"
HA_URL = os.getenv("HA_URL", "http://homeassistant:8123")
HA_TOKEN = os.getenv("HA_TOKEN")

@router.get("/calendar", response_class=HTMLResponse)
def calendar_page(request: Request):
    # Magyar nap- és hónapnevek
    napok = ['H', 'K', 'Sze', 'Cs', 'P', 'Szo', 'V']
    honapok = ['', 'jan.', 'feb.', 'márc.', 'ápr.', 'máj.', 'jún.', 'júl.', 'aug.', 'szep.', 'okt.', 'nov.', 'dec.']

    today = datetime.today().date()
    start_date = today - timedelta(days=7)
    end_date = today + timedelta(weeks=6)
    days = [(start_date + timedelta(days=i)) for i in range((end_date - start_date).days + 1)]

    # 🔄 Lekérdezzük az input_select értékeit
    headers = {"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"}
    try:
        r = requests.get(f"{HA_URL}/api/states/input_select.guest_house_id", headers=headers, timeout=5)
        r.raise_for_status()
        options = r.json()["attributes"].get("options", [])
    except Exception as e:
        options = ["1"]  # fallback, ha hiba van

    szobak = sorted(options)[:8]  # max. 8 szoba

    # 🔄 Lekérjük a foglalásokat
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT guest_first_name, guest_last_name, checkin_time, checkout_time, guest_house_id
        FROM guest_bookings
    """)
    bookings = cursor.fetchall()
    conn.close()

    date_map = {szoba: {} for szoba in szobak}
    for row in bookings:
        house = row["guest_house_id"]
        fname = row["guest_first_name"] or ""
        lname = row["guest_last_name"] or ""
        name = f"{lname} {fname}".strip()
        try:
            checkin = datetime.fromisoformat(row["checkin_time"]).date()
            checkout = datetime.fromisoformat(row["checkout_time"]).date()
            for d in range((checkout - checkin).days + 1):
                day = checkin + timedelta(days=d)
                date_map.setdefault(house, {})[day] = name
        except:
            continue

    # 🔄 HTML sorok építése
    rows = []
    for d in days:
        iso = d.isoformat()
        day_label = f"{d.year}. {honapok[d.month]} {d.day}."
        dow = napok[d.weekday()]
        weekend = d.weekday() in [5, 6]
        is_today = (d == today)

        row = f"<tr class='{'weekend' if weekend else ''} {'today' if is_today else ''}'>"
        row += f"<td>{day_label}</td><td>{dow}</td>"
        for szoba in szobak:
            guest = date_map.get(szoba, {}).get(d, "=")
            link = f"/edit_booking?date={iso}&house={szoba}" if guest else "#"
            row += f"<td><a href='{link}'>{guest}</a></td>"
        row += "</tr>"
        rows.append(row)

    # 🔄 Oszlopfejlécek
    header_cells = "<th>Dátum</th><th>Nap</th>" + ''.join([f"<th>Szoba {sz}</th>" for sz in szobak])

    html = f"""
    <!DOCTYPE html>
    <html lang=\"hu\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>Foglalási naptár</title>
        <style>
            body {{ font-family: sans-serif; margin: 20px; font-size: 1em; }}
            table {{ border-collapse: collapse; width: 100%; table-layout: fixed; }}
            th, td {{ padding: 6px 8px; border: 1px solid #ccc; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
            tr.weekend {{ background-color: #e0f5e0; }}
            tr.today {{ background-color: #ffe0e0; font-weight: bold; }}
            .nav {{ margin: 10px 0; }}
            .nav a {{ text-decoration: none; margin-right: 10px; background: #eee; padding: 5px 10px; border-radius: 4px; color: black; }}
            @media (max-width: 600px) {{ body {{ font-size: 1em; }} th, td {{ padding: 6px 6px; }} td {{ max-width: 6em; }} }}
        </style>
    </head>
    <body>
        <h2>Foglalási naptár – {'–'.join(szobak)}. szoba</h2>
        <div class='nav'><a href='#'>⬅️ Vissza</a><a href='#'>Előre ➡️</a></div>
        <table>
            <thead><tr>{header_cells}</tr></thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
