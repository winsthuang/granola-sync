# Granola Sync - Deployment Guide

This guide walks you through deploying the Granola transcript sync system.

## Architecture Overview

```
┌─────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   Granola   │───▶│  granola-sync   │───▶│  Cloudflare API  │
│   (local)   │    │  (CLI tool)     │    │  (Worker + KV)   │
└─────────────┘    └─────────────────┘    └──────────────────┘
                                                   │
                                                   ▼
                                          ┌──────────────────┐
                                          │  ChatGPT GPT     │
                                          │  (Actions)       │
                                          └──────────────────┘
```

## Part 1: Deploy the Cloudflare Worker API

### Prerequisites
- Node.js installed (v16+)
- A free Cloudflare account

### Step 1: Create Cloudflare Account
1. Go to https://dash.cloudflare.com/sign-up
2. Sign up with email (free, no credit card required)

### Step 2: Install Wrangler CLI
```bash
npm install -g wrangler
wrangler login  # Opens browser to authenticate
```

### Step 3: Create KV Namespaces
```bash
# Create storage for transcripts
wrangler kv:namespace create "TRANSCRIPTS"
# Note the ID that's returned, e.g., "abc123..."

# Create storage for users
wrangler kv:namespace create "USERS"
# Note this ID too, e.g., "def456..."
```

### Step 4: Configure the Worker
Edit `granola-api/wrangler.toml` and add your KV namespace IDs:

```toml
name = "granola-api"
main = "src/index.js"
compatibility_date = "2024-01-01"

[[kv_namespaces]]
binding = "TRANSCRIPTS"
id = "abc123..."  # Replace with your TRANSCRIPTS ID

[[kv_namespaces]]
binding = "USERS"
id = "def456..."  # Replace with your USERS ID
```

### Step 5: Deploy
```bash
cd granola-api
npm install
wrangler deploy
```

You'll get a URL like: `https://granola-api.your-subdomain.workers.dev`

**Save this URL** - you'll need it for the CLI and ChatGPT setup.

### Step 6: Test the API
```bash
curl https://granola-api.your-subdomain.workers.dev/health
# Should return: {"status":"ok","service":"granola-api"}
```

---

## Part 2: Install the CLI Tool

### For You (Admin)
```bash
# Install the CLI
pip3 install ~/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/Claude\ Code/Granola/granola-sync

# Add to PATH (add to ~/.zshrc for persistence)
export PATH="$HOME/Library/Python/3.9/bin:$PATH"

# Login to your API
granola-sync login --api-url https://granola-api.your-subdomain.workers.dev

# Upload your transcripts
granola-sync upload
```

### For Coworkers
Share these instructions:

```bash
# 1. Install
pip3 install ~/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/Claude\ Code/Granola/granola-sync

# 2. Add to PATH (one-time)
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 3. Login (use URL provided by admin)
granola-sync login --api-url https://granola-api.XXXXX.workers.dev

# 4. Upload transcripts
granola-sync upload

# 5. (Optional) Run periodically to keep in sync
granola-sync upload
```

---

## Part 3: Set Up ChatGPT Custom GPT

### Step 1: Create the GPT
1. Go to https://chat.openai.com
2. Click your profile → "My GPTs" → "Create a GPT"
3. Click "Configure" tab

### Step 2: Configure Basics
- **Name**: Meeting Transcript Assistant
- **Description**: Search and analyze your Granola meeting transcripts
- **Instructions**: Copy from `granola-api/chatgpt-gpt-instructions.md`

### Step 3: Add the Action
1. Scroll down to "Actions" → "Create new action"
2. Copy contents of `granola-api/openapi.yaml`
3. **Important**: Replace the server URL with your actual Cloudflare Worker URL
4. Click "Save"

### Step 4: Configure Authentication
1. In the Action settings, click "Authentication"
2. Select "API Key"
3. Auth Type: "Custom"
4. Custom Header Name: `X-API-Key`
5. Enter your API key (from `granola-sync login` output)

### Step 5: Test
Try these prompts:
- "Show my recent meetings"
- "Search for discussions about [topic]"

---

## Part 4: Sharing with Your Team

### Option A: Each Person Creates Their Own GPT (Recommended)
1. Share the GPT instructions and OpenAPI spec
2. Each person creates their own Custom GPT
3. Each person uses their own API key
4. **Pros**: True privacy, each person sees only their data
5. **Cons**: Everyone creates their own GPT

### Option B: Shared GPT Template
1. Create the GPT as above
2. Don't add authentication in the GPT config
3. Each user will need to pass their API key in each request
4. This is less seamless but allows a shared GPT

---

## Troubleshooting

### "Command not found: granola-sync"
Add Python bin to PATH:
```bash
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
```

### "Granola credentials not found"
Make sure Granola app is installed and you're logged in.

### "API error 401"
Your API key is invalid or not set. Run `granola-sync login` again.

### "KV namespace not found"
Make sure you created the KV namespaces and added their IDs to `wrangler.toml`.

### ChatGPT Action errors
1. Check the API URL is correct (no trailing slash)
2. Check the API key is entered correctly
3. Test the API directly with curl first

---

## Commands Reference

```bash
# Check Granola connection
granola-sync status

# Check cloud connection
granola-sync cloud-status

# Upload transcripts to cloud
granola-sync upload

# Upload with limit (for testing)
granola-sync upload --limit 10

# Sync to local folder (no cloud)
granola-sync sync

# Logout from cloud
granola-sync logout
```

---

## Security Notes

- Each user's transcripts are stored separately in Cloudflare KV
- API keys are unique per user
- The admin (you) can technically access all data in the KV store
- For maximum privacy, each user should host their own Worker (but this adds complexity)
- Consider your team's privacy requirements when deciding on the setup
