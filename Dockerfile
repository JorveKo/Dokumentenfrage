FROM python:3.11-slim

# System-Dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python Requirements in zwei Schritten installieren
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    scikit-learn \
    websockets \
    python-socketio \
    fastapi \
    uvicorn[standard] \
    jinja2 \
    python-multipart \
    langdetect \
    google-api-python-client \
    motor \
    pydantic \
    aiohttp \
    websocket-client

# Dann den Rest der Requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projektdateien kopieren
COPY . .

# Verzeichnisse erstellen
RUN mkdir -p downloads logs

# Berechtigungen setzen
RUN chmod +x docker/scripts/start.sh

# Port freigeben
EXPOSE 5000

# Start-Command
CMD ["./docker/scripts/start.sh"]