const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

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

export async function fetchSlaBreaches(token: string) {
  const res = await fetch(`${API_URL}/compliance/sla/breaches`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch SLA breaches');
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

export interface ChatAction {
  action: string;
  message: string;
  data: Record<string, any>;
  suggestions: string[];
  product_matched?: string;
  role: string;
}

export async function sendChatMessage(
  message: string,
  role: string = 'partner',
  token?: string
): Promise<ChatAction> {
  try {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    
    const payload = { 
      message, 
      role,
      history: []
    };

    const res = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Chat failed');
    return await res.json();
  } catch (err) {
    console.error("Chat Error", err);
    return {
      action: 'text_reply',
      message: "Sorry, I'm having trouble connecting. Please try again.",
      data: {},
      suggestions: ["Show my dashboard", "Generate API key"],
      role: 'system',
    }
  }
}

// ============================================================
//  SUPERADMIN ENDPOINTS
// ============================================================

export async function fetchGlobalMetrics(token: string) {
  const res = await fetch(`${API_URL}/admin/metrics`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch global metrics');
  return res.json();
}

export async function fetchTenants(token: string) {
  const res = await fetch(`${API_URL}/admin/tenants`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch tenants');
  return res.json();
}

export async function toggleTenantStatus(token: string, tenantId: string) {
  const res = await fetch(`${API_URL}/admin/tenants/${tenantId}/suspend`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to toggle tenant');
  return res.json();
}

export async function fetchPlatformConfigs(token: string) {
  const res = await fetch(`${API_URL}/admin/config`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch platform configs');
  return res.json();
}

export async function updatePlatformConfig(token: string, key: string, value: string) {
  const res = await fetch(`${API_URL}/admin/config/${key}`, {
    method: 'PUT',
    headers: { 
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}` 
    },
    body: JSON.stringify({ value })
  });
  if (!res.ok) throw new Error(`Failed to update config ${key}`);
  return res.json();
}
