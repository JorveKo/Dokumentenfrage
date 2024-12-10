# app/database.py
import logging
from typing import Optional, Dict, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, TEXT
# app/database.py
from pymongo.errors import DuplicateKeyError
from pymongo.errors import ServerSelectionTimeoutError as ConnectionError  # Geändert


from app.config import MONGODB_URI, DB_NAME
from app.models.schemas import DocumentMetadata, ScrapingStats

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Verwaltet alle Datenbankoperationen"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.connected = False
        self.in_memory_storage = []  # Fallback für fehlende DB-Verbindung
        
    async def connect(self) -> bool:
        """Stellt Verbindung zur Datenbank her"""
        try:
            logger.info(f"Versuche Verbindung mit URI: {MONGODB_URI}")
            self.client = AsyncIOMotorClient(MONGODB_URI)
            await self.client.server_info()  # Test connection
            self.db = self.client[DB_NAME]
            self.connected = True
            
            # Erstelle Indizes
            await self.create_indices()
            
            logger.info("MongoDB Verbindung erfolgreich hergestellt")
            return True
            
        except ConnectionError as e:
            logger.error(f"MongoDB Verbindungsfehler: {str(e)}")
            logger.error(f"Verwendete URI: {MONGODB_URI}")
            self.connected = False
            return False
            
    async def create_indices(self):
        """Erstellt notwendige Datenbankindizes"""
        try:
            await self.db.documents.create_index([("url", ASCENDING)], unique=True)
            await self.db.documents.create_index([("term", ASCENDING)])
            await self.db.documents.create_index([("file_type", ASCENDING)])
            await self.db.documents.create_index([("hash", ASCENDING)])
            await self.db.documents.create_index([("timestamp", ASCENDING)])
            await self.db.documents.create_index([
                ("snippet", TEXT),
                ("title", TEXT)
            ])
            
            logger.info("Datenbankindizes erfolgreich erstellt")
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Indizes: {str(e)}")
            
    async def store_document(self, document: DocumentMetadata) -> bool:
        """Speichert ein Dokument in der Datenbank"""
        try:
            if self.connected:
                result = await self.db.documents.insert_one(document.dict())
                logger.info(f"Dokument gespeichert mit ID: {result.inserted_id}")
                return True
            else:
                self.in_memory_storage.append(document.dict())
                logger.info("Dokument im temporären Speicher abgelegt")
                return True
                
        except DuplicateKeyError:
            logger.warning(f"Dokument existiert bereits: {document.url}")
            return False
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Dokuments: {str(e)}")
            return False
            
    async def get_document_by_url(self, url: str) -> Optional[Dict]:
        """Sucht ein Dokument anhand der URL"""
        try:
            if self.connected:
                return await self.db.documents.find_one({"url": url})
            else:
                return next((doc for doc in self.in_memory_storage 
                           if doc["url"] == url), None)
                
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Dokuments: {str(e)}")
            return None
            
    async def get_document_by_hash(self, hash_value: str) -> Optional[Dict]:
        """Sucht ein Dokument anhand des Hashes"""
        try:
            if self.connected:
                return await self.db.documents.find_one({"hash": hash_value})
            else:
                return next((doc for doc in self.in_memory_storage 
                           if doc["hash"] == hash_value), None)
                
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Dokuments: {str(e)}")
            return None
            
    async def get_similar_documents(self, term: str, hash_value: str) -> List[Dict]:
        """Findet ähnliche Dokumente basierend auf Term und Hash"""
        try:
            if self.connected:
                cursor = self.db.documents.find({
                    "term": term,
                    "hash": {"$ne": hash_value}
                })
                return await cursor.to_list(length=None)
            else:
                return [doc for doc in self.in_memory_storage 
                        if doc["term"] == term and doc["hash"] != hash_value]
                
        except Exception as e:
            logger.error(f"Fehler beim Abrufen ähnlicher Dokumente: {str(e)}")
            return []
            
    async def get_statistics(self) -> ScrapingStats:
        """Erstellt Statistiken über die gespeicherten Dokumente"""
        try:
            if self.connected:
                pipeline = [
                    {
                        "$facet": {
                            "by_type": [
                                {"$group": {
                                    "_id": "$file_type",
                                    "count": {"$sum": 1},
                                    "total_size": {"$sum": "$size"}
                                }}
                            ],
                            "by_term": [
                                {"$group": {
                                    "_id": "$term",
                                    "count": {"$sum": 1}
                                }}
                            ],
                            "by_language": [
                                {"$group": {
                                    "_id": "$language",
                                    "count": {"$sum": 1}
                                }}
                            ],
                            "overall": [
                                {"$group": {
                                    "_id": None,
                                    "total_docs": {"$sum": 1},
                                    "total_size": {"$sum": "$size"},
                                    "unique_domains": {"$addToSet": "$domain"}
                                }}
                            ]
                        }
                    }
                ]
                
                result = await self.db.documents.aggregate(pipeline).to_list(length=1)
                
                if not result:
                    return ScrapingStats()
                    
                stats = result[0]
                return ScrapingStats(
                    total_documents=stats["overall"][0]["total_docs"] if stats["overall"] else 0,
                    documents_per_type={
                        doc["_id"]: doc["count"] for doc in stats["by_type"]
                    },
                    documents_per_term={
                        doc["_id"]: doc["count"] for doc in stats["by_term"]
                    },
                    total_size=stats["overall"][0]["total_size"] if stats["overall"] else 0,
                    unique_domains=len(stats["overall"][0]["unique_domains"] if stats["overall"] else []),
                    language_distribution={
                        doc["_id"]: doc["count"] for doc in stats["by_language"]
                    }
                )
            else:
                return self._calculate_in_memory_stats()
                
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Statistiken: {str(e)}")
            return ScrapingStats()
            
    def _calculate_in_memory_stats(self) -> ScrapingStats:
        """Berechnet Statistiken für In-Memory Storage"""
        if not self.in_memory_storage:
            return ScrapingStats()
            
        stats = ScrapingStats(
            total_documents=len(self.in_memory_storage),
            total_size=sum(doc.get("size", 0) for doc in self.in_memory_storage)
        )
        
        # Berechne Dokumentverteilungen
        type_counts = {}
        term_counts = {}
        lang_counts = {}
        domains = set()
        
        for doc in self.in_memory_storage:
            # Dateitypen
            file_type = doc.get("file_type", "unknown")
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
            
            # Terme
            term = doc.get("term", "unknown")
            term_counts[term] = term_counts.get(term, 0) + 1
            
            # Sprachen
            lang = doc.get("language", "unknown")
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
            
            # Domains
            if "url" in doc:
                from urllib.parse import urlparse
                domain = urlparse(doc["url"]).netloc
                domains.add(domain)
        
        stats.documents_per_type = type_counts
        stats.documents_per_term = term_counts
        stats.language_distribution = lang_counts
        stats.unique_domains = len(domains)
        
        return stats
        
    async def cleanup_old_documents(self, days: int = 30) -> int:
        """Löscht Dokumente, die älter als X Tage sind"""
        try:
            if not self.connected:
                return 0
                
            cutoff_date = datetime.now() - timedelta(days=days)
            result = await self.db.documents.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Fehler beim Bereinigen alter Dokumente: {str(e)}")
            return 0

    async def get_recent_documents(self, limit: int = 10) -> List[Dict]:
        """Holt die neuesten Dokumente, sortiert nach Zeitstempel"""
        try:
            documents = await self.db.documents.find() \
                .sort("timestamp", -1) \
                .limit(limit) \
                .to_list(length=limit)
            
            return [{
                "title": doc.get("title", "Untitled"),
                "file_type": doc.get("file_type", "unknown"),
                "size": doc.get("size", 0),
                "timestamp": doc.get("timestamp"),
                "term": doc.get("term", ""),
                "success": doc.get("success", False)
            } for doc in documents]
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Dokumente: {str(e)}")
            return []

    async def get_document_count(self) -> int:
        """Gibt die Gesamtanzahl der Dokumente zurück"""
        try:
            return await self.db.documents.count_documents({})
        except Exception as e:
            logger.error(f"Fehler beim Zählen der Dokumente: {str(e)}")
            return 0

# Globale Datenbankinstanz
db_manager = DatabaseManager()