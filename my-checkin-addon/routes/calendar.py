#calendar.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import sqlite3
import os
from datetime import datetime, timedelta
from translations.translations import tr, get_translations, get_weekday_names, get_month_names

router = APIRouter()
DB_PATH = "/config/guestbook.db"

def get_guest_house_ids_from_ha():
    import requests
    HA_URL = os.getenv("HA_URL", "http://homeassistant.local:8123")
    HA_TOKEN = os.getenv("HA_TOKEN", "")
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.get(f"{HA_URL}/states/input_select.guest_house_id", headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        options = data.get("attributes", {}).get("options", [])
        return [str(opt).strip() for opt in options if str(opt).strip()]
    except Exception as e:
        print("❌ Nem sikerült lekérni a szobaazonosítókat:", e)
        return ["1"]

@router.get("/calendar", response_class=HTMLResponse)
def calendar_page(request: Request, start: str = "", lang: str = None):
    tr_dict = get_translations(lang)
    room_ids = get_guest_house_ids_from_ha()
    multiple_rooms = len(room_ids) > 1

    # dátum paraméter értelmezése
    try:
        start_date = datetime.fromisoformat(start).date() if start else datetime.today().date() - timedelta(days=7)
    except ValueError:
        start_date = datetime.today().date() - timedelta(days=7)

    end_date = start_date + timedelta(days=34)
    days = [(start_date + timedelta(days=i)) for i in range(35)]

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

    date_map = {rid: {} for rid in room_ids}
    for row in bookings:
        fname = row["guest_first_name"] or ""
        lname = row["guest_last_name"] or ""
        name = f"{lname} {fname}".strip()
        guest_house = str(row["guest_house_id"])
        try:
            checkin = datetime.fromisoformat(row["checkin_time"]).date()
            checkout = datetime.fromisoformat(row["checkout_time"]).date()
            for d in range((checkout - checkin).days):
                day = checkin + timedelta(days=d)
                date_map[guest_house][day] = name
        except:
            continue

    HONAPOK = tr_dict["month_names"]
    NAPOK = tr_dict["weekday_names"]
    today = datetime.today().date()

    rows = []
    for d in days:
        iso = d.isoformat()
        if lang == "ro":
            day_label = f"{d.day} {HONAPOK[d.month]} {d.year}"
        else:
            day_label = f"{d.year}. {HONAPOK[d.month]} {d.day}."
        dow = NAPOK[d.weekday()]
        weekend = d.weekday() in [5, 6]
        is_today = (d == today)

        row = f"<tr class='{'weekend' if weekend else ''} {'today' if is_today else ''}'>"
        row += f"<td>{day_label}</td><td>{dow}</td>"

        for rid in room_ids:
            guest = date_map.get(rid, {}).get(d, "")
            cell = f"<a href='/edit_booking?date={iso}&house_id={rid}'>{guest or '---'}</a>"
            row += f"<td>{cell}</td>"

        row += "</tr>"
        rows.append(row)

        prev_start = (start_date - timedelta(days=35)).isoformat()
        next_start = (start_date + timedelta(days=35)).isoformat()
        today_start = (datetime.today().date() - timedelta(days=7)).isoformat()

        lang_param = f"&lang={lang}" if lang else ""

        nav_html = f"""
            <div class="nav">
                <a href="/calendar?start={prev_start}{lang_param}">⬅️ {tr_dict['back']}</a>
                <a href="/calendar?start={today_start}{lang_param}">🏠 {tr_dict.get('home', 'Ma')}</a>
                <a href="/calendar?start={next_start}{lang_param}">{tr_dict['forward']} ➡️</a>
            </div>
        """

    th_cells = f"<th>{tr_dict['date']}</th><th>{tr_dict['day']}</th>" + "".join(
        f"<th>{tr_dict['room'].format(rid)}</th>" for rid in room_ids)

    table_html = f"""
    <!DOCTYPE html>
    <html lang="{lang or 'hu'}">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{tr_dict['title']}</title>
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
        <h2>{tr_dict['title']}</h2>
        {nav_html}
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
