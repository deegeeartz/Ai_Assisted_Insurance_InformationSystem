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

export async function fetchManuals(token: string) {
  const res = await fetch(`${API_URL}/manuals`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch manuals');
  return res.json();
}

export async function uploadManual(token: string, formData: FormData) {
    const res = await fetch(`${API_URL}/manuals/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
    });
    if (!res.ok) throw new Error('Failed to upload manual');
    return res.json();
}

export async function fetchSlaDashboard(token: string) {
  const res = await fetch(`${API_URL}/sla/dashboard`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch SLA dashboard');
  return res.json();
}

export async function registerWebhook(token: string, data: { event_type: string; url: string; secret: string }) {
  const res = await fetch(`${API_URL}/webhooks`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}` 
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to register webhook');
  return res.json();
}

export async function exportBatchCsv(token: string) {
  const res = await fetch(`${API_URL}/export/batch-csv`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to export CSV');
  return res.blob(); // Return blob for file download
}

export async function fetchRuleDetails(token: string, manualId: number) {
  const res = await fetch(`${API_URL}/compliance/rules/inspector?manual_id=${manualId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch rules');
  return res.json();
}
export async function underwrite(token: string, data: any, apiKey?: string) {
  const headers: any = { 
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}` 
  };
  if (apiKey) {
    headers['X-Api-Key'] = apiKey;
  }

  const res = await fetch(`${API_URL}/underwrite`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Underwriting failed');
  return res.json();
}
