import { useState, useEffect } from 'react';
import { CoverageSelector } from './CoverageSelector';
import { calculatePremium, getProducts, PolicyState, CoverageBlock, submitUnderwriting, payForPolicy, getProductSchema } from '../../services/api';
import { Loader2, ArrowRight, FileDown } from 'lucide-react';

export function PolicyBuilder() {
  const [products, setProducts] = useState<CoverageBlock[]>([]);
  const [state, setState] = useState<PolicyState>({
    holderName: '',
    holderEmail: '',
    age: 30,
    gender: 'female',
    occupation: 'tech',
    selectedCoverage: ['life_basic'],
    estimatedPremium: 0
  });

  const [loading, setLoading] = useState(false);
  const [processingStep, setProcessingStep] = useState<'idle' | 'underwriting' | 'paying' | 'success'>('idle');
  const [policyResult, setPolicyResult] = useState<any>(null);
  const [paymentResult, setPaymentResult] = useState<any>(null);
  const [schema, setSchema] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState('');

  // Fetch products on mount
  useEffect(() => {
    getProducts().then(setProducts);

    // Listen for ChatBot product selection
    const handleProductSelect = (e: any) => {
        const productType = e.detail; // e.g., "Life", "Gadget"
        console.log("ChatBot triggered selection:", productType);
        
        // Map simplified type string to coverage ID
        // In a real app, this mapping would be more robust/dynamic
        let coverageId = '';
        if (productType.includes('Life')) coverageId = 'life_basic';
        else if (productType.includes('Gadget')) coverageId = 'gadget_prot'; // Assuming ID exists or similar
        else if (productType.includes('Auto')) coverageId = 'auto_basic';

        if (coverageId) {
            setState(s => ({ ...s, selectedCoverage: [coverageId] }));
            // Optional: Scroll to builder
            document.getElementById('policy-builder')?.scrollIntoView({ behavior: 'smooth' });
        }
    };

    window.addEventListener('insurbridge:product-selected', handleProductSelect);
    return () => window.removeEventListener('insurbridge:product-selected', handleProductSelect);
  }, []);

  // Recalculate premium on change
  useEffect(() => {
    const updatePremium = async () => {
      setLoading(true);
      const premium = await calculatePremium(state);
      setState(s => ({ ...s, estimatedPremium: premium }));
      setLoading(false);
    };
    const timer = setTimeout(updatePremium, 500);
    return () => clearTimeout(timer);
  }, [state.selectedCoverage, state.age, state.gender, state.occupation]);

  // Fetch dynamic schema when coverage changes
  useEffect(() => {
    if (state.selectedCoverage.length > 0 && products.length > 0) {
      // Derive product type from the last selected product
      const lastId = state.selectedCoverage[state.selectedCoverage.length - 1];
      const selectedProduct = products.find(p => p.id === lastId) || products.find(p => state.selectedCoverage.includes(p.id));
      const pt = selectedProduct?.category || 'life';
      
      getProductSchema(pt).then(setSchema).catch(console.error);
    } else {
      setSchema(null);
    }
  }, [state.selectedCoverage, products]);

  const handleCategorySelect = (category: string) => {
    const matchingProduct = products.find(p => (p.category || 'life') === category);
    if (matchingProduct) {
      setState(s => ({
        ...s,
        selectedCoverage: [matchingProduct.id],
        dynamicFields: {}
      }));
    }
  };

  const toggleCoverage = (id: string) => {
    setState(prev => {
      // Single policy purchase mode: selecting an item replaces current selection
      const isAlreadySelected = prev.selectedCoverage.length === 1 && prev.selectedCoverage[0] === id;
      return { 
        ...prev, 
        selectedCoverage: isAlreadySelected ? [] : [id], 
        dynamicFields: {} 
      };
    });
  };

  const handlePayment = async () => {
    setErrorMessage('');

    if (state.selectedCoverage.length === 0) {
      setErrorMessage('Please select an insurance policy before proceeding to payment.');
      return;
    }

    if (!state.holderName || !state.holderName.trim()) {
      setErrorMessage('Required KYC Missing: Please enter your Full Name.');
      return;
    }

    if (!state.holderEmail || !state.holderEmail.trim() || !state.holderEmail.includes('@')) {
      setErrorMessage('Required KYC Missing: Please enter a valid Email Address.');
      return;
    }

    if (!state.age || state.age < 18) {
      setErrorMessage('Please enter a valid age (minimum 18 years old).');
      return;
    }

    // Require all product-specific dynamic fields to be filled before purchase
    if (schema?.product_specific_fields) {
      const requiredKeys = Object.keys(schema.product_specific_fields);
      const missingKeys = requiredKeys.filter(k => !state.dynamicFields?.[k] || !String(state.dynamicFields[k]).trim());
      
      if (missingKeys.length > 0) {
        const formatted = missingKeys.map(k => k.replace(/_/g, ' ')).join(', ');
        setErrorMessage(`Required Entry Missing: Please fill in ${formatted} before completing purchase.`);
        return;
      }
    }

    setProcessingStep('underwriting');
    try {
        // 1. Get Underwriting Decision
        const decision = await submitUnderwriting(state);
        setPolicyResult(decision);

        if (decision.status !== 'approved') {
            setErrorMessage(`Application Status: ${decision.status.toUpperCase()} - ${decision.reason}`);
            setProcessingStep('idle');
            return;
        }

        // 2. Process Real Payment
        setProcessingStep('paying');
        const payment = await payForPolicy(decision.policy_number || "PENDING");
        setPaymentResult(payment);
        
        // 3. Success
        setProcessingStep('success');

    } catch (err: any) {
        console.error(err);
        setErrorMessage("Payment Failed: " + err.message);
        setProcessingStep('idle');
    }
  };

  if (processingStep === 'success') {
      const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
      const downloadUrl = `${apiBase}/documents/key-facts/${policyResult?.policy_number}?format=pdf`;

      return (
          <div className="py-20 container mx-auto px-6 text-center">
              <div className="bg-white/10 p-12 rounded-3xl backdrop-blur-md max-w-2xl mx-auto border border-white/20">
                  <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg shadow-green-500/30">
                      <ArrowRight className="w-10 h-10 text-white rotate-45" /> {/* Reuse Check icon logic if available */}
                  </div>
                  <h2 className="text-4xl font-bold text-white mb-4">Policy Issued!</h2>
                  <p className="text-blue-100 text-xl mb-8">{policyResult?.plain_english_summary}</p>
                  
                  <div className="bg-white/5 p-6 rounded-xl text-left space-y-3 mb-8">
                      <div className="flex justify-between text-white/80">
                          <span>Policy Number</span>
                          <span className="font-mono font-bold text-white">{policyResult?.policy_number}</span>
                      </div>
                      <div className="flex justify-between text-white/80">
                        <span>Gateway</span>
                        <span className="font-bold text-white">{paymentResult?.gateway_name || 'Paystack (Simulated)'}</span>
                      </div>
                      <div className="flex justify-between text-white/80">
                        <span>Reference</span>
                        <span className="font-mono text-xs font-bold text-white">{paymentResult?.gateway_reference}</span>
                      </div>
                      <div className="flex justify-between text-white/80">
                          <span>Monthly Premium</span>
                          <span className="font-bold text-white">₦{policyResult?.premium_monthly?.toLocaleString()}</span>
                      </div>
                  </div>

                  <div className="flex flex-col gap-4">
                    <a 
                        href={downloadUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="btn bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-full font-bold transition-all flex items-center justify-center gap-2"
                    >
                        <FileDown className="w-5 h-5" /> Download Key Facts Document
                    </a>

                    {paymentResult?.authorization_url && (
                      <a
                        href={paymentResult.authorization_url}
                        target="_blank"
                        rel="noreferrer"
                        className="btn bg-green-600/80 hover:bg-green-700 text-white px-8 py-3 rounded-full font-bold transition-all"
                      >
                        View Simulated Checkout
                      </a>
                    )}
                    
                    <button 
                        onClick={() => window.location.reload()}
                        className="btn bg-white/10 hover:bg-white/20 text-white px-8 py-3 rounded-full font-bold transition-all"
                    >
                        Back to Home
                    </button>
                  </div>
              </div>
          </div>
      )
  }

  return (
    <section id="policy-builder" className="py-20 relative">
      <div className="container mx-auto px-6">
        <div className="flex flex-col lg:flex-row gap-12">
          
          {/* Left: Input & Selection */}
          <div className="flex-1 space-y-8">
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">Build Your Protection</h2>
              <p className="text-white/60">Customize your coverage blocks like lego.</p>
            </div>

            {/* Basic KYC Inputs */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-6 space-y-4">
              <h3 className="text-white font-semibold">Policyholder KYC Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm text-white/60 mb-2 flex items-center justify-between">
                    <span>Full Name</span>
                    <span className="text-red-400 text-xs font-semibold">Required *</span>
                  </label>
                  <input 
                    type="text" 
                    placeholder="e.g. Jane Doe"
                    value={state.holderName || ''}
                    onChange={(e) => setState(s => ({ ...s, holderName: e.target.value }))}
                    className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-blue-500 outline-none transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-sm text-white/60 mb-2 flex items-center justify-between">
                    <span>Email Address</span>
                    <span className="text-red-400 text-xs font-semibold">Required *</span>
                  </label>
                  <input 
                    type="email" 
                    placeholder="e.g. jane.doe@example.com"
                    value={state.holderEmail || ''}
                    onChange={(e) => setState(s => ({ ...s, holderEmail: e.target.value }))}
                    className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-blue-500 outline-none transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-sm text-white/60 mb-2 flex items-center justify-between">
                    <span>Your Age</span>
                    <span className="text-red-400 text-xs font-semibold">Required *</span>
                  </label>
                  <input 
                    type="number" 
                    aria-label="Your Age"
                    value={state.age}
                    onChange={(e) => setState(s => ({ ...s, age: parseInt(e.target.value) || 0 }))}
                    className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-blue-500 outline-none transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-sm text-white/60 mb-2">Gender</label>
                  <select 
                    aria-label="Gender"
                    className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-blue-500 outline-none transition-colors cursor-pointer"
                    value={state.gender}
                    onChange={(e) => setState(s => ({ ...s, gender: e.target.value }))}
                    style={{ backgroundColor: 'hsl(220 30% 12%)' }}
                  >
                    <option value="female">Female</option>
                    <option value="male">Male</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Dynamic Schema Inputs */}
            {schema && schema.product_specific_fields && Object.keys(schema.product_specific_fields).length > 0 && (
                <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                    <h3 className="text-white font-semibold mb-4 capitalize">{schema.product} Required Information</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {Object.entries(schema.product_specific_fields).map(([key, desc]: [string, any]) => (
                            <div key={key}>
                                <label className="block text-sm text-white/60 mb-2 capitalize flex items-center justify-between">
                                  <span>{key.replace(/_/g, ' ')}</span>
                                  <span className="text-red-400 text-xs font-semibold">Required *</span>
                                </label>
                                <input 
                                    type={desc.includes('integer') || desc.includes('number') ? 'number' : 'text'}
                                    placeholder={desc}
                                    value={state.dynamicFields?.[key] || ''}
                                    onChange={(e) => setState(s => ({ 
                                        ...s, 
                                        dynamicFields: { ...s.dynamicFields, [key]: e.target.value } 
                                    }))}
                                    className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-blue-500 outline-none transition-colors"
                                />
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <CoverageSelector 
              products={products}
              selectedIds={state.selectedCoverage}
              onToggle={toggleCoverage}
              onCategorySelect={handleCategorySelect}
            />
          </div>

          {/* Right: Summary Sticky Card */}
          <div className="lg:w-96">
            <div className="sticky top-24">
              <div className="card space-y-6">
                <h3 className="text-xl font-semibold text-white">Policy Summary</h3>
                
                <div className="space-y-4">
                  {state.selectedCoverage.length === 0 && (
                    <p className="text-white/40 text-sm italic">No coverage selected</p>
                  )}
                  {state.selectedCoverage.map(id => (
                    <div key={id} className="flex justify-between text-sm">
                      <span className="text-white/80 capitalize">{id.replace('_', ' ')}</span>
                      <span className="text-white/40">Included</span>
                    </div>
                  ))}
                  <div className="h-px bg-white/10 my-4" />
                  
                  <div className="flex justify-between items-end">
                    <span className="text-white/60">Total Monthly</span>
                    <div className="text-right">
                      {loading ? (
                        <Loader2 className="w-6 h-6 animate-spin text-blue-500 ml-auto" />
                      ) : (
                        <span className="text-3xl font-bold text-white tracking-tight">
                          ₦{state.estimatedPremium.toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <button 
                    onClick={handlePayment}
                    disabled={processingStep !== 'idle' || state.estimatedPremium === 0}
                    className="btn btn-primary w-full py-4 text-lg shadow-xl shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {processingStep === 'idle' && <>Proceed to Payment <ArrowRight className="w-5 h-5 ml-2" /></>}
                  {processingStep === 'underwriting' && <><Loader2 className="w-5 h-5 animate-spin mr-2" /> AI Underwriting...</>}
                  {processingStep === 'paying' && <><Loader2 className="w-5 h-5 animate-spin mr-2" /> Processing Payment...</>}
                </button>
                
                {errorMessage && (
                    <div className="bg-red-500/10 border border-red-500/20 text-red-500 p-4 rounded-xl text-sm font-medium animate-in fade-in slide-in-from-bottom-2">
                        {errorMessage}
                    </div>
                )}

                <p className="text-xs text-center text-white/30">
                  Includes AI-generated plain English policy document.
                </p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
