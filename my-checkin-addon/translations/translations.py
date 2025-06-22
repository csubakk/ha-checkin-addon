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
        "create": "Létrehozás"
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
        "create": "Salvare"
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
