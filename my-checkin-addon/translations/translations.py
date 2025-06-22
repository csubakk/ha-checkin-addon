def get_translations(lang: str):
    if lang == "hu":
        return {
            "calendar_title": "Foglalási naptár",
            "back": "⬅️ Vissza",
            "forward": "Előre ➡️",
            "date": "Dátum",
            "day": "Nap",
            "room": "{}. szoba",
            "edit_link": "·",
            "weekday_labels": ['H', 'K', 'Sze', 'Cs', 'P', 'Szo', 'V'],
            "month_labels": ['', 'jan.', 'feb.', 'márc.', 'ápr.', 'máj.', 'jún.',
                             'júl.', 'aug.', 'szep.', 'okt.', 'nov.', 'dec.'],
        }
    return {}  # más nyelvekhez később
