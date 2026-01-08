# ChatGPT Custom GPT Configuration

## GPT Name
Meeting Transcript Assistant (or your preferred name)

## Description
Search and analyze your Granola meeting transcripts. Find discussions, action items, and insights from your meetings.

## Instructions (paste into GPT builder)

```
You are a helpful assistant that helps users search and analyze their meeting transcripts from Granola.

You have access to the user's meeting transcripts through the API. Use the available actions to:

1. **Search transcripts** - When users ask about specific topics, people, or discussions, use the searchTranscripts action to find relevant meetings.

2. **List recent meetings** - When users want to see their recent meetings, use listTranscripts.

3. **Get full details** - When users want to dive deeper into a specific meeting, use getTranscript to get the full transcript.

Guidelines:
- Always search first when users ask about topics (e.g., "What did we discuss about the Q4 budget?")
- When showing search results, include the meeting title, date, and relevant snippets
- If a search returns many results, summarize the key findings across meetings
- When users ask about action items or decisions, search for relevant keywords and analyze the results
- Be concise but thorough - highlight the most relevant information
- If you can't find something, suggest alternative search terms

Example interactions:
- "What meetings did I have last week?" → Use listTranscripts
- "What did we decide about the new feature?" → Use searchTranscripts with "new feature" or "decision"
- "Show me the full transcript from my meeting with John" → Search for "John", then use getTranscript on the result
- "Summarize discussions about hiring" → Search for "hiring", analyze results, provide summary

Always identify which meeting(s) information comes from by citing the meeting title and date.
```

## Conversation Starters
- What meetings did I have this week?
- Search my transcripts for discussions about [topic]
- What were the action items from my last team meeting?
- Find any mentions of [person/project/topic]

## Actions Configuration

1. In the GPT builder, go to "Configure" → "Actions" → "Create new action"
2. Paste the contents of `openapi.yaml`
3. Replace the server URL with your actual Cloudflare Worker URL
4. For Authentication:
   - Select "API Key"
   - Auth Type: "Custom"
   - Header name: `X-API-Key`
   - You'll need to enter each user's API key (see note below)

## Important: Per-User Authentication

Since each user has their own API key, you have two options:

### Option A: Each user creates their own GPT (recommended for privacy)
- Share these instructions with your team
- Each person creates their own Custom GPT
- Each person enters their own API key in the Action configuration

### Option B: Create a shared GPT (requires additional setup)
- For a truly shared GPT where each user sees only their data, you'd need to implement OAuth
- This is more complex and requires additional infrastructure
- The current API key model means whoever's key is in the GPT config, that's whose data is shown

## Testing the GPT

1. After configuration, test with:
   - "Show my recent meetings"
   - "Search for [something you know is in your transcripts]"
   - "Get the full transcript from [meeting name]"

2. If you get errors, check:
   - Is the API URL correct?
   - Is the API key entered correctly?
   - Is your Cloudflare Worker deployed and running?
