import { useState, useEffect } from 'react';
import { CoverageSelector } from './CoverageSelector';
import { calculatePremium, PolicyState } from '../../services/api';
import { motion } from 'framer-motion';
import { Loader2, ArrowRight } from 'lucide-react';

export function PolicyBuilder() {
  const [state, setState] = useState<PolicyState>({
    age: 30,
    gender: 'female',
    occupation: 'tech',
    selectedCoverage: ['life_basic'],
    estimatedPremium: 0
  });

  const [loading, setLoading] = useState(false);

  // Recalculate premium on change
  useEffect(() => {
    const updatePremium = async () => {
      setLoading(true);
      const premium = await calculatePremium(state);
      setState(s => ({ ...s, estimatedPremium: premium }));
      setLoading(false);
    };
    updatePremium();
  }, [state.selectedCoverage, state.age]);

  const toggleCoverage = (id: string) => {
    setState(prev => {
      const exists = prev.selectedCoverage.includes(id);
      const newCoverage = exists 
        ? prev.selectedCoverage.filter(c => c !== id)
        : [...prev.selectedCoverage, id];
      return { ...prev, selectedCoverage: newCoverage };
    });
  };

  return (
    <section className="py-20 bg-black/20" id="builder">
      <div className="container mx-auto px-6">
        <div className="flex flex-col lg:flex-row gap-12">
          
          {/* Left: Input & Selection */}
          <div className="flex-1 space-y-8">
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">Build Your Protection</h2>
              <p className="text-white/60">Customize your coverage blocks like lego.</p>
            </div>

            {/* Basic Inputs (Simplified for Proto) */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-6 grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm text-white/60 mb-2">Your Age</label>
                <input 
                  type="number" 
                  value={state.age}
                  onChange={(e) => setState(s => ({ ...s, age: parseInt(e.target.value) || 0 }))}
                  className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-blue-500 outline-none transition-colors"
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Gender</label>
                <select 
                  className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-blue-500 outline-none transition-colors"
                  value={state.gender}
                  onChange={(e) => setState(s => ({ ...s, gender: e.target.value }))}
                >
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                </select>
              </div>
            </div>

            <CoverageSelector 
              selectedIds={state.selectedCoverage}
              onToggle={toggleCoverage}
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

                <button className="btn btn-primary w-full py-4 text-lg shadow-xl shadow-blue-500/20">
                  Proceed to Payment
                  <ArrowRight className="w-5 h-5 ml-2" />
                </button>
                
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
