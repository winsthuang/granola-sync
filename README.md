# Granola Sync

Sync your Granola meeting transcripts to local folders or a cloud API for ChatGPT integration.

## Features

- Export Granola transcripts to local markdown files
- Upload transcripts to a cloud API (Cloudflare Workers)
- Search transcripts via ChatGPT Custom GPT
- Per-user data isolation (each person sees only their own transcripts)

## Quick Start

### Local Export Only
```bash
pip3 install ./granola-sync
granola-sync sync  # Exports to ~/Granola/transcripts/
```

### Cloud + ChatGPT Integration
```bash
# 1. Deploy the API (see DEPLOYMENT.md)
# 2. Install and login
pip3 install ./granola-sync
granola-sync login --api-url https://your-api.workers.dev

# 3. Upload transcripts
granola-sync upload

# 4. Set up ChatGPT Custom GPT (see DEPLOYMENT.md)
```

## Project Structure

```
Granola/
├── README.md              # This file
├── DEPLOYMENT.md          # Full deployment guide
├── granola-sync/          # CLI tool (pip installable)
│   ├── pyproject.toml
│   ├── README.md
│   └── src/
│       └── granola_sync/
│           ├── __init__.py
│           ├── api.py      # Granola API client
│           ├── cli.py      # CLI commands
│           ├── cloud.py    # Cloud API client
│           ├── config.py   # Configuration management
│           └── export.py   # Markdown export
├── granola-api/           # Cloudflare Worker API
│   ├── wrangler.toml      # Cloudflare config
│   ├── package.json
│   ├── openapi.yaml       # ChatGPT Action spec
│   ├── chatgpt-gpt-instructions.md
│   └── src/
│       └── index.js       # API implementation
└── transcripts/           # Your exported transcripts (gitignored)
```

## Commands

```bash
# Local operations
granola-sync status      # Check Granola connection
granola-sync sync        # Export to local folder
granola-sync info        # Show local transcript stats

# Cloud operations
granola-sync login       # Login to cloud API
granola-sync upload      # Upload transcripts to cloud
granola-sync cloud-status # Check cloud connection
granola-sync logout      # Clear cloud credentials
```

## Requirements

- macOS (Granola is Mac-only)
- Python 3.9+
- Granola app installed and logged in
- (For cloud) Cloudflare account (free)

## How It Works

1. **granola-sync** reads your credentials from Granola's local storage
2. Fetches your documents and transcripts via Granola's API
3. Either exports to local markdown files or uploads to your cloud API
4. ChatGPT Custom GPT queries the cloud API with your API key
5. Each user's data is isolated by their unique API key

## Privacy

- Local mode: All data stays on your machine
- Cloud mode: Data is stored in Cloudflare KV, isolated per user
- The API admin can technically access all data (same as any SaaS)
- For maximum privacy, each user can host their own Worker

## License

MIT
