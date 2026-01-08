# Granola Sync

Sync your Granola meeting transcripts to ChatGPT. Search and analyze your meetings with AI.

## Setup Guide

### Prerequisites
- macOS with [Granola](https://granola.ai) installed and logged in
- Python 3.9+ (check with `python3 --version`)

### Step 1: Install the sync tool
```bash
pip3 install git+https://github.com/winsthuang/granola-sync.git
```

### Step 2: Create your account and set a password
```bash
granola-sync login --api-url https://granola-api.hazel-health.workers.dev
```
- Press Enter to accept your Granola email
- Create a password (you'll use this to sign in via ChatGPT)
- Confirm the password

### Step 3: Upload your transcripts
```bash
granola-sync upload
```
This syncs all your Granola meetings to the cloud. Run this again anytime to sync new meetings.

### Step 4: Connect in ChatGPT
1. Open the GPT (get link from your admin)
2. Ask it anything (e.g., "Show my recent meetings")
3. It will prompt you to sign in
4. Enter your email and the password you created in Step 2

### You're done!

Now you can ask things like:
- "What meetings did I have this week?"
- "What did we discuss about [topic]?"
- "Find mentions of [person/project]"
- "What were the action items from my last meeting with [person]?"

### Syncing new meetings
Whenever you want to add new meetings, just run:
```bash
granola-sync upload
```

## Local Export Only

If you just want to export transcripts to local markdown files (no ChatGPT):
```bash
pip3 install git+https://github.com/winsthuang/granola-sync.git
granola-sync sync  # Exports to ~/Granola/transcripts/
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
