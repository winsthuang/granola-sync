"""Export Granola documents to markdown files."""
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict


def sanitize_filename(name: str) -> str:
    """Create a safe filename from a title."""
    name = re.sub(r'[<>:"/\\|?*]', '-', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:100]


def format_transcript(utterances: List[Dict]) -> str:
    """Format transcript utterances into readable text."""
    if not utterances:
        return ""

    lines = []
    for utt in utterances:
        speaker = utt.get('speaker', 'Unknown')
        text = utt.get('text', '')
        timestamp = utt.get('start_timestamp', '')

        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S')
                lines.append(f"**[{time_str}] {speaker}:** {text}")
            except Exception:
                lines.append(f"**{speaker}:** {text}")
        else:
            lines.append(f"**{speaker}:** {text}")

    return "\n\n".join(lines)


def extract_notes_text(notes) -> str:
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


def export_document(
    doc: Dict,
    transcript: Optional[List[Dict]],
    output_dir: Path
) -> Path:
    """Export a single document with its transcript to markdown."""
    doc_id = doc.get('id', 'unknown')
    title = doc.get('title', 'Untitled Meeting')
    created_at = doc.get('created_at', '')
    summary = doc.get('summary', '')
    notes = (
        doc.get('notes_plain', '') or
        doc.get('notes_markdown', '') or
        extract_notes_text(doc.get('notes', ''))
    )
    people = doc.get('people', [])

    # Parse date for filename
    date_str = ''
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
        except Exception:
            date_str = created_at[:10]

    # Build filename
    safe_title = sanitize_filename(title)
    filename = f"{date_str}_{safe_title}.md" if date_str else f"{safe_title}.md"
    filepath = output_dir / filename

    # Build markdown content
    content = []
    content.append(f"# {title}")
    content.append("")
    content.append(f"**Date:** {created_at}")
    content.append(f"**Document ID:** {doc_id}")

    if people:
        attendees = [
            p.get('name', p.get('email', 'Unknown'))
            for p in people
            if isinstance(p, dict)
        ]
        if attendees:
            content.append(f"**Attendees:** {', '.join(attendees)}")

    content.append("")
    content.append("---")
    content.append("")

    if summary:
        content.append("## Summary")
        content.append("")
        content.append(summary)
        content.append("")

    if notes:
        content.append("## Notes")
        content.append("")
        content.append(notes)
        content.append("")

    if transcript:
        utterances = transcript if isinstance(transcript, list) else transcript.get('utterances', [])
        if utterances:
            content.append("## Transcript")
            content.append("")
            content.append(format_transcript(utterances))
            content.append("")

    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

    return filepath
