EMAIL_TEMPLATES = {
    "hu": {
        "confirmation_subject": "Foglalás visszaigazolása",
        "confirmation_body": """Kedves {name}!

Köszönjük, hogy szálláshelyünket választotta. Az Ön foglalása sikeresen rögzítésre került az alábbi adatokkal:

• 🗓️ Érkezés: {arrival}  
• 🏠 Ház/Szoba: {house}  
• 🚪 Távozás: {departure}  

Kérjük, hogy az utazás előtt figyelje e-mailjeit, hamarosan küldjük a további részleteket és az online check-in linket is.

Amennyiben kérdése van, forduljon hozzánk bizalommal.

Üdvözlettel:  
{signature}  
Telefon: {phone}  
Email: {email}""",

        "checkin_subject": "Online Check-in link",
        "checkin_body": """Kedves {name},

Emlékeztetőül küldjük a holnapi érkezés részleteit:
• Érkezés: {arrival}  
• Ház/Szoba: {house}  

Kérjük, töltse ki az online check-in űrlapot az alábbi linken:

{link}

Köszönjük, és kellemes utazást kívánunk!

Üdvözlettel,  
{signature}  
Telefon: {phone}  
Email: {email}""",

        "reminder_subject": "Emlékeztető – Online Check-in",
        "reminder_body": """Kedves {name},

Ez egy emlékeztető, hogy Ön ma érkezik hozzánk ({arrival}).  
Kérjük, ha még nem tette meg, töltse ki az online check-in űrlapot az alábbi linken:

{link}

Ez segít gyorsítani a bejelentkezést és egyszerűsíti az adminisztrációt.

Köszönjük, és jó utat kívánunk!

Üdvözlettel,  
{signature}  
Telefon: {phone}  
Email: {email}""",

        "access_subject": "Ajtónyitási link",
        "access_body": """Kedves {name},

Az Ön szobája készen áll, az alábbi linken keresztül tudja kinyitni az ajtót:

🔓 {link}

A link csak az Ön tartózkodása alatt működik.

Bármilyen kérdés esetén forduljon hozzánk bizalommal.

Üdvözlettel,  
{signature}  
Telefon: {phone}  
Email: {email}"""
    },

    "en": {
        "confirmation_subject": "Booking Confirmation",
        "confirmation_body": """Dear {name},

Thank you for choosing our accommodation. Your reservation has been successfully recorded with the following details:

• 🗓️ Arrival: {arrival}  
• 🏠 House/Room: {house}  
• 🚪 Departure: {departure}  

We will soon send further details and your online check-in link.

If you have any questions, feel free to contact us.

Best regards,  
{signature}  
Phone: {phone}  
Email: {email}""",

        "checkin_subject": "Online Check-in Link",
        "checkin_body": """Dear {name},

This is a reminder of your upcoming arrival:
• Arrival: {arrival}  
• House/Room: {house}  

Please complete your online check-in using the following link:

{link}

Thank you and we wish you a pleasant journey!

Best regards,  
{signature}  
Phone: {phone}  
Email: {email}""",

        "reminder_subject": "Reminder – Online Check-in",
        "reminder_body": """Dear {name},

This is a reminder that you are arriving today ({arrival}).  
If you haven't already, please complete your online check-in at the following link:

{link}

This helps us speed up the registration process and simplify administration.

Thank you and have a safe trip!

Best regards,  
{signature}  
Phone: {phone}  
Email: {email}""",

        "access_subject": "Door Access Link",
        "access_body": """Dear {name},

Your room is now ready. You can open the door using the following link:

🔓 {link}

The link is valid only during your stay.

If you have any questions, feel free to contact us.

Best regards,  
{signature}  
Phone: {phone}  
Email: {email}"""
    },

    "ro": {
        "confirmation_subject": "Confirmarea rezervării",
        "confirmation_body": """Stimate/ă {name},

Vă mulțumim că ați ales unitatea noastră de cazare. Rezervarea dvs. a fost înregistrată cu succes cu următoarele detalii:

• 🗓️ Sosire: {arrival}  
• 🏠 Casă/Cameră: {house}  
• 🚪 Plecare: {departure}  

În curând veți primi mai multe informații și link-ul pentru check-in online.

Pentru orice întrebări, nu ezitați să ne contactați.

Cu stimă,  
{signature}  
Telefon: {phone}  
Email: {email}""",

        "checkin_subject": "Link Check-in Online",
        "checkin_body": """Stimate/ă {name},

Vă reamintim că urmează sosirea dvs.:
• Sosire: {arrival}  
• Casă/Cameră: {house}  

Vă rugăm să completați formularul de check-in online folosind linkul de mai jos:

{link}

Vă mulțumim și vă dorim o călătorie plăcută!

Cu stimă,  
{signature}  
Telefon: {phone}  
Email: {email}""",

        "reminder_subject": "Reminder – Check-in Online",
        "reminder_body": """Stimate/ă {name},

Acesta este un memento că astăzi este ziua sosirii dvs. ({arrival}).  
Dacă nu ați completat deja check-in-ul online, o puteți face folosind următorul link:

{link}

Acest lucru ne ajută să accelerăm procesul de înregistrare și să simplificăm administrația.

Vă mulțumim și vă dorim drum bun!

Cu stimă,  
{signature}  
Telefon: {phone}  
Email: {email}""",

        "access_subject": "Link pentru accesul în cameră",
        "access_body": """Stimate/ă {name},

Camera dvs. este pregătită. Puteți deschide ușa folosind următorul link:

🔓 {link}

Link-ul este valabil doar pe durata sejurului dvs.

Pentru întrebări, nu ezitați să ne contactați.

Cu stimă,  
{signature}  
Telefon: {phone}  
Email: {email}"""
    }
}
