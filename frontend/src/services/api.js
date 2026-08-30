/**
 * API Service for connecting to FastAPI Backend with HTTP-only Session Cookie Support
 */

// Custom backend URL from environment (e.g., VITE_API_URL=https://api.myproject.com)
const ENV_API_URL = import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL.replace(/\/$/, '') : '';

// Helper to determine if we are running on a local development machine
const isLocalhost = typeof window !== 'undefined' && (
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1' ||
  window.location.hostname === '0.0.0.0'
);

/**
 * Smart fetch helper:
 * - Uses ENV_API_URL if explicitly configured.
 * - Otherwise uses relative path `/api/...` (handled by Vite proxy in dev, and Vercel routing in prod).
 * - Enforces default 45-second timeout via AbortController.
 * - Always returns the HTTP Response object cleanly so callers can inspect real status codes and error JSON.
 */
async function smartFetch(path, options = {}, timeoutMs = 45000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const fetchOptions = {
    ...options,
    signal: options.signal || controller.signal,
    credentials: 'include',
  };

  const targetUrl = ENV_API_URL ? `${ENV_API_URL}${path}` : path;

  try {
    const res = await fetch(targetUrl, fetchOptions);
    clearTimeout(timeoutId);
    return res;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeoutMs / 1000}s. The server is taking too long to respond. Please try again.`);
    }

    // On local development, if relative path failed completely (network unreachable), try direct port 8000
    if (isLocalhost && !ENV_API_URL) {
      try {
        const directRes = await fetch(`http://127.0.0.1:8000${path}`, fetchOptions);
        return directRes;
      } catch (directErr) {
        throw new Error("Unable to connect to News AI backend on port 8000. Please ensure 'python run_app.py' is running.");
      }
    }

    throw new Error(`Network error connecting to API (${path}): ${err.message}`);
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function sendChatMessage(message, conversationId = null, language = 'auto') {
  try {
    const res = await smartFetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        language,
      }),
    }, 50000);
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const detail = errorData.detail || errorData.message || (
        res.status === 502
          ? 'Server gateway timeout (502). The serverless function took too long to start or respond. Please retry in a moment.'
          : res.status === 500
          ? 'Internal server error (500). Please verify your environment variables and database configuration.'
          : `Server returned HTTP ${res.status}`
      );
      throw new Error(detail);
    }
    return await res.json();
  } catch (err) {
    console.error('sendChatMessage error:', err);
    throw err;
  }
}

export async function fetchLatestNews(limit = 10) {
  try {
    const res = await smartFetch(`/api/news/latest?limit=${limit}`);
    if (!res.ok) throw new Error(`API returned ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('fetchLatestNews error:', err);
    return [];
  }
}

export async function fetchNewsByCategory(category, limit = 10) {
  try {
    const res = await smartFetch(`/api/news/category/${encodeURIComponent(category)}?limit=${limit}`);
    if (!res.ok) throw new Error(`API returned ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error(`fetchNewsByCategory error (${category}):`, err);
    return [];
  }
}

export async function sendVoiceChat(audioBlob, conversationId = null, language = 'auto') {
  try {
    const formData = new FormData();
    formData.append('file', audioBlob, 'speech_recording.wav');
    if (conversationId) formData.append('conversation_id', conversationId);
    if (language) formData.append('language', language);

    const res = await smartFetch('/api/voice/chat', {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(`Voice API returned status ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('sendVoiceChat error:', err);
    throw err;
  }
}

export async function fetchChatSessions() {
  try {
    const res = await smartFetch('/api/chat/sessions');
    if (!res.ok) throw new Error(`API returned ${res.status}`);
    const data = await res.json();
    return data.sessions || [];
  } catch (err) {
    console.error('fetchChatSessions error:', err);
    return [];
  }
}

// Authentication & Client DB Services

export async function registerUser({ name, email, password, country = 'Global', preferences = {} }) {
  const res = await smartFetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password, country, preferences }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Registration failed.');
  }
  return data;
}

export async function loginUser({ email, password }) {
  const res = await smartFetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Invalid email or password.');
  }
  return data;
}

export async function fetchClientsList() {
  try {
    const res = await smartFetch('/api/auth/clients');
    if (!res.ok) return [];
    const data = await res.json();
    return data.clients || [];
  } catch (err) {
    console.error('fetchClientsList error:', err);
    return [];
  }
}

export async function fetchCurrentUser(email) {
  try {
    const url = email ? `/api/auth/me?email=${encodeURIComponent(email)}` : '/api/auth/me';
    const res = await smartFetch(url);
    if (!res.ok) return null;
    const data = await res.json();
    return data.client || null;
  } catch (err) {
    return null;
  }
}

export async function logoutUser() {
  try {
    localStorage.removeItem('news_ai_user');
    localStorage.removeItem('news_ai_token');
    return { status: 'success' };
  } catch (err) {
    return { status: 'success' };
  }
}

export async function fetchUserSavedArticles() {
  try {
    const res = await smartFetch('/api/news/saved');
    if (!res.ok) return [];
    return await res.json();
  } catch (err) {
    return [];
  }
}

export async function saveUserArticle(article) {
  const res = await smartFetch('/api/news/saved', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url: article.url,
      title: article.title,
      source: article.source || 'News Source',
      published_at: article.published_at || '',
    }),
  });
  return await res.json();
}

export async function removeUserArticle(url) {
  const res = await smartFetch(`/api/news/saved?url=${encodeURIComponent(url)}`, {
    method: 'DELETE',
  });
  return await res.json();
}



