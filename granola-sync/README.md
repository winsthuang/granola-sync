# Granola Sync

Export your Granola meeting transcripts to local markdown files.

## Installation

### For Hazel team members:

```bash
# 1. Install the package
pip3 install ~/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/Claude\ Code/Granola/granola-sync

# 2. Add to your PATH (add this line to ~/.zshrc)
export PATH="$HOME/Library/Python/3.9/bin:$PATH"

# 3. Reload shell config
source ~/.zshrc
```

### For external users:

```bash
# Clone or copy the granola-sync folder, then:
pip3 install /path/to/granola-sync
```

## Prerequisites

1. **Granola must be installed** on your Mac
2. **You must be logged into Granola** (the tool reads your local credentials)

## Usage

### Sync your transcripts

```bash
# Sync all transcripts to ~/Granola/transcripts/
granola-sync sync

# Sync to a custom location
granola-sync sync --output ~/Documents/MeetingNotes/

# Test with just 5 documents
granola-sync sync --limit 5
```

### Check connection status

```bash
granola-sync status
```

### View transcript info

```bash
granola-sync info
```

## Output Format

Each meeting is exported as a markdown file with:
- **Title** and date
- **Attendees** (if available)
- **Summary** (if Granola generated one)
- **Notes** (your typed notes)
- **Full transcript** with timestamps

Example filename: `2024-01-15_Weekly Team Sync.md`

## Using with ChatGPT

### Option A: Upload to Custom GPT
1. Run `granola-sync sync` to get your transcripts
2. In ChatGPT, create a Custom GPT
3. Upload your .md files to the "Knowledge" section
4. Query away!

### Option B: ChatGPT Desktop App (macOS)
1. Run `granola-sync sync`
2. In ChatGPT desktop app, you can reference local files
3. Drag files into the chat or use file picker

### Option C: Scheduled Sync
Set up a cron job or launchd to run `granola-sync sync` periodically.

## Troubleshooting

**"Granola credentials not found"**
- Make sure Granola is installed and you're logged in
- Check that `~/Library/Application Support/Granola/supabase.json` exists

**"401 Unauthorized"**
- Your Granola session may have expired
- Open Granola app to refresh your credentials

## Privacy

- All data stays local on your machine
- No data is sent anywhere except to Granola's API (to fetch your own transcripts)
- Your credentials are read from Granola's local storage
