# services/notifications.py
import os
import smtplib
import sqlite3
import ssl
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from dotenv import load_dotenv
from translations.email_templates import EMAIL_TEMPLATES

load_dotenv("/config/.env")

context = ssl.create_default_context()

def get_config():
    return {
        "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD"),
        "SMTP_SERVER": os.getenv("SMTP_SERVER"),
        "SMTP_PORT": int(os.getenv("SMTP_PORT", 587)),
        "SMTP_USER": os.getenv("SMTP_USER"),
        "SENDER_EMAIL": os.getenv("SENDER_EMAIL"),
        "SENDER_NAME": os.getenv("SENDER_NAME"),
        "SENDER_SIGNATURE": os.getenv("SENDER_SIGNATURE"),
        "SENDER_PHONE": os.getenv("SENDER_PHONE"),
        "BASE_URL": os.getenv("BASE_URL"),
        "DB_PATH": "/config/guestbook.db"
    }

def send_email(recipient: str, subject: str, body: str, message_id: str = None):
    cfg = get_config()

    msg = MIMEMultipart()
    msg["From"] = f"{cfg['SENDER_NAME']} <{cfg['SENDER_EMAIL']}>"
    msg["To"] = recipient
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = message_id or make_msgid()
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(cfg["SMTP_SERVER"], cfg["SMTP_PORT"]) as server:
            server.starttls(context=context)
            server.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
            server.sendmail(cfg["SENDER_EMAIL"], recipient, msg.as_string())
        return True
    except Exception as e:
        print(f"[HIBA] Email küldés sikertelen: {recipient} – {e}")
        return False

def get_email_content(lang, template_key, **kwargs):
    cfg = get_config()
    lang = lang if lang in EMAIL_TEMPLATES else "en"
    template = EMAIL_TEMPLATES[lang]
    subject = template[f"{template_key}_subject"]
    body = template[f"{template_key}_body"].format(
        signature=cfg["SENDER_SIGNATURE"],
        phone=cfg["SENDER_PHONE"],
        email=cfg["SENDER_EMAIL"],
        **kwargs
    )
    return subject, body

def send_guest_email(booking_id: int):
    cfg = get_config()
    conn = sqlite3.connect(cfg["DB_PATH"])
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
    lang = row.get("lang") or "en"

    subject, body = get_email_content(lang, "confirmation", name=name, arrival=arrival, departure=departure, house=house)
    return send_email(recipient, subject, body, message_id=f"<guest-{row['id']}@tapexpert.eu>")

def send_checkin_link(booking_id: int):
    cfg = get_config()
    conn = sqlite3.connect(cfg["DB_PATH"])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM guest_bookings WHERE id = ?", (booking_id,))
    row = cursor.fetchone()

    if not row:
        print(f"Booking not found: {booking_id}")
        return False

    checkin_time_raw = row["checkin_time"]
    try:
        checkin_date = datetime.strptime(checkin_time_raw, "%Y-%m-%d %H:%M:%S").date()
    except ValueError:
        checkin_date = datetime.strptime(checkin_time_raw, "%Y-%m-%d").date()

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    if checkin_date not in [today, tomorrow]:
        print(f"[INFO] Nem küldünk check-in linket, mert az érkezés nem ma vagy holnap: {checkin_date}")
        return False

    recipient = row["guest_email"]
    token = row["access_token"]
    name = f"{row['guest_first_name']} {row['guest_last_name']}"
    arrival = row["checkin_time"]
    house = row["guest_house_id"]
    link = f"{cfg['BASE_URL']}?token={token}"
    lang = row.get("lang") or "en"

    subject, body = get_email_content(lang, "checkin", name=name, arrival=arrival, house=house, link=link)
    send_email(recipient, subject, body)

    cursor.execute("""
        UPDATE guest_bookings
        SET checkin_email_sent_at = datetime('now')
        WHERE id = ?
    """, (booking_id,))
    conn.commit()
    conn.close()
    return True

def send_checkin_links_for_all():
    cfg = get_config()
    conn = sqlite3.connect(cfg["DB_PATH"])
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
    cfg = get_config()
    conn = sqlite3.connect(cfg["DB_PATH"])
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
        link = f"{cfg['BASE_URL']}?token={token}"
        lang = row.get("lang") or "en"

        subject, body = get_email_content(lang, "reminder", name=name, arrival=arrival_date, link=link)
        send_email(recipient, subject, body)
        count += 1

    return count

def send_access_link(booking_id: int):
    cfg = get_config()
    conn = sqlite3.connect(cfg["DB_PATH"])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM guest_bookings WHERE id = ?", (booking_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"Booking not found: {booking_id}")
        return False

    recipient = row["guest_email"]
    token = row["access_token"]
    name = f"{row['guest_first_name']} {row['guest_last_name']}"
    link = f"{cfg['BASE_URL']}?token={token}"
    lang = row.get("lang") or "en"

    subject, body = get_email_content(lang, "access", name=name, link=link)
    return send_email(recipient, subject, body, message_id=f"<access-{row['id']}@tapexpert.eu>")
