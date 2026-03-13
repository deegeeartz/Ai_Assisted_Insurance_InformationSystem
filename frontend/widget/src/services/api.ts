const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface ChatResponse {
  message: string;
  product_matched?: string;
  role: string;
}

export async function sendChatMessage(message: string, role: 'consumer' | 'agent' = 'consumer'): Promise<ChatResponse> {
  try {
    const res = await fetch(`${API_URL}/chat?message=${encodeURIComponent(message)}&role=${role}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    
    // Fallback for different endpoint structure if needed
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
      message: "Sorry, I'm having trouble connecting to the InsurBridge brain. Please make sure the backend is running!",
      role: 'system'
    };
  }
}
