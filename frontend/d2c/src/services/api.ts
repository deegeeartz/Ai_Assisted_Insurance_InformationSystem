const API_URL = 'http://localhost:8000/api/v1';

export interface CoverageBlock {
  id: string;
  name: string;
  description: string;
  basePrice: number;
  icon: string; // Lucide icon name
}

export interface PolicyState {
  age: number;
  gender: string;
  occupation: string;
  selectedCoverage: string[]; // IDs
  estimatedPremium: number;
  naturalLanguageQuery?: string;
}

export interface UnderwritingResponse {
  status: "approved" | "declined" | "referred";
  premium_monthly: number;
  premium_annual: number;
  policy_number?: string;
  reason: string;
  plain_english_summary: string;
}

// Fetch available products from backend
export async function getProducts(): Promise<CoverageBlock[]> {
  try {
    const res = await fetch(`${API_URL}/products`);
    if (!res.ok) throw new Error('Failed to fetch products');
    const data = await res.json();
    
    // Map backend snake_case to frontend camelCase
    return data.map((item: any) => ({
      id: item.id,
      name: item.name,
      description: item.description,
      basePrice: item.base_price,
      icon: item.icon
    }));
  } catch (err) {
    console.error("API Error, falling back to mock", err);
    // Fallback if backend is down (for demo resilience)
    return [
      {
        id: "life_basic",
        name: "Life Protection (Offline)",
        description: "Backend unreachable. Using cached data.",
        basePrice: 5000,
        icon: "Heart"
      }
    ];
  }
}

export async function calculatePremium(state: PolicyState): Promise<number> {
  try {
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

    if (!res.ok) throw new Error('Failed to calculate premium');
    const data = await res.json();
    return data.premium;
  } catch (err) {
    console.error("Calculation Error", err);
    return 0;
  }
}

export async function submitUnderwriting(state: PolicyState): Promise<UnderwritingResponse> {
  // Convert basic state to Full Underwrite Request
  // In a real app, we'd map the coverage IDs to full objects if needed, 
  // but for now we'll rely on natural language inference or simple ID passing if backend supports it.
  // The backend route_to_product might need 'product_type' or inferred from 'natural_language_query'.
  // We'll simulate a "Life" request if life is selected.
  
  const productType = state.selectedCoverage.join(', ') || "General Insurance";
  
  const res = await fetch(`${API_URL}/underwrite`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      age: state.age,
      gender: state.gender,
      occupation: state.occupation,
      role: "consumer",
      // We pass a constructed query to help the router
      natural_language_query: `I am a ${state.age} year old ${state.gender} ${state.occupation} looking for ${productType}.`,
      coverage_selection: [] // Backend can infer or we can pass full objects if we had them here
      // For this hackathon, let's rely on the NL query to pick the 'Life' manual primarily
    }),
  });

  if (!res.ok) {
     const error = await res.json();
     throw new Error(error.detail || 'Underwriting failed');
  }
  return res.json();
}

export async function processPayment(amount: number, policyNumber: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/payments/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        policy_number: policyNumber,
        amount: amount,
        currency: "NGN",
        gateway: "paystack" // Hardcoded for demo
      }),
    });

    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Payment failed');
    }
    return true;
  } catch (e) {
    console.error(e);
    throw e;
  }
}

export interface ChatResponse {
  message: string;
  product_matched?: string;
  role: string;
}

export async function sendChatMessage(message: string, role: 'consumer' | 'agent' = 'consumer'): Promise<ChatResponse> {
  try {
    // Note: Endpoint might be /api/v1/chat or /api/v1/underwrite/chat depending on main.py prefix
    // Trying /api/v1/chat first based on @router.post("/chat") without extra prefix if included at root
    // But main.py likely prefixes it. Let's try /api/v1/chat
    const res = await fetch(`${API_URL}/chat?message=${encodeURIComponent(message)}&role=${role}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    
    // If 404, try /underwrite/chat
    if (res.status === 404) {
       const res2 = await fetch(`${API_URL}/underwrite/chat?message=${encodeURIComponent(message)}&role=${role}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!res2.ok) throw new Error('Chat API failed');
      return await res2.json();
    }

    if (!res.ok) throw new Error('Chat API failed');
    return await res.json();
  } catch (err) {
    console.error("Chat Error", err);
    return {
      message: "Sorry, I'm having trouble connecting to the brain. Please try again.",
      role: 'system'
    };
  }
}
