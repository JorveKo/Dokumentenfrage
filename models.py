# models.py
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, HttpUrl, validator
from enum import Enum

class FileType(str, Enum):
    """Unterstützte Dateitypen"""
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"

class DocumentMetadata(BaseModel):
    """Metadaten für ein Dokument"""
    url: HttpUrl
    title: str
    snippet: Optional[str] = None
    file_type: FileType
    content_type: str
    size: int
    timestamp: datetime = Field(default_factory=datetime.now)
    keywords: List[str] = Field(default_factory=list)
    language: Optional[str] = None
    hash: str
    term: str
    download_time: float = 0.0
    local_path: str
    
    class Config:
        arbitrary_types_allowed = True

class ScrapingStatus(BaseModel):
    """Status des Scraping-Prozesses"""
    is_running: bool = False
    current_term: str = ""
    progress: float = 0
    total_documents: int = 0
    completed_terms: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    api_costs: float = 0
    downloaded_files: int = 0
    successful_downloads: int = 0
    failed_downloads: int = 0
    total_bytes: int = 0
    processing_speed: float = 0
    
    @property
    def success_rate(self) -> float:
        """Berechnet die Erfolgsrate der Downloads"""
        total = self.successful_downloads + self.failed_downloads
        if total == 0:
            return 0.0
        return (self.successful_downloads / total) * 100

class ScrapingStats(BaseModel):
    """Statistiken des Scraping-Prozesses"""
    total_documents: int = 0
    documents_per_type: Dict[str, int] = Field(default_factory=dict)
    documents_per_term: Dict[str, int] = Field(default_factory=dict)
    total_size: int = 0
    average_file_size: float = 0
    success_rate: float = 0
    processing_speed: float = 0
    unique_domains: int = 0
    language_distribution: Dict[str, int] = Field(default_factory=dict)
    
    def update_averages(self):
        """Aktualisiert die Durchschnittswerte"""
        if self.total_documents > 0:
            self.average_file_size = self.total_size / self.total_documents

class ScrapingRequest(BaseModel):
    """Eingabeparameter für den Scraping-Prozess"""
    term: str = Field(..., min_length=2)
    file_type: FileType
    max_results: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.85, ge=0, le=1.0)
    include_related_terms: bool = True
    prioritize_recent: bool = True
    language_filter: Optional[str] = None

class PerformanceMetrics(BaseModel):
    """Performance-Metriken des Systems"""
    cpu_usage: float = 0
    memory_usage: float = 0
    network_speed: float = 0
    response_times: List[float] = Field(default_factory=list)
    error_rate: float = 0
    queue_size: int = 0
    
    @validator('cpu_usage', 'memory_usage')
    def validate_percentage(cls, v):
        """Validiert Prozentangaben"""
        if not 0 <= v <= 100:
            raise ValueError('Prozentwert muss zwischen 0 und 100 liegen')
        return v

class DownloadResult(BaseModel):
    """Ergebnis eines Download-Vorgangs"""
    url: HttpUrl
    success: bool
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    download_time: float = 0.0
    size: Optional[int] = None
    content_type: Optional[str] = None

class ProcessingResult(BaseModel):
    """Ergebnis der Dokumentverarbeitung"""
    document_id: str
    success: bool
    metadata: Optional[DocumentMetadata] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    is_duplicate: bool = False
    similarity_score: Optional[float] = None

class WebSocketMessage(BaseModel):
    """Nachrichtenformat für WebSocket-Kommunikation"""
    type: str
    data: Dict
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        schema_extra = {
            "example": {
                "type": "status_update",
                "data": {
                    "progress": 45.5,
                    "current_term": "vertrag",
                    "status": "processing"
                }
            }
        }