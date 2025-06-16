FROM python:3.11-slim

# Rendszercsomagok telepítése (pl. sqlite3 CLI és fejlécek + libfreetype és libjpeg reportlab-hoz)
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

# Python függőségek telepítése
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Forrásfájlok bemásolása
COPY . .

# Alapértelmezett parancs a konténer futtatásához
CMD ["uvicorn", "checkin_api:app", "--host", "0.0.0.0", "--port", "8124"]
