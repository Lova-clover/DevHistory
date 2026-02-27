// API client with cookie-based authentication
// All auth is handled via httpOnly Secure cookies (no localStorage tokens)

export async function fetchWithAuth(url: string, options: RequestInit = {}) {
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
    },
    credentials: 'include',  // sends httpOnly cookies automatically
  });
}

export async function logout() {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
  window.location.href = '/';
}
