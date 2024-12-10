#!/bin/bash



# Start-Script für den Document Scraper

# Wartet auf MongoDB und initialisiert die Datenbank, bevor die Anwendung gestartet wird



echo "Starting Neural Document Acquisition System..."



# Warte auf MongoDB

# Dies ist wichtig, da MongoDB etwas Zeit braucht, um vollständig zu starten

echo "Waiting for MongoDB..."

sleep 5



# Initialisiere die Datenbank

# Erstellt Collections und Indizes

./docker/scripts/init-mongo.sh



# Starte die Anwendung mit uvicorn

# --host 0.0.0.0: Erlaubt externe Verbindungen

# --port 5000: Standard-Port für die Anwendung

# --reload: Automatisches Neuladen bei Code-Änderungen

# --reload-exclude: Verhindert Neuladen bei Änderungen in Logs und Downloads

uvicorn app:app --host 0.0.0.0 --port 5000 --reload --reload-exclude="logs/*" --reload-exclude="downloads/*"