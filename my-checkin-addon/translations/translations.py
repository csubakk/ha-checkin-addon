# translations/translations.py

import os

HOST_LANGUAGE = os.getenv("HOST_LANGUAGE", "hu")

TRANSLATIONS = {
    "hu": {
        "title": "Foglalási naptár",
        "back": "Vissza",
        "forward": "Előre",
        "date": "Dátum",
        "day": "Nap",
        "room": "{}. szoba",
        "weekday_names": ['H', 'K', 'Sze', 'Cs', 'P', 'Szo', 'V'],
        "month_names": ['', 'jan.', 'feb.', 'márc.', 'ápr.', 'máj.', 'jún.',
                        'júl.', 'aug.', 'szep.', 'okt.', 'nov.', 'dec.'],
        "last_name": "Vezetéknév",
        "first_name": "Keresztnév",
        "email": "Email",
        "phone": "Telefon",
        "room": "Szoba",
        "arrival": "Érkezés",
        "departure": "Távozás",
        "guest_count": "Vendégek száma",
        "notes": "Megjegyzés",
        "created_by": "Rögzítő",
        "delete": "Törlés",
        "edit_booking": "Foglalás szerkesztése",
        "new_booking": "Új foglalás",
        "save": "Mentés",
        "create": "Létrehozás",
        "invalid_email": "Hibás vagy hiányzó email cím!",
        "invalid_phone": "Hibás telefonszám! Kérjük, adjon meg legalább 9 számjegyet, +, 00 vagy 07 előtaggal.",
        "empty_name": "A vendég neve nem lehet üres.",
        "invalid_dates": "Távozás nem lehet az érkezés előtt vagy azonos nap.",
        "date_format_error": "Dátum formátuma hibás.",
        "conflict": "Ütközés: már van foglalás ezeken a napokon: {}"
        "delete_title": "Foglalás törlése",
        "delete_warning": "Biztosan törlöd ezt a foglalást?",
        "guest": "Vendég",
        "checkin": "Érkezés",
        "checkout": "Távozás",
        "confirm_delete": "Igen, törlöm",
        "cancel": "Mégse"
    },
    "ro": {
        "title": "Calendar rezervări",
        "back": "Înapoi",
        "forward": "Înainte",
        "date": "Dată",
        "day": "Zi",
        "room": "Camera {}",
        "weekday_names": ['L', 'Ma', 'Mi', 'J', 'V', 'S', 'D'],
        "month_names": ['', 'ian.', 'feb.', 'mart.', 'apr.', 'mai', 'iun.',
                        'iul.', 'aug.', 'sept.', 'oct.', 'noi.', 'dec.'],
        "last_name": "Nume de familie",
        "first_name": "Prenume",
        "email": "Email",
        "phone": "Telefon",
        "room": "Cameră",
        "arrival": "Sosire",
        "departure": "Plecare",
        "guest_count": "Număr de oaspeți",
        "notes": "Observații",
        "created_by": "Înregistrat de",
        "delete": "Ștergere",
        "edit_booking": "Modificare rezervare",
        "new_booking": "Rezervare nouă",
        "save": "Salvare",
        "create": "Salvare",
        "invalid_email": "Adresă de email lipsă sau incorectă!",
        "invalid_phone": "Număr de telefon invalid! Vă rugăm să introduceți cel puțin 9 cifre, cu prefix +, 00 sau 07.",
        "empty_name": "Numele oaspetelui nu poate fi gol.",
        "invalid_dates": "Plecarea nu poate fi înainte sau în aceeași zi cu sosirea.",
        "date_format_error": "Formatul datei este incorect.",
        "conflict": "Conflict: există deja rezervări în aceste zile: {}"
        "delete_title": "Ștergere rezervare",
        "delete_warning": "Sigur vrei să ștergi?",
        "guest": "Oaspete",
        "checkin": "Sosire",
        "checkout": "Plecare",
        "confirm_delete": "Da, șterg",
        "cancel": "Cancel"
    },
}

def get_translations(lang=None):
    lang = lang or os.getenv("HOST_LANGUAGE", "hu")
    return TRANSLATIONS.get(lang, TRANSLATIONS["hu"])

def tr(key, *args, lang=None):
    translations = get_translations(lang)
    text = translations.get(key, key)
    if args:
        try:
            return text.format(*args)
        except Exception:
            return text
    return text


def get_weekday_names():
    lang = HOST_LANGUAGE if HOST_LANGUAGE in TRANSLATIONS else "hu"
    return TRANSLATIONS[lang]["weekday_names"]


def get_month_names():
    lang = HOST_LANGUAGE if HOST_LANGUAGE in TRANSLATIONS else "hu"
    return TRANSLATIONS[lang]["month_names"]
