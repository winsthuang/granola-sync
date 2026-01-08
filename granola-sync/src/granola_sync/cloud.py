"""Cloud API client for granola-sync."""
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime

from .config import get_api_url, get_api_key


class CloudAPIError(Exception):
    """Error from the cloud API."""
    pass


class CloudClient:
    """Client for interacting with the Granola cloud API."""

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or get_api_url()
        self.api_key = api_key or get_api_key()

        if not self.api_url:
            raise CloudAPIError("API URL not configured. Run 'granola-sync login' first.")
        if not self.api_key:
            raise CloudAPIError("API key not configured. Run 'granola-sync login' first.")

    def _headers(self) -> Dict[str, str]:
        """Build request headers."""
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }

    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make an API request."""
        url = f"{self.api_url}{path}"
        resp = requests.request(method, url, headers=self._headers(), **kwargs)

        if resp.status_code >= 400:
            try:
                error = resp.json().get('error', resp.text)
            except Exception:
                error = resp.text
            raise CloudAPIError(f"API error ({resp.status_code}): {error}")

        return resp.json()

    @staticmethod
    def register(api_url: str, email: str, password: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Register a new user and get API key."""
        url = f"{api_url.rstrip('/')}/api/register"
        payload = {"email": email, "password": password}
        if name:
            payload["name"] = name

        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"})

        if resp.status_code >= 400:
            try:
                error = resp.json().get('error', resp.text)
            except Exception:
                error = resp.text
            raise CloudAPIError(f"Registration failed ({resp.status_code}): {error}")

        return resp.json()

    def upload_transcripts(self, transcripts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload transcripts to the cloud."""
        return self._request("POST", "/api/upload", json={"transcripts": transcripts})

    def list_transcripts(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """List transcripts in the cloud."""
        return self._request("GET", f"/api/transcripts?limit={limit}&offset={offset}")

    def search(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search transcripts."""
        return self._request("GET", f"/api/search?q={query}&limit={limit}")

    def get_stats(self) -> Dict[str, Any]:
        """Get user stats."""
        return self._request("GET", "/api/stats")


def prepare_transcript_for_upload(doc: Dict, transcript: Optional[List[Dict]]) -> Dict[str, Any]:
    """Prepare a document and transcript for upload to the cloud."""
    # Extract date
    created_at = doc.get('created_at', '')
    date_str = ''
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
        except Exception:
            date_str = created_at[:10] if len(created_at) >= 10 else ''

    # Extract attendees
    people = doc.get('people', [])
    attendees = []
    if people:
        attendees = [
            p.get('name', p.get('email', 'Unknown'))
            for p in people
            if isinstance(p, dict)
        ]

    # Format transcript text
    transcript_text = ''
    if transcript:
        lines = []
        for utt in transcript:
            speaker = utt.get('speaker', 'Unknown')
            text = utt.get('text', '')
            lines.append(f"{speaker}: {text}")
        transcript_text = '\n'.join(lines)

    # Extract notes
    notes = doc.get('notes_plain', '') or doc.get('notes_markdown', '')
    if not notes and doc.get('notes'):
        # Try to extract from ProseMirror structure
        notes = _extract_notes_text(doc.get('notes'))

    return {
        "id": doc.get('id'),
        "title": doc.get('title', 'Untitled Meeting'),
        "date": date_str,
        "created_at": created_at,
        "attendees": attendees,
        "summary": doc.get('summary', ''),
        "notes": notes,
        "transcript": transcript_text,
    }


def _extract_notes_text(notes) -> str:
    """Extract plain text from ProseMirror notes structure."""
    if not notes:
        return ""
    if isinstance(notes, str):
        return notes

    def extract_text(node):
        if isinstance(node, str):
            return node
        if isinstance(node, dict):
            if 'text' in node:
                return node['text']
            if 'content' in node:
                return ''.join(extract_text(c) for c in node['content'])
        if isinstance(node, list):
            return ''.join(extract_text(n) for n in node)
        return ''

    return extract_text(notes)
