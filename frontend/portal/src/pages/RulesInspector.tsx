import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchManuals, fetchRuleDetails } from '../services/api';
import { FileCode, Loader2, ChevronRight } from 'lucide-react';

export function RulesInspector() {
  const { token } = useAuth();
  const [manuals, setManuals] = useState<any[]>([]);
  const [selectedManual, setSelectedManual] = useState<any>(null);
  const [rules, setRules] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token) {
        fetchManuals(token).then(setManuals).catch(console.error);
    }
  }, [token]);

  const loadRules = async (manualId: number) => {
    setLoading(true);
    try {
        const data = await fetchRuleDetails(token!, manualId);
        setRules(JSON.parse(data.rules)); // Rules are stored as stringified JSON in DB
        setSelectedManual(manuals.find(m => m.id === manualId));
    } catch (e) {
        console.error(e);
        alert('Failed to load rules.');
    } finally {
        setLoading(false);
    }
  };

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col">
        <div className="mb-6">
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                <FileCode className="w-8 h-8 text-blue-600" /> 
                Rules Inspector
            </h1>
            <p className="text-slate-500">Visualize the probabilistic logic extracted by the AI Engine.</p>
        </div>

        <div className="flex-1 flex gap-6 min-h-0">
            {/* Sidebar List */}
            <div className="w-1/3 bg-white border border-slate-200 rounded-xl overflow-hidden flex flex-col">
                <div className="p-4 bg-slate-50 border-b border-slate-200 font-medium text-slate-700">
                    Ingested Manuals
                </div>
                <div className="overflow-y-auto flex-1 p-2 space-y-2">
                    {manuals.map(m => (
                        <button
                            key={m.id}
                            onClick={() => loadRules(m.id)}
                            className={`w-full text-left p-3 rounded-lg flex justify-between items-center transition-colors ${selectedManual?.id === m.id ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'hover:bg-slate-50 text-slate-600'}`}
                        >
                            <span className="truncate font-medium">{m.filename}</span>
                            <ChevronRight className={`w-4 h-4 ${selectedManual?.id === m.id ? 'text-blue-500' : 'text-slate-300'}`} />
                        </button>
                    ))}
                    {manuals.length === 0 && <div className="p-4 text-center text-slate-400 text-sm">No manuals found.</div>}
                </div>
            </div>

            {/* Main Viewer */}
            <div className="hidden visible sm:visible w-2/3 bg-slate-900 rounded-xl overflow-hidden flex flex-col relative">
                {loading && (
                    <div className="absolute inset-0 bg-slate-900/50 flex items-center justify-center z-10 backdrop-blur-sm">
                        <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
                    </div>
                )}
                
                <div className="p-4 bg-slate-800 border-b border-slate-700 flex justify-between items-center">
                    <span className="text-slate-300 font-mono text-sm">
                        {selectedManual ? `logic_tree_${selectedManual.product_type.toLowerCase()}.json` : 'Select a manual...'}
                    </span>
                    <span className="text-xs text-slate-500 uppercase tracking-wider">Read-Only</span>
                </div>
                
                <div className="flex-1 overflow-auto p-6">
                    {rules ? (
                        <pre className="text-green-400 font-mono text-sm leading-relaxed">
                            {JSON.stringify(rules, null, 2)}
                        </pre>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-slate-600">
                            <FileCode className="w-12 h-12 mb-4 opacity-50" />
                            <p>Select a manual to inspect its decision tree.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    </div>
  );
}
