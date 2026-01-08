/**
 * Granola Transcript API
 * Cloudflare Worker for storing and searching meeting transcripts
 * With OAuth support for ChatGPT Actions
 */

// CORS headers for ChatGPT Actions
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key',
};

// Helper: JSON response
function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders },
  });
}

// Helper: Error response
function errorResponse(message, status = 400) {
  return jsonResponse({ error: message }, status);
}

// Helper: HTML response
function htmlResponse(html, status = 200) {
  return new Response(html, {
    status,
    headers: { 'Content-Type': 'text/html', ...corsHeaders },
  });
}

// Helper: Hash password using SHA-256
async function hashPassword(password) {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Helper: Authenticate request via API key or Bearer token
async function authenticate(request, env) {
  const apiKey = request.headers.get('X-API-Key') ||
                 request.headers.get('Authorization')?.replace('Bearer ', '');

  if (!apiKey) {
    return null;
  }

  // Look up user by API key
  const userData = await env.USERS.get(`apikey:${apiKey}`);
  if (!userData) {
    return null;
  }

  return JSON.parse(userData);
}

// ============ OAuth Endpoints ============

// GET /oauth/authorize - Show login form
async function handleOAuthAuthorize(request, env) {
  const url = new URL(request.url);
  const clientId = url.searchParams.get('client_id');
  const redirectUri = url.searchParams.get('redirect_uri');
  const state = url.searchParams.get('state');
  const responseType = url.searchParams.get('response_type');
  const error = url.searchParams.get('error');

  const errorHtml = error ? `<div class="error">${error}</div>` : '';

  const html = `
<!DOCTYPE html>
<html>
<head>
  <title>Granola - Connect Your Account</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0;
      padding: 20px;
    }
    .container {
      background: white;
      padding: 40px;
      border-radius: 16px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      max-width: 400px;
      width: 100%;
    }
    h1 {
      margin: 0 0 8px 0;
      font-size: 24px;
      color: #1a1a1a;
    }
    p {
      color: #666;
      margin: 0 0 24px 0;
      font-size: 14px;
    }
    label {
      display: block;
      margin-bottom: 8px;
      font-weight: 500;
      color: #333;
    }
    input[type="email"], input[type="password"] {
      width: 100%;
      padding: 12px 16px;
      border: 2px solid #e0e0e0;
      border-radius: 8px;
      font-size: 16px;
      margin-bottom: 20px;
      transition: border-color 0.2s;
    }
    input[type="email"]:focus, input[type="password"]:focus {
      outline: none;
      border-color: #667eea;
    }
    button {
      width: 100%;
      padding: 14px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    button:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    .error {
      background: #fee;
      color: #c00;
      padding: 12px;
      border-radius: 8px;
      margin-bottom: 20px;
      font-size: 14px;
    }
    .info {
      background: #f0f7ff;
      color: #0066cc;
      padding: 12px;
      border-radius: 8px;
      margin-bottom: 20px;
      font-size: 13px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>🎙️ Granola Transcripts</h1>
    <p>Connect your account to access your meeting transcripts in ChatGPT.</p>

    ${errorHtml}

    <form method="POST" action="/oauth/authorize">
      <input type="hidden" name="client_id" value="${clientId || ''}">
      <input type="hidden" name="redirect_uri" value="${redirectUri || ''}">
      <input type="hidden" name="state" value="${state || ''}">
      <input type="hidden" name="response_type" value="${responseType || 'code'}">

      <label for="email">Email Address</label>
      <input type="email" id="email" name="email" placeholder="you@company.com" required autofocus>

      <label for="password">Password</label>
      <input type="password" id="password" name="password" placeholder="Your password" required>

      <button type="submit">Sign In</button>
    </form>
  </div>
</body>
</html>
  `;

  return htmlResponse(html);
}

// POST /oauth/authorize - Process login form
async function handleOAuthAuthorizePost(request, env) {
  const formData = await request.formData();
  const email = formData.get('email')?.toLowerCase().trim();
  const password = formData.get('password');
  const redirectUri = formData.get('redirect_uri');
  const state = formData.get('state');
  const clientId = formData.get('client_id');
  const responseType = formData.get('response_type');

  if (!email || !password) {
    const params = new URLSearchParams({
      client_id: clientId || '',
      redirect_uri: redirectUri || '',
      state: state || '',
      response_type: responseType || 'code',
      error: 'Email and password are required.',
    });
    return Response.redirect(`/oauth/authorize?${params}`, 302);
  }

  // Look up user by email
  const userData = await env.USERS.get(`user:${email}`);
  if (!userData) {
    const params = new URLSearchParams({
      client_id: clientId || '',
      redirect_uri: redirectUri || '',
      state: state || '',
      response_type: responseType || 'code',
      error: 'Account not found. Make sure you have run granola-sync login first.',
    });
    return Response.redirect(`/oauth/authorize?${params}`, 302);
  }

  const user = JSON.parse(userData);

  // Verify password
  const hashedPassword = await hashPassword(password);
  if (user.passwordHash !== hashedPassword) {
    const params = new URLSearchParams({
      client_id: clientId || '',
      redirect_uri: redirectUri || '',
      state: state || '',
      response_type: responseType || 'code',
      error: 'Incorrect password.',
    });
    return Response.redirect(`/oauth/authorize?${params}`, 302);
  }

  // Generate authorization code (valid for 5 minutes)
  const authCode = crypto.randomUUID();
  const codeData = {
    userId: user.id,
    email: user.email,
    apiKey: user.apiKey,
    createdAt: Date.now(),
    expiresAt: Date.now() + (5 * 60 * 1000),
  };

  await env.USERS.put(`authcode:${authCode}`, JSON.stringify(codeData), {
    expirationTtl: 300,
  });

  // Redirect back to ChatGPT with the code
  const redirectUrl = new URL(redirectUri);
  redirectUrl.searchParams.set('code', authCode);
  if (state) {
    redirectUrl.searchParams.set('state', state);
  }

  return Response.redirect(redirectUrl.toString(), 302);
}

// POST /oauth/token - Exchange code for access token
async function handleOAuthToken(request, env) {
  let grantType, code, refreshToken;

  const contentType = request.headers.get('content-type') || '';
  if (contentType.includes('application/x-www-form-urlencoded')) {
    const formData = await request.formData();
    grantType = formData.get('grant_type');
    code = formData.get('code');
    refreshToken = formData.get('refresh_token');
  } else {
    const body = await request.json();
    grantType = body.grant_type;
    code = body.code;
    refreshToken = body.refresh_token;
  }

  // Handle refresh token
  if (grantType === 'refresh_token' && refreshToken) {
    const tokenData = await env.USERS.get(`refresh:${refreshToken}`);
    if (!tokenData) {
      return jsonResponse({ error: 'invalid_grant', error_description: 'Invalid refresh token' }, 400);
    }

    const data = JSON.parse(tokenData);
    const user = await env.USERS.get(`userid:${data.userId}`);
    if (!user) {
      return jsonResponse({ error: 'invalid_grant', error_description: 'User not found' }, 400);
    }

    const userData = JSON.parse(user);

    const newRefreshToken = 'gra_refresh_' + crypto.randomUUID().replace(/-/g, '');
    await env.USERS.put(`refresh:${newRefreshToken}`, JSON.stringify({ userId: userData.id }), {
      expirationTtl: 30 * 24 * 60 * 60,
    });

    await env.USERS.delete(`refresh:${refreshToken}`);

    return jsonResponse({
      access_token: userData.apiKey,
      token_type: 'Bearer',
      expires_in: 3600,
      refresh_token: newRefreshToken,
    });
  }

  // Handle authorization code
  if (grantType === 'authorization_code' && code) {
    const codeData = await env.USERS.get(`authcode:${code}`);
    if (!codeData) {
      return jsonResponse({ error: 'invalid_grant', error_description: 'Invalid or expired code' }, 400);
    }

    const data = JSON.parse(codeData);

    if (Date.now() > data.expiresAt) {
      await env.USERS.delete(`authcode:${code}`);
      return jsonResponse({ error: 'invalid_grant', error_description: 'Code expired' }, 400);
    }

    await env.USERS.delete(`authcode:${code}`);

    const newRefreshToken = 'gra_refresh_' + crypto.randomUUID().replace(/-/g, '');
    await env.USERS.put(`refresh:${newRefreshToken}`, JSON.stringify({ userId: data.userId }), {
      expirationTtl: 30 * 24 * 60 * 60,
    });

    return jsonResponse({
      access_token: data.apiKey,
      token_type: 'Bearer',
      expires_in: 3600,
      refresh_token: newRefreshToken,
    });
  }

  return jsonResponse({ error: 'unsupported_grant_type' }, 400);
}

// ============ API Endpoints ============

// POST /api/register - Register a new user
async function handleRegister(request, env) {
  const { email, name, password } = await request.json();

  if (!email) {
    return errorResponse('Email is required');
  }

  if (!password) {
    return errorResponse('Password is required');
  }

  const emailLower = email.toLowerCase().trim();
  const passwordHash = await hashPassword(password);

  // Check if user already exists
  const existing = await env.USERS.get(`user:${emailLower}`);
  if (existing) {
    // Update password if user exists
    const user = JSON.parse(existing);
    user.passwordHash = passwordHash;

    // Update all user records
    await env.USERS.put(`user:${emailLower}`, JSON.stringify(user));
    await env.USERS.put(`apikey:${user.apiKey}`, JSON.stringify(user));
    await env.USERS.put(`userid:${user.id}`, JSON.stringify(user));

    return jsonResponse({
      message: 'Password updated',
      api_key: user.apiKey,
      user_id: user.id
    });
  }

  // Generate API key and user ID
  const userId = crypto.randomUUID();
  const apiKey = 'gra_' + crypto.randomUUID().replace(/-/g, '');

  const user = {
    id: userId,
    email: emailLower,
    name: name || emailLower.split('@')[0],
    apiKey,
    passwordHash,
    createdAt: new Date().toISOString(),
  };

  // Store user data
  await env.USERS.put(`user:${emailLower}`, JSON.stringify(user));
  await env.USERS.put(`apikey:${apiKey}`, JSON.stringify(user));
  await env.USERS.put(`userid:${userId}`, JSON.stringify(user));

  return jsonResponse({
    message: 'User registered successfully',
    api_key: apiKey,
    user_id: userId,
  });
}

// POST /api/upload - Upload transcripts
async function handleUpload(request, env, user) {
  const { transcripts } = await request.json();

  if (!transcripts || !Array.isArray(transcripts)) {
    return errorResponse('transcripts array is required');
  }

  let uploaded = 0;
  let updated = 0;

  for (const transcript of transcripts) {
    const key = `transcript:${user.id}:${transcript.id}`;

    const existing = await env.TRANSCRIPTS.get(key);
    if (existing) {
      updated++;
    } else {
      uploaded++;
    }

    const data = {
      ...transcript,
      userId: user.id,
      uploadedAt: new Date().toISOString(),
    };

    await env.TRANSCRIPTS.put(key, JSON.stringify(data));
  }

  const indexKey = `index:${user.id}`;
  const existingIndex = await env.TRANSCRIPTS.get(indexKey);
  const index = existingIndex ? JSON.parse(existingIndex) : { transcriptIds: [] };

  for (const transcript of transcripts) {
    if (!index.transcriptIds.includes(transcript.id)) {
      index.transcriptIds.push(transcript.id);
    }
  }
  index.lastUpdated = new Date().toISOString();

  await env.TRANSCRIPTS.put(indexKey, JSON.stringify(index));

  return jsonResponse({
    message: 'Upload successful',
    uploaded,
    updated,
    total: index.transcriptIds.length,
  });
}

// GET /api/transcripts - List user's transcripts
async function handleListTranscripts(request, env, user) {
  const url = new URL(request.url);
  const limit = parseInt(url.searchParams.get('limit') || '50');
  const offset = parseInt(url.searchParams.get('offset') || '0');

  const indexKey = `index:${user.id}`;
  const indexData = await env.TRANSCRIPTS.get(indexKey);

  if (!indexData) {
    return jsonResponse({ transcripts: [], total: 0 });
  }

  const index = JSON.parse(indexData);
  const transcriptIds = index.transcriptIds.slice(offset, offset + limit);

  const transcripts = [];
  for (const id of transcriptIds) {
    const key = `transcript:${user.id}:${id}`;
    const data = await env.TRANSCRIPTS.get(key);
    if (data) {
      const transcript = JSON.parse(data);
      transcripts.push({
        id: transcript.id,
        title: transcript.title,
        date: transcript.date,
        attendees: transcript.attendees,
        summary: transcript.summary,
      });
    }
  }

  return jsonResponse({
    transcripts,
    total: index.transcriptIds.length,
    limit,
    offset,
  });
}

// GET /api/transcript/:id - Get a specific transcript
async function handleGetTranscript(request, env, user, transcriptId) {
  const key = `transcript:${user.id}:${transcriptId}`;
  const data = await env.TRANSCRIPTS.get(key);

  if (!data) {
    return errorResponse('Transcript not found', 404);
  }

  return jsonResponse(JSON.parse(data));
}

// GET /api/search - Search transcripts
async function handleSearch(request, env, user) {
  const url = new URL(request.url);
  const query = url.searchParams.get('q')?.toLowerCase();
  const limit = parseInt(url.searchParams.get('limit') || '20');

  if (!query) {
    return errorResponse('Search query (q) is required');
  }

  const indexKey = `index:${user.id}`;
  const indexData = await env.TRANSCRIPTS.get(indexKey);

  if (!indexData) {
    return jsonResponse({ results: [], total: 0, query });
  }

  const index = JSON.parse(indexData);
  const results = [];

  for (const id of index.transcriptIds) {
    if (results.length >= limit) break;

    const key = `transcript:${user.id}:${id}`;
    const data = await env.TRANSCRIPTS.get(key);

    if (data) {
      const transcript = JSON.parse(data);
      const searchText = [
        transcript.title,
        transcript.summary,
        transcript.notes,
        transcript.transcript,
      ].filter(Boolean).join(' ').toLowerCase();

      if (searchText.includes(query)) {
        const snippets = findSnippets(searchText, query);

        results.push({
          id: transcript.id,
          title: transcript.title,
          date: transcript.date,
          attendees: transcript.attendees,
          summary: transcript.summary,
          snippets,
          relevance: countOccurrences(searchText, query),
        });
      }
    }
  }

  results.sort((a, b) => b.relevance - a.relevance);

  return jsonResponse({
    results,
    total: results.length,
    query,
  });
}

// Helper: Find snippets around search term
function findSnippets(text, query, maxSnippets = 3, contextChars = 100) {
  const snippets = [];
  let searchIndex = 0;

  while (snippets.length < maxSnippets) {
    const index = text.indexOf(query, searchIndex);
    if (index === -1) break;

    const start = Math.max(0, index - contextChars);
    const end = Math.min(text.length, index + query.length + contextChars);

    let snippet = text.slice(start, end);
    if (start > 0) snippet = '...' + snippet;
    if (end < text.length) snippet = snippet + '...';

    snippets.push(snippet);
    searchIndex = index + query.length;
  }

  return snippets;
}

// Helper: Count occurrences
function countOccurrences(text, query) {
  let count = 0;
  let index = 0;
  while ((index = text.indexOf(query, index)) !== -1) {
    count++;
    index += query.length;
  }
  return count;
}

// GET /api/stats - Get user stats
async function handleStats(request, env, user) {
  const indexKey = `index:${user.id}`;
  const indexData = await env.TRANSCRIPTS.get(indexKey);

  if (!indexData) {
    return jsonResponse({
      totalTranscripts: 0,
      lastUpdated: null,
      user: { name: user.name, email: user.email }
    });
  }

  const index = JSON.parse(indexData);

  return jsonResponse({
    totalTranscripts: index.transcriptIds.length,
    lastUpdated: index.lastUpdated,
    user: { name: user.name, email: user.email },
  });
}

// ============ Main Request Handler ============

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;

    // Handle CORS preflight
    if (method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Health check
    if (path === '/' || path === '/health') {
      return jsonResponse({ status: 'ok', service: 'granola-api' });
    }

    // OAuth endpoints (no auth required)
    if (path === '/oauth/authorize' && method === 'GET') {
      return handleOAuthAuthorize(request, env);
    }

    if (path === '/oauth/authorize' && method === 'POST') {
      return handleOAuthAuthorizePost(request, env);
    }

    if (path === '/oauth/token' && method === 'POST') {
      return handleOAuthToken(request, env);
    }

    // Registration endpoint (no auth required)
    if (path === '/api/register' && method === 'POST') {
      return handleRegister(request, env);
    }

    // All other endpoints require authentication
    const user = await authenticate(request, env);
    if (!user) {
      return errorResponse('Invalid or missing API key', 401);
    }

    // Route requests
    if (path === '/api/upload' && method === 'POST') {
      return handleUpload(request, env, user);
    }

    if (path === '/api/transcripts' && method === 'GET') {
      return handleListTranscripts(request, env, user);
    }

    if (path.startsWith('/api/transcript/') && method === 'GET') {
      const transcriptId = path.replace('/api/transcript/', '');
      return handleGetTranscript(request, env, user, transcriptId);
    }

    if (path === '/api/search' && method === 'GET') {
      return handleSearch(request, env, user);
    }

    if (path === '/api/stats' && method === 'GET') {
      return handleStats(request, env, user);
    }

    return errorResponse('Not found', 404);
  },
};
