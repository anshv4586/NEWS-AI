/**
 * API Service for connecting to FastAPI Backend with HTTP-only Session Cookie Support
 */

const DIRECT_URL = 'http://127.0.0.1:8000';

/**
 * Smart fetch helper: calls FastAPI backend directly at http://127.0.0.1:8000 first,
 * automatically transmitting HTTP-only cookies with credentials: 'include'.
 */
async function smartFetch(path, options = {}) {
  const fetchOptions = {
    ...options,
    credentials: 'include',
  };

  try {
    const res = await fetch(`${DIRECT_URL}${path}`, fetchOptions);
    if (res.ok) return res;

    // Fallback attempt: relative path proxy
    const relRes = await fetch(path, fetchOptions);
    return relRes;
  } catch (err) {
    // Second attempt: relative path proxy
    try {
      const relRes = await fetch(path, fetchOptions);
      return relRes;
    } catch (relErr) {
      throw new Error("Unable to connect to News AI backend on port 8000. Please ensure 'python run_app.py' is running.");
    }
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
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const detail = errorData.detail || `Server returned HTTP ${res.status}`;
      throw new Error(`Backend Error: ${detail}`);
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

// Authentication API Services

export async function sendOtp(identifier, authType = 'email', countryCode = '+91') {
  const res = await smartFetch('/api/auth/send-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ identifier, auth_type: authType, country_code: countryCode }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Failed to send OTP verification code.');
  }
  return data;
}

export async function verifyOtp(identifier, authType, otpCode, countryCode = '+91') {
  const res = await smartFetch('/api/auth/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ identifier, auth_type: authType, otp_code: otpCode, country_code: countryCode }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Invalid or expired OTP code.');
  }
  return data;
}

export async function fetchCurrentUser() {
  try {
    const res = await smartFetch('/api/auth/me');
    if (!res.ok) return { authenticated: false, user: null };
    return await res.json();
  } catch (err) {
    return { authenticated: false, user: null };
  }
}

export async function logoutUser() {
  try {
    const res = await smartFetch('/api/auth/logout', { method: 'POST' });
    return await res.json();
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



