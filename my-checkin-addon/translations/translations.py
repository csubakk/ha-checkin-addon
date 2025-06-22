# translations/translations.py

import os

HOST_LANGUAGE = os.getenv("HOST_LANGUAGE", "hu")

TRANSLATIONS = {
    "hu": {
        "title": "Foglalási naptár",
        "back": "⬅️ Vissza",
        "forward": "Előre ➡️",
        "date": "Dátum",
        "day": "Nap",
        "room": "{}. szoba",
        "weekday_names": ['H', 'K', 'Sze', 'Cs', 'P', 'Szo', 'V'],
        "month_names": ['', 'jan.', 'feb.', 'márc.', 'ápr.', 'máj.', 'jún.',
                        'júl.', 'aug.', 'szep.', 'okt.', 'nov.', 'dec.'],
    },
    "ro": {
        "title": "Calendar rezervări",
        "back": "⬅️ Înapoi",
        "forward": "Înainte ➡️",
        "date": "Dată",
        "day": "Zi",
        "room": "Camera {}",
        "weekday_names": ['L', 'Ma', 'Mi', 'J', 'V', 'S', 'D'],
        "month_names": ['', 'ian.', 'feb.', 'mart.', 'apr.', 'mai', 'iun.',
                        'iul.', 'aug.', 'sept.', 'oct.', 'nov.', 'dec.'],
    },
}


def tr(key, *args):
    lang = HOST_LANGUAGE if HOST_LANGUAGE in TRANSLATIONS else "hu"
    text = TRANSLATIONS[lang].get(key, key)
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
