import os
import requests
from googleapiclient.discovery import build


class DocumentScraper:
    """Hauptklasse für das Scraping von Dokumenten"""

    def __init__(self, api_key: str, cse_id: str):
        self.api_key = api_key
        self.cse_id = cse_id
        self.search_service = build("customsearch", "v1", developerKey=self.api_key)

    def search_documents(self, term: str, file_type: str, max_results: int):
        """Sucht Dokumente mit der Google Custom Search API"""
        try:
            results = []
            file_type_query = f"filetype:{file_type}"

            for start_index in range(1, min(max_results, 100), 10):
                response = (
                    self.search_service.cse()
                    .list(
                        q=f"{term} {file_type_query}",
                        cx=self.cse_id,
                        start=start_index,
                        num=min(10, max_results - start_index),
                    )
                    .execute()
                )
                results.extend(response.get("items", []))
            return results

        except Exception as e:
            print(f"Fehler beim Suchen von Dokumenten: {e}")
            return []

    def download_document(self, url: str, download_folder: str = "downloads"):
        """Lädt ein Dokument herunter und speichert es im Download-Ordner"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            filename = url.split("/")[-1]
            file_path = os.path.join(download_folder, filename)

            with open(file_path, "wb") as file:
                file.write(response.content)

            return {"status": "success", "file_path": file_path}

        except Exception as e:
            print(f"Fehler beim Herunterladen des Dokuments: {e}")
            return {"status": "error", "message": str(e)}
