#!/bin/bash

# MongoDBDB Initialisierungs-Script

# Erstellt die notwendige Datenbank und Indizes für den Document Scraper



echo "Initializing MongoDB..."



# Verbinde mit MongoDB und führe Initialisierungsbefehle aus

mongosh <<EOF

# Wähle oder erstelle die Datenbank

use document_scraper



# Erstelle die documents Collection

db.createCollection("documents")



# Erstelle notwendige Indizes

# URL-Index für eindeutige Dokumente

db.documents.createIndex({ "url": 1 }, { unique: true })



# Term-Index für Suchoperationen

db.documents.createIndex({ "term": 1 })



# Dateityp-Index für Filterung

db.documents.createIndex({ "file_type": 1 })

EOF

