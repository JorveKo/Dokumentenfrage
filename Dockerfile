# Basis-Image: Verwende eine schlanke Python-Version
# Python 3.11 bietet gute Performance und aktuelle Features
FROM python:3.11-slim

# System-Dependencies installieren
# build-essential: Für Kompilierung einiger Python-Pakete
# curl: Für Healthchecks und Downloads
# python3-dev: Für Python-Header-Dateien
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis im Container erstellen
WORKDIR /app

# Anforderungen aus requirements.txt installieren
# --no-cache-dir reduziert die Image-Größe
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projektdateien kopieren
COPY . .

# Verzeichnisse für Downloads und Logs erstellen
# Diese werden als Volume-Mounts verwendet
RUN mkdir -p /app/downloads /app/logs /app/static/images

# Berechtigungen für die Skripte setzen
RUN chmod +x docker/scripts/start.sh docker/scripts/init-mongo.sh

# Port freigeben
EXPOSE 5000

# Startkommando für den Container
# Verwendet das start.sh Script für die Initialisierung
CMD ["./docker/scripts/start.sh"]