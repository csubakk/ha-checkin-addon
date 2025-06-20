from fastapi import APIRouter
from services import notifications

router = APIRouter()

@router.post("/send-checkin-links")
def send_checkin_links():
    count = notifications.send_checkin_links_for_all()
    return {"sent": count}

@router.post("/send-checkin-reminders")
def send_checkin_reminders():
    count = notifications.send_checkin_reminders_for_today()
    return {"sent": count}
