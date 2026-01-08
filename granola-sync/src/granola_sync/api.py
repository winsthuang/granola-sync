"""Granola API client."""
import json
from pathlib import Path
from typing import Optional, List, Dict
import requests


class GranolaClient:
    """Client for interacting with Granola's API."""

    BASE_URL = "https://api.granola.ai"
    CREDENTIALS_PATH = Path.home() / "Library/Application Support/Granola/supabase.json"

    def __init__(self):
        self.token: Optional[str] = None
        self._load_credentials()

    def _load_credentials(self):
        """Load access token from Granola's local storage."""
        if not self.CREDENTIALS_PATH.exists():
            raise FileNotFoundError(
                f"Granola credentials not found at {self.CREDENTIALS_PATH}\n"
                "Make sure Granola is installed and you're logged in."
            )

        with open(self.CREDENTIALS_PATH) as f:
            data = json.load(f)

        tokens = json.loads(data['workos_tokens'])
        self.token = tokens['access_token']

    def _headers(self) -> dict:
        """Build request headers."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "Granola/5.354.0"
        }

    def get_documents(self, limit: int = 500) -> List[Dict]:
        """Fetch all documents from Granola."""
        url = f"{self.BASE_URL}/v2/get-documents"
        all_docs = []
        offset = 0

        while True:
            payload = {
                "limit": limit,
                "offset": offset,
                "include_last_viewed_panel": True
            }

            resp = requests.post(url, headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()

            docs = data.get('docs', []) if isinstance(data, dict) else data

            if not docs:
                break

            all_docs.extend(docs)

            if len(docs) < limit:
                break

            offset += limit

        return all_docs

    def get_transcript(self, document_id: str) -> Optional[List[Dict]]:
        """Fetch transcript for a specific document."""
        url = f"{self.BASE_URL}/v1/get-document-transcript"
        payload = {"document_id": document_id}

        try:
            resp = requests.post(url, headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else data.get('utterances', [])
        except Exception:
            return None

    def get_user_info(self) -> dict:
        """Get current user info from credentials."""
        with open(self.CREDENTIALS_PATH) as f:
            data = json.load(f)
        return json.loads(data.get('user_info', '{}'))
