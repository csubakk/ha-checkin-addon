from fastapi import APIRouter, Response, HTTPException
import sqlite3
from datetime import datetime, timezone
import os

router = APIRouter()

DB_PATH = "/config/guestbook.db"
EXPORT_FOLDER = "/config/www/ics_exports"
CALENDAR_NAME = "Foglalások"
PROD_ID = "-//tapexpert.eu//GuestCheckin//HU"

os.makedirs(EXPORT_FOLDER, exist_ok=True)

def generate_ics(house_id: str, platform: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    today_str = datetime.now().date().isoformat()
    
    cursor.execute("""
        SELECT checkin_time, checkout_time, ical_uid FROM guest_bookings
        WHERE guest_house_id = ? AND source IS NOT NULL AND source != ? AND checkout_time >= ?
    """, (house_id, platform, today_str))
    
    rows = cursor.fetchall()
    conn.close()

    events = []
    for row in rows:
        try:
            start = datetime.fromisoformat(row["checkin_time"]).strftime("%Y%m%d")
            end = datetime.fromisoformat(row["checkout_time"]).strftime("%Y%m%d")
            dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            uid = row["ical_uid"] or f"{platform}_{house_id}_{start}@tapexpert.eu"
        except Exception:
            continue

        events.append(f"""BEGIN:VEVENT
DTSTART;VALUE=DATE:{start}
DTEND;VALUE=DATE:{end}
DTSTAMP:{dtstamp}
SUMMARY:Szállás foglalás (tapexpert)
UID:{uid}
END:VEVENT""")

    calendar_header = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:{PROD_ID}
METHOD:PUBLISH
CALSCALE:GREGORIAN
X-WR-CALNAME:{CALENDAR_NAME} - {platform}/{house_id}
X-WR-TIMEZONE:UTC"""

    return calendar_header + "\n" + "\n".join(events) + "\nEND:VCALENDAR\n"

@router.get("/ics/{platform}_{house_id}.ics")
async def export_ics_file(platform: str, house_id: str):
    try:
        content = generate_ics(house_id, platform)
        return Response(content=content.strip(), media_type="text/calendar; charset=utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ICS generálás hiba: {str(e)}")
