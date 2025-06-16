FROM python:3.11-slim

# Rendszercsomagok telepítése
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libsqlite3-dev \
        sqlite3 \
        libfreetype6-dev \
        libjpeg-dev \
        zlib1g-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Munkakönyvtár beállítása
WORKDIR /app

# Python függőségek
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ⬇️ Fontfájl bemásolása
COPY fonts/DejaVuSans.ttf /config/DejaVuSans.ttf

# Forráskód bemásolása
COPY . .

# Konténer indulás
CMD ["uvicorn", "checkin_api:app", "--host", "0.0.0.0", "--port", "8124"]
