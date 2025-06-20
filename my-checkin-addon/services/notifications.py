# services/notifications.py
import os
import smtplib
import sqlite3
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from dotenv import load_dotenv

load_dotenv("/config/.env")

SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = os.getenv("SENDER_NAME")
BASE_URL = os.getenv("BASE_URL")
DB_PATH = "/config/guestbook.db"

context = ssl.create_default_context()

def send_email(recipient: str, subject: str, body: str, message_id: str = None):
    msg = MIMEMultipart()
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = recipient
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = message_id or make_msgid()
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
        return True
    except Exception as e:
        print(f"[HIBA] Email küldés sikertelen: {recipient} – {e}")
        return False


def send_guest_email(booking_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM guest_bookings WHERE id = ?", (booking_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"Booking not found: {booking_id}")
        return False

    recipient = row["guest_email"]
    name = f"{row['guest_first_name']} {row['guest_last_name']}"
    arrival = row["checkin_time"]
    departure = row["checkout_time"]
    house = row["guest_house_id"]

    body = f"""\
Kedves {name},

Köszönjük a foglalását! Az alábbi adatokkal rögzítettük:
• Érkezés: {arrival}
• Távozás: {departure}
• Ház/Szoba: {house}

További információval hamarosan jelentkezünk.

Üdvözlettel,
Jóska Pista
"""
    send_email(recipient, "Foglalás visszaigazolása", body, message_id=f"<guest-{row['id']}@tapexpert.eu>")
    return True


def send_checkin_link(booking_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM guest_bookings WHERE id = ?", (booking_id,))
    row = cursor.fetchone()

    if not row:
        print(f"Booking not found: {booking_id}")
        return False

    recipient = row["guest_email"]
    token = row["access_token"]
    name = f"{row['guest_first_name']} {row['guest_last_name']}"
    arrival = row["checkin_time"]
    house = row["guest_house_id"]
    link = f"{BASE_URL}?token={token}"

    body = f"""\
Kedves {name},

Emlékeztetőül küldjük a holnapi érkezés részleteit:
• Érkezés: {arrival}
• Ház/Szoba: {house}

Kérjük, töltse ki az online check-in űrlapot az alábbi linken:

{link}

Köszönjük, és kellemes utazást kívánunk!

Üdvözlettel,
Jóska Pista
"""
    send_email(recipient, "Online Check-in link", body)

    cursor.execute("""
        UPDATE guest_bookings
        SET checkin_email_sent_at = datetime('now')
        WHERE id = ?
    """, (booking_id,))
    conn.commit()
    conn.close()
    return True


def send_checkin_links_for_all():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM guest_bookings
        WHERE checkin_time <= DATE('now', '+1 day')
          AND checkin_email_sent_at IS NULL
    """)
    rows = cursor.fetchall()
    conn.close()

    count = 0
    for row in rows:
        send_checkin_link(row["id"])
        count += 1
    return count


def send_checkin_reminders_for_today():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM guest_bookings
        WHERE DATE(checkin_time) = DATE('now')
          AND checkin_email_sent_at IS NOT NULL
          AND (
            birth_date IS NULL OR birth_date = '' OR
            birth_place IS NULL OR birth_place = '' OR
            nationality IS NULL OR nationality = '' OR
            document_type IS NULL OR document_type = '' OR
            document_number IS NULL OR document_number = '' OR
            address IS NULL OR address = '' OR
            signature IS NULL OR signature = ''
          )
    """)
    rows = cursor.fetchall()
    conn.close()

    count = 0
    for row in rows:
        recipient = row["guest_email"]
        token = row["access_token"]
        name = f"{row['guest_first_name']} {row['guest_last_name']}"
        arrival_date = row["checkin_time"].split(" ")[0]
        link = f"{BASE_URL}?token={token}"

        body = f"""\
Kedves {name},

Ez egy emlékeztető, hogy Ön ma érkezik hozzánk ({arrival_date}).  
Kérjük, ha még nem tette meg, töltse ki az online check-in űrlapot az alábbi linken:

{link}

Ez segít gyorsítani a bejelentkezést és egyszerűsíti az adminisztrációt.

Köszönjük, és jó utat kívánunk!

Üdvözlettel,  
Jóska Pista
"""
        send_email(recipient, "Emlékeztető – Online Check-in", body)
        count += 1

    return count
