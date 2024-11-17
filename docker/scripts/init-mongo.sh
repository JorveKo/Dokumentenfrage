#!/bin/bash
echo "Initializing MongoDB..."
# Erstellt Datenbank und Indizes
mongosh <<EOF
use document_scraper
db.createCollection("documents")
db.documents.createIndex({ "url": 1 }, { unique: true })
db.documents.createIndex({ "term": 1 })
db.documents.createIndex({ "file_type": 1 })
EOF