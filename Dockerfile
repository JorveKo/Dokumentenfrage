# Basis-Image: Verwende eine schlanke Python-Version
FROM python:3.11-slim

# System-Dependencies installieren
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis im Container erstellen
WORKDIR /app

# Anforderungen aus requirements.txt installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projektdateien kopieren
COPY . .

# Verzeichnisse für Downloads und Logs erstellen
RUN mkdir -p /app/downloads /app/logs

# Port freigeben
EXPOSE 5000

# Startkommando für den Container
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
