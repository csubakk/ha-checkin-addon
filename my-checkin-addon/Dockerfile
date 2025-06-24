FROM python:3.11-slim

# 🧱 Rendszercsomagok telepítése
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libsqlite3-dev \
        sqlite3 \
        libfreetype6-dev \
        libjpeg-dev \
        zlib1g-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 📁 Munkakönyvtár beállítása
WORKDIR /app

# 📦 Python-függőségek telepítése
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 🔤 Betűtípus bemásolása
COPY fonts/DejaVuSans.ttf /app/fonts/DejaVuSans.ttf
COPY log_config.yaml /app/log_config.yaml

# 📁 Sablonok bemásolása a HA alatt elérhető /config alá
COPY templates /app/templates

# 🧠 Forráskód bemásolása (végül)
COPY . .

# 🚀 Konténer indulás
CMD ["uvicorn", "checkin_api:app", "--host", "0.0.0.0", "--port", "8124", "--log-config", "/app/log_config.yaml"]
