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
    # később bővíthető pl. "ro": { ... }
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
