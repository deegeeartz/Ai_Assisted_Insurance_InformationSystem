const API_URL = 'http://localhost:8000/api/v1';

export async function login(email: string, password: string) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(error.detail || 'Login failed');
  }
  return res.json();
}

export async function fetchMe(token: string) {
  const res = await fetch(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch user profile');
  return res.json();
}

export async function fetchPartnerDashboard(token: string) {
  const res = await fetch(`${API_URL}/partners/dashboard`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch dashboard');
  return res.json();
}

export async function fetchAuditLog(token: string) {
  const res = await fetch(`${API_URL}/compliance/audit-log`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch audit log');
  return res.json();
}

export async function rotateApiKey(token: string) {
  const res = await fetch(`${API_URL}/partners/api-key/rotate`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.json();
}
