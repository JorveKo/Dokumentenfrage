# Entwickler-Dokumentation

## 🔧 Entwicklungsumgebung

### Voraussetzungen
- Docker & Docker Compose
- Python 3.11+
- Git
- MongoDB Compass (optional)
- VS Code mit Python Extensions (empfohlen)

### Initiales Setup

1. **Repository klonen** 

bash
git clone https://github.com/username/dokumentenfrage.git
cd dokumentenfrage


2. **Virtuelle Umgebung erstellen**

bash
python -m venv venv
source venv/bin/activate # Linux/Mac
.\venv\Scripts\activate # Windows


3. **Dependencies installieren**

bash
pip install -r requirements.txt
pip install -r requirements-dev.txt # Entwickler-Tools


4. **Umgebungsvariablen**

bash
cp .env.example .env
.env anpassen mit eigenen Werten


5. **Docker starten**

bash
docker-compose up -d


6. **Dashboard aufrufen**

http://localhost:5000


### Wichtige Umgebungsvariablen     


env
MONGODB_URI=mongodb://mongodb:27017
DB_NAME=document_scraper
LOG_LEVEL=DEBUG
MAX_PARALLEL_DOWNLOADS=5
GOOGLE_API_KEY=your_api_key
GOOGLE_CSE_ID=your_cse_id



## 🏗 Architektur

### Core Module

1. **Scraper** (`app/core/scraper.py`)
   - Hauptlogik für Dokumenten-Scraping
   - Parallelisierte Downloads
   - Rate Limiting & Retry Logic
   - Fehlerbehandlung

2. **Processor** (`app/core/processor.py`)
   - Dokumentenverarbeitung
   - Metadaten-Extraktion
   - Text-Analyse
   - Format-Konvertierung

3. **Status Manager** (`app/core/status_manager.py`)
   - Echtzeit-Status-Tracking
   - WebSocket Updates
   - Health Monitoring
   - Performance Metrics

### API Struktur
- REST Endpoints für Scraping-Steuerung
- WebSocket für Live-Updates
- Health Check Endpoints
- Rate Limiting & Caching

### Datenbank-Schema

python
Document {
id: ObjectId,
title: str,
content: str,
metadata: {
source_url: str,
scrape_date: datetime,
file_type: str,
size: int,
...
},
status: str,
tags: List[str],
vector: List[float]
}


## 🧪 Testing

### Unit Tests ausführen
bash
Alle Tests
pytest
Spezifische Test-Datei
pytest tests/test_scraper.py
Mit Coverage
pytest --cov=app tests/


### Test-Struktur

tests/
├── unit/ # Unit Tests
├── integration/ # Integrationstests
├── e2e/ # End-to-End Tests
└── fixtures/ # Test-Daten



## 📝 Coding Guidelines

### Python Style
- PEP 8 Konventionen
- Type Hints verwenden
- Docstrings (Google Style)
- Max Line Length: 88 Zeichen

### Beispiel

python
def process_document(
document: Document,
options: Dict[str, Any]
) -> ProcessingResult:
"""Verarbeitet ein Dokument mit gegebenen Optionen.
Args:
document: Das zu verarbeitende Dokument
options: Verarbeitungsoptionen
Returns:
ProcessingResult mit Verarbeitungsergebnis
Raises:
ProcessingError: Bei Verarbeitungsfehlern
"""
pass


## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

yaml
name: CI/CD
on: [push, pull_request]
jobs:
test:
runs-on: ubuntu-latest
steps:
uses: actions/checkout@v2
name: Run Tests
run: docker-compose run web pytest
deploy:
needs: test
if: github.ref == 'refs/heads/main'
runs-on: ubuntu-latest
steps:
name: Deploy
run: ./deploy.sh


## 🐛 Debugging

### Logs checken

bash
Web Service Logs
docker-compose logs -f web
MongoDB Logs
docker-compose logs -f mongodb
Alle Logs
docker-compose logs -f


### Common Issues

1. **MongoDB Connection**
   - Connection String prüfen
   - Network Settings checken
   - MongoDB Status verifizieren

2. **File Permissions**
   - Download Directory Rechte
   - Log Directory Rechte
   - Docker Volume Permissions

3. **Memory Issues**
   - Docker Resources checken
   - MongoDB Memory Usage
   - Python Memory Profiling

## 📦 Deployment

### Staging Deployment

bash
docker-compose -f docker-compose.staging.yml up -d


### Production Deployment
bash
docker-compose -f docker-compose.prod.yml up -d


### Monitoring
- Grafana Dashboard
- MongoDB Compass
- Log Aggregation
- Error Tracking

## 🔄 Updates & Maintenance

### Database Backups

bash
Backup erstellen
docker-compose exec mongodb mongodump
Backup wiederherstellen
docker-compose exec mongodb mongorestore


### System Updates

bash
Latest Code
git pull
Rebuild Container
docker-compose build --no-cache
Update starten
docker-compose up -d


## 📚 Weitere Ressourcen

- [API Dokumentation](docs/API.md)
- [Architektur Guide](docs/ARCHITECTURE.md)
- [Monitoring Guide](docs/MONITORING.md)
- [Security Guide](docs/SECURITY.md)