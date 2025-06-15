FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn python-multipart paho-mqtt

COPY . .

CMD ["uvicorn", "checkin_api:app", "--host", "0.0.0.0", "--port", "8124"]
