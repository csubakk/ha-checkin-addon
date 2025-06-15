FROM python:3.11-slim

# Telepíts rendszercsomagokat (ha kell pl. sqlite3 CLI)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc libsqlite3-dev sqlite3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Függőségek telepítése
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Forrás bemásolása
COPY . .

# Alapértelmezett parancs
CMD ["uvicorn", "checkin_api:app", "--host", "0.0.0.0", "--port", "8124"]
