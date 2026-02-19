import { useAuth } from '../../context/AuthContext';
import { Copy, Code, Key } from 'lucide-react';

interface IntegrationCenterProps {
    apiKey?: string;
    onRotate?: () => void;
    rotating?: boolean;
}

export function IntegrationCenter({ apiKey, onRotate, rotating }: IntegrationCenterProps) {
  const { user } = useAuth();
  
  // Use real key from backend (via user context) or prop override
  const keyToDisplay = apiKey || user?.api_key || "Loading...";

  const widgetCode = `<div id="insurbridge-widget"></div>
<script src="https://cdn.insurbridge.ai/widget.js" 
        data-partner-id="${user?.email}" 
        data-key="${keyToDisplay}">
</script>`;

  return (
    <div className="space-y-6">
        <div className="card p-6 border-l-4 border-blue-500">
            <h3 className="text-lg font-bold text-slate-900 mb-2 flex items-center">
                <Key className="w-5 h-5 mr-2" /> Your API Key
            </h3>
            <p className="text-sm text-slate-500 mb-4">
                Use this key to authenticate API requests from your backend (`X-Api-Key` header).
            </p>
            
            <div className="bg-slate-900 rounded-lg p-4 flex justify-between items-center group">
                <code className="text-green-400 font-mono text-sm">{keyToDisplay}</code>
                <div className="flex gap-2">
                    <button 
                        className="text-slate-400 hover:text-white transition-colors"
                        onClick={() => navigator.clipboard.writeText(keyToDisplay)}
                        title="Copy API Key"
                    >
                        <Copy className="w-4 h-4" />
                    </button>
                    {onRotate && (
                        <button 
                            className={`text-slate-400 hover:text-red-400 transition-colors ${rotating ? 'animate-spin' : ''}`}
                            onClick={onRotate}
                            disabled={rotating}
                            title="Rotate API Key"
                        >
                            <Key className="w-4 h-4" /> 
                        </button>
                    )}
                </div>
            </div>
            {/* Helper for Curl */}
            <div className="mt-4 p-3 bg-slate-100 rounded text-xs font-mono text-slate-600 overflow-x-auto">
                curl -H "X-Api-Key: {keyToDisplay}" {window.location.protocol}//{window.location.hostname}:8000/api/v1/auth/me
            </div>
        </div>

        <div className="card p-6">
            <h3 className="text-lg font-bold text-slate-900 mb-2 flex items-center">
                <Code className="w-5 h-5 mr-2" /> Embeddable Widget
            </h3>
            <p className="text-sm text-slate-500 mb-4">
                Copy and paste this code into your website's &lt;body&gt; to instantly sell insurance.
            </p>
            
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 relative">
                <pre className="text-xs text-slate-600 overflow-x-auto font-mono">
                    {widgetCode}
                </pre>
                <button 
                    className="absolute top-4 right-4 text-slate-400 hover:text-blue-600"
                    onClick={() => navigator.clipboard.writeText(widgetCode)}
                >
                    <Copy className="w-4 h-4" />
                </button>
            </div>
        </div>
    </div>
  );
}
