FROM python:3.11-slim

WORKDIR /app

# Telepítendő csomagok
RUN pip install --no-cache-dir fastapi uvicorn python-multipart

# Saját fájlok
COPY . .

# Indítási parancs
CMD ["uvicorn", "checkin_api:app", "--host", "0.0.0.0", "--port", "8124"]
