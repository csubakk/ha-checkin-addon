import sqlite3
import subprocess
import os
import yaml
import requests
from fastapi import FastAPI, HTTPException, Form, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from checkin_meta_api import router as meta_router
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate, make_msgid
from PIL import Image
from io import BytesIO

def generate_guest_pdf(data: dict, path: str, image_path: str = None):
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    # 🌿 Háttér világoszöld színnel
    light_green = HexColor("#CCFFCC")  # világoszöld hex kód
    c.setFillColor(light_green)
    c.rect(0, 0, width, height, fill=True, stroke=False)  # teljes oldalra

    y = height - 50
    c.setFillColorRGB(0, 0, 0)  # vissza fekete szövegszínre

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Vendég check-in adatok")
    y -= 30

    c.setFont("Helvetica", 12)
    for key, value in data.items():
        c.drawString(50, y, f"{key.replace('_', ' ').capitalize()}: {value}")
        y -= 20

    if image_path and os.path.exists(image_path):
        y -= 30
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Igazolvány fotó:")
        y -= 200

        try:
            img = ImageReader(image_path)
            c.drawImage(img, 50, y, width=200, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            c.drawString(50, y, f"(Nem sikerült betölteni a képet: {e})")

    c.save()

# Betöltjük egyszer az .env fájlt és kiolvassuk a szükséges változókat
load_dotenv("/config/.env")
HA_TOKEN = os.getenv("HA_TOKEN")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = os.getenv("SENDER_NAME")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
DB_PATH = "/config/guestbook.db"
SCRIPT_PATH = "/config/scripts/send_access_link.py"
DOOR_MAP_PATH = "/config/guest_door_map.yaml"
HA_URL = os.getenv("HA_URL", "http://homeassistant.local:8123/api/services")
OWNER_EMAIL = os.getenv("OWNER_EMAIL")

app = FastAPI()
app.include_router(meta_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/local/door/{token}/state")
async def get_door_state(token: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT guest_house_id FROM guest_bookings WHERE access_token = ?", (token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Token not found")

    house_id = str(row["guest_house_id"])

    try:
        with open(DOOR_MAP_PATH, "r") as f:
            door_map = yaml.safe_load(f)
        config = door_map[house_id]
        entity_id = config.get("entity_id")

        if not entity_id:
            raise HTTPException(status_code=500, detail="Hiányos ajtókonfiguráció")

        headers = {
            "Authorization": f"Bearer {HA_TOKEN}"
        }

        response = requests.get(
            f"{HA_URL}/states/{entity_id}",
            headers=headers
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"HA válasz: {response.status_code} {response.text}")

        data = response.json()
        return {"state": data["state"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba az állapot lekérdezéskor: {str(e)}")

@app.get("/local/checkin_data/{token}.json")
async def get_guest_data(token: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM guest_bookings WHERE access_token = ?", (token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Token not found")

    return {
        "guest_first_name": row["guest_first_name"] or "",
        "guest_last_name": row["guest_last_name"] or "",
        "nationality": row["nationality"] or "",
        "birth_date": row["birth_date"] or "",
        "birth_place": row["birth_place"] or "",
        "document_type": row["document_type"] or "",
        "document_number": row["document_number"] or "",
        "cnp": row["cnp"] or "",
        "address": row["address"] or "",
        "travel_purpose": row["travel_purpose"] or "",
        "signature": row["signature"] or ""
    }

@app.post("/local/checkin_data/{token}.submit")
async def submit_guest_data(
    request: Request,
    token: str,
    document_photo: UploadFile = File(...),
    guest_first_name: str = Form(...),
    guest_last_name: str = Form(...),
    nationality: str = Form(...),
    birth_date: str = Form(""),
    birth_place: str = Form(""),
    document_type: str = Form(""),
    document_number: str = Form(""),
    cnp: str = Form(""),
    address: str = Form(""),
    travel_purpose: str = Form(""),
    signature: str = Form("")
):

    # 📁 Dokumentumfotó mentése biztonságos módon
    save_path = f"/config/private_docs/{token}_document.jpg"

    image_bytes = await document_photo.read()

    try:
        img = Image.open(BytesIO(image_bytes))
        rgb_img = img.convert("RGB")  # konvertálás biztos JPEG-be
        rgb_img.save(save_path, format="JPEG", quality=90)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Nem sikerült feldolgozni a képet: {str(e)}")

    # 🗃️ Adatbázis frissítés
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE guest_bookings SET
            guest_first_name = ?,
            guest_last_name = ?,
            nationality = ?,
            birth_date = ?,
            birth_place = ?,
            document_type = ?,
            document_number = ?,
            cnp = ?,
            address = ?,
            travel_purpose = ?,
            signature = ?,
            updated_at = datetime('now')
        WHERE access_token = ?
    """, (
        guest_first_name, guest_last_name, nationality, birth_date,
        birth_place, document_type, document_number, cnp,
        address, travel_purpose, signature, token
    ))

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    if affected == 0:
        raise HTTPException(status_code=404, detail="Token not found")

    # 📤 Email küldés subprocess segítségével
    try:
        env = os.environ.copy()
        env["SMTP_PASSWORD"] = SMTP_PASSWORD
        result = subprocess.run(
            ["python3", SCRIPT_PATH, token],
            capture_output=True,
            text=True,
            env=env
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Sikertelen emailküldés: {result.stderr.strip()}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba emailküldés közben: {str(e)}")

    # 📄 PDF generálás a gazdának
    guest_data = {
        "Név": f"{guest_first_name} {guest_last_name}",
        "Nemzetiség": nationality,
        "Születési idő": birth_date,
        "Születési hely": birth_place,
        "Igazolvány típusa": document_type,
        "Igazolvány szám": document_number,
        "CNP": cnp,
        "Cím": address,
        "Utazás célja": travel_purpose
    }

    pdf_path = f"/config/private_docs/{token}_checkin.pdf"
    image_path = f"/config/private_docs/{token}_document.jpg"
    generate_guest_pdf(guest_data, pdf_path)
    
    # 📧 Email küldés a gazdának PDF-melléklettel
    try:
        msg = MIMEMultipart()
        msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg["To"] = OWNER_EMAIL
        msg["Subject"] = f"Vendég bejelentkezés: {guest_first_name} {guest_last_name}"
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()

        msg.attach(MIMEText(f"""Új vendég check-in érkezett.

    Név: {guest_first_name} {guest_last_name}
    Nemzetiség: {nationality}
    Születési idő: {birth_date}

    A csatolt PDF tartalmazza a teljes adatlapot.
    """, "plain"))

        # Csatoljuk a PDF-et
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "pdf")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{token}_checkin.pdf"')
            msg.attach(part)

        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, OWNER_EMAIL, msg.as_string())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF csatolásos email küldése sikertelen: {str(e)}")


    
    return {"status": "ok", "message": "Adatok frissítve, email elküldve."}
    
    
@app.post("/local/door/{token}/toggle")
async def toggle_door(token: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT guest_house_id FROM guest_bookings WHERE access_token = ?", (token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Token not found")

    house_id = str(row["guest_house_id"])

    try:
        with open(DOOR_MAP_PATH, "r") as f:
            door_map = yaml.safe_load(f)
        if house_id not in door_map:
            raise HTTPException(status_code=404, detail="Nincs ajtókonfiguráció ehhez a házhoz")

        config = door_map[house_id]
        domain = config.get("domain")
        action = config.get("action")
        entity_id = config.get("entity_id")

        if not domain or not action or not entity_id:
            raise HTTPException(status_code=500, detail="Hiányos ajtókonfiguráció")

        headers = {
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{HA_URL}/services/{domain}/{action}",
            headers=headers,
            json={"entity_id": entity_id}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Home Assistant válasz: {response.status_code} {response.text}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ajtóvezérlési hiba: {str(e)}")

    return {"status": "ok", "message": "Ajtó művelet elküldve"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8124)
