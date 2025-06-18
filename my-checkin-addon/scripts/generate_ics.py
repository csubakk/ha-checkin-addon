import sqlite3
from ics import Calendar, Event
from datetime import datetime
import os

DB_PATH = "/config/guestbook.db"
ICS_OUTPUT = "/config/bookings.ics"

def generate_calendar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT guest_first_name, guest_last_name, guest_house_id, checkin_time, checkout_time
        FROM guest_bookings
        WHERE checkin_time IS NOT NULL AND checkout_time IS NOT NULL
    """)
    rows = cursor.fetchall()
    conn.close()

    calendar = Calendar()

    for row in rows:
        try:
            checkin = datetime.fromisoformat(row["checkin_time"])
            checkout = datetime.fromisoformat(row["checkout_time"])
        except Exception as e:
            continue  # rossz dátumformátum

        name = f"{row['guest_first_name']} {row['guest_last_name']}".strip()
        house = f"Ház {row['guest_house_id']}"
        summary = f"{house}: {name}"

        event = Event()
        event.name = summary
        event.begin = checkin
        event.end = checkout
        event.description = f"{name} - {house}"

        calendar.events.add(event)

    with open(ICS_OUTPUT, "w") as f:
        f.writelines(calendar)

    print(f"📅 ICS fájl frissítve: {ICS_OUTPUT}")

if __name__ == "__main__":
    generate_calendar()
