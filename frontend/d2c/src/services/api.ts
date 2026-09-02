export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// ============================================================
//  INTERFACES
// ============================================================
export interface CoverageBlock {
  id: string;
  name: string;
  description: string;
  basePrice: number;
  icon: string;
  insurerName: string;
  category: string;
}

export interface PolicyState {
  holderName?: string;
  holderEmail?: string;
  age: number;
  gender: string;
  occupation: string;
  selectedCoverage: string[];
  estimatedPremium: number;
  naturalLanguageQuery?: string;
  dynamicFields?: Record<string, string>;
}

export interface UnderwritingResponse {
  status: "approved" | "declined" | "referred";
  premium_monthly: number;
  premium_annual: number;
  policy_number?: string;
  reason: string;
  plain_english_summary: string;
}

export interface ChatAction {
  action: string;
  message: string;
  data: Record<string, any>;
  suggestions: string[];
  product_matched?: string;
  role: string;
}

export interface PolicyInfo {
  policy_number: string;
  product_type: string;
  status: string;
  holder_name: string;
  holder_email?: string;
  premium_monthly: number | null;
  premium_annual: number | null;
  bound_at?: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  role: string;
}

// ============================================================
//  AUTH
// ============================================================
let _token: string | null = localStorage.getItem('ib_token');

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (_token) headers['Authorization'] = `Bearer ${_token}`;
  return headers;
}

export function getToken() { return _token; }
export function isLoggedIn() { return !!_token; }

export async function login(email: string, password: string): Promise<AuthToken> {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Login failed');
  }
  const data: AuthToken = await res.json();
  _token = data.access_token;
  localStorage.setItem('ib_token', data.access_token);
  localStorage.setItem('ib_role', data.role);
  return data;
}

export async function register(
  email: string, password: string, fullName: string, role = 'consumer'
): Promise<any> {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, full_name: fullName, role }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Registration failed');
  }
  return res.json();
}

export function logout() {
  _token = null;
  localStorage.removeItem('ib_token');
  localStorage.removeItem('ib_role');
}

// ============================================================
//  PRODUCTS & PREMIUM
// ============================================================
export async function getProducts(): Promise<CoverageBlock[]> {
  const res = await fetch(`${API_URL}/products`);
  if (!res.ok) throw new Error('Failed to fetch products');
  const data = await res.json();
  return data.map((item: any) => ({
    id: item.id,
    name: item.name,
    description: item.description,
    basePrice: item.base_price,
    icon: item.icon,
    insurerName: item.insurer_name || 'Unknown Insurer',
    category: item.category || 'life'
  }));
}

export async function calculatePremium(state: PolicyState): Promise<number> {
    const res = await fetch(`${API_URL}/calculate-premium`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        age: state.age,
        gender: state.gender,
        occupation: state.occupation,
        selected_coverage: state.selectedCoverage
      }),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(err || 'Failed to calculate premium');
    }
    const data = await res.json();
    return data.premium;
}

export async function getProductSchema(productType: string): Promise<any> {
    const res = await fetch(`${API_URL}/products/${productType}/schema`);
    if (!res.ok) throw new Error('Failed to fetch schema');
    return res.json();
}

// ============================================================
//  UNDERWRITING
// ============================================================
export async function submitUnderwriting(state: PolicyState): Promise<UnderwritingResponse> {
  const selectedProduct = state.selectedCoverage[0] || 'life_basic';
  let targetProductType = 'life';
  if (selectedProduct.includes('auto')) targetProductType = 'auto';
  else if (selectedProduct.includes('gadget') || selectedProduct.includes('screen') || selectedProduct.includes('extended')) targetProductType = 'gadget';
  else if (selectedProduct.includes('home')) targetProductType = 'home';

  const userFields = state.dynamicFields || {};

  const extras = Object.entries(userFields)
    .filter(([_, v]) => v && String(v).trim() !== '')
    .map(([k, v]) => `${k.replace(/_/g, ' ')}: ${v}`)
    .join(', ');

  const nlpQuery = `I am a ${state.age} year old ${state.gender} ${state.occupation} applying for ${targetProductType} insurance (${selectedProduct}). Underwriting Requirements: ${extras}.`;

  const res = await fetch(`${API_URL}/underwrite`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      holder_name: state.holderName || undefined,
      holder_email: state.holderEmail || undefined,
      age: state.age,
      gender: state.gender,
      occupation: state.occupation,
      role: "consumer",
      product_type: targetProductType,
      natural_language_query: nlpQuery,
      coverage_selection: [{ 
        id: selectedProduct, 
        name: selectedProduct, 
        description: selectedProduct, 
        base_price: state.estimatedPremium || 0, 
        icon: "Shield", 
        enabled: true 
      }]
    }),
  });
  if (!res.ok) {
    const error = await res.json();
    let msg = 'Underwriting failed';
    if (typeof error.detail === 'string') {
      msg = error.detail;
    } else if (Array.isArray(error.detail)) {
      msg = error.detail.map((e: any) => `${e.loc ? e.loc.filter((x: any) => x !== 'body').join('.') : ''}: ${e.msg}`).join('; ');
    }
    throw new Error(msg);
  }
  return res.json();
}

// ============================================================
//  MOCK PAYMENT
// ============================================================
export async function payForPolicy(policyNumber: string): Promise<any> {
  const res = await fetch(`${API_URL}/pay?policy_number=${encodeURIComponent(policyNumber)}`, {
    method: 'POST',
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Payment failed');
  }
  return res.json();
}

// ============================================================
//  POLICIES
// ============================================================
export async function getMyPolicies(email?: string): Promise<PolicyInfo[]> {
  const params = new URLSearchParams();
  if (email) params.set('holder_email', email);
  const suffix = params.toString() ? `?${params.toString()}` : '';

  const res = await fetch(`${API_URL}/policies/my${suffix}`, {
    method: 'GET',
    headers: authHeaders(),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch policies' }));
    throw new Error(err.detail || 'Failed to fetch policies');
  }

  return res.json();
}

// ============================================================
//  AGENTIC CHAT
// ============================================================
export async function sendChatMessage(
  message: string,
  role: 'consumer' | 'agent' | 'partner' = 'consumer',
  history: Array<{ role: 'user' | 'model'; content: string }> = []
): Promise<ChatAction> {
  try {
    const res = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, role, history }),
    });

    if (!res.ok) throw new Error('Chat API failed');
    return await res.json();
  } catch (err) {
    console.error("Chat Error", err);
    return {
      action: 'text_reply',
      message: "Sorry, I'm having trouble connecting. Please try again.",
      data: {},
      suggestions: ["Show products", "Get a quote"],
      role: 'system',
    };
  }
}
