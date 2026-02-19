import { useState } from 'react';
import { Check, Loader2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { underwrite } from '../../services/api';

export function QuoteWizard() {
  const { token, user } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    product: 'Life', // Matches manual product_type
    age: 30,
    amount: 5000000,
    customerName: '',
    customerEmail: ''
  });
  const [quote, setQuote] = useState<any>(null);

  const calculate = async () => {
    if (!token) return;
    setLoading(true);
    try {
        const payload = {
            age: formData.age,
            product_type: formData.product,
            holder_name: formData.customerName || `Customer (${formData.age})`,
            holder_email: formData.customerEmail || "customer@example.com",
            natural_language_query: "I want to buy insurance",
            role: "consumer"
        };

        // Pass API Key to link policy to Partner!
        const decision = await underwrite(token, payload, user?.api_key);
        
        if (decision.status === 'approved') {
            setQuote(decision);
            setStep(2);
        } else {
            alert(`Quote Declined: ${decision.reason}`);
        }
    } catch (e) {
        console.error(e);
        alert('Error generating quote. Ensure backend is running.');
    } finally {
        setLoading(false);
    }
  };

  const bind = async () => {
    // Policy is already created in "pending_payment" status by the underwrite call!
    // In a real flow, we'd take payment here.
    // For MVP, we just show success.
    setStep(3);
  };

  return (
    <div className="max-w-2xl mx-auto">
        <div className="mb-8 flex justify-between items-center relative">
            <div className="absolute left-0 top-1/2 w-full h-1 bg-slate-200 -z-10" />
            {[1, 2, 3].map(i => (
                <div key={i} className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${step >= i ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-500'}`}>
                    {step > i ? <Check className="w-4 h-4" /> : i}
                </div>
            ))}
        </div>

        <div className="card p-8">
            {step === 1 && (
                <div className="space-y-6">
                    <h2 className="text-xl font-bold text-slate-900">New Quote</h2>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="label">Product</label>
                            <select 
                                className="input w-full p-2 border rounded" 
                                value={formData.product}
                                onChange={e => setFormData({...formData, product: e.target.value})}
                            >
                                <option value="Life">Life Protection</option>
                                <option value="Auto">Auto Insurance</option>
                                <option value="Gadget">Gadget Protection</option>
                            </select>
                        </div>
                        <div>
                            <label className="label">Customer Age</label>
                            <input 
                                type="number" 
                                className="input w-full p-2 border rounded"
                                value={formData.age}
                                onChange={e => setFormData({...formData, age: Number(e.target.value)})}
                            />
                        </div>
                        <div className="col-span-2">
                            <label className="label">Customer Name (Optional)</label>
                            <input 
                                type="text" 
                                placeholder="John Doe"
                                className="input w-full p-2 border rounded"
                                value={formData.customerName}
                                onChange={e => setFormData({...formData, customerName: e.target.value})}
                            />
                        </div>
                    </div>
                    <button 
                        className="btn btn-primary w-full flex justify-center items-center" 
                        onClick={calculate}
                        disabled={loading}
                    >
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Generate Quote'}
                    </button>
                </div>
            )}

            {step === 2 && quote && (
                <div className="space-y-6 text-center">
                    <h2 className="text-xl font-bold text-slate-900">Quote Approved</h2>
                    <p className="text-sm text-slate-500">Policy Reference: {quote.policy_number}</p>
                    
                    <div className="py-6 bg-slate-50 rounded-xl">
                        <p className="text-slate-500">Annual Premium</p>
                        <p className="text-4xl font-bold text-blue-600">₦{quote.premium_annual?.toLocaleString()}</p>
                        <p className="text-sm text-slate-400 mt-2">or ₦{quote.premium_monthly?.toLocaleString()}/mo</p>
                    </div>
                    
                    <div className="flex gap-4">
                        <button className="btn w-full border" onClick={() => setStep(1)}>Back</button>
                        <button className="btn btn-primary w-full" onClick={bind}>Bind & Collect Payment</button>
                    </div>
                </div>
            )}

            {step === 3 && (
                <div className="text-center py-12">
                    <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Check className="w-8 h-8" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900">Policy Issued!</h2>
                    <p className="text-slate-500 mt-2">Policy #{quote?.policy_number} has been bound to your account.</p>
                    <p className="text-xs text-slate-400 mt-1">Pending payment collection via Payment Link.</p>
                    <button className="btn btn-primary mt-8" onClick={() => setStep(1)}>
                        Create Another
                    </button>
                </div>
            )}
        </div>
    </div>
  );
}
