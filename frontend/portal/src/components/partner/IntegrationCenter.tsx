import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Copy, Code, Key } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface IntegrationCenterProps {
    apiKey?: string;
    onRotate?: () => void;
    rotating?: boolean;
}

export function IntegrationCenter({ apiKey, onRotate, rotating }: IntegrationCenterProps) {
  const { user } = useAuth();
  const [products, setProducts] = useState<any[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<string>('life_basic');
  const [schema, setSchema] = useState<any>(null);
  
  // Use real key from backend (via user context) or prop override
  const keyToDisplay = apiKey || user?.api_key || "Loading...";

  useEffect(() => {
    fetch(`${API_URL}/products`)
      .then(r => r.json())
      .then(data => {
          setProducts(data);
          if (data.length > 0 && !selectedProduct) setSelectedProduct(data[0].id);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
     if (selectedProduct) {
         fetch(`${API_URL}/products/${selectedProduct}/schema`)
         .then(r => r.json())
         .then(setSchema)
         .catch(console.error);
     }
  }, [selectedProduct]);

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

        {/* Server to Server APIs */}
        <div className="card p-6 border-l-4 border-indigo-500">
            <h3 className="text-lg font-bold text-slate-900 mb-4 flex flex-col md:flex-row md:items-center justify-between">
                <span className="flex items-center mb-2 md:mb-0"><Code className="w-5 h-5 mr-2" /> Dynamic Product APIs</span>
                <select 
                    className="text-sm border-slate-300 rounded-lg bg-slate-50 text-slate-700 shadow-sm px-3 py-1.5 focus:ring-indigo-500 focus:border-indigo-500"
                    value={selectedProduct}
                    onChange={(e) => setSelectedProduct(e.target.value)}
                >
                    {products.map(p => <option key={p.id} value={p.id}>{p.name} API</option>)}
                </select>
            </h3>
            <p className="text-sm text-slate-500 mb-6 flex justify-between items-center">
                <span>View exactly what fields are required to bind policies for this specific product.</span>
                {schema && <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded-full font-medium">Docs Auto-Generated via AI</span>}
            </p>
            
            {schema && (
            <div className="space-y-4">
                <div>
                    <h4 className="font-semibold text-sm mb-2 text-slate-800 flex items-center justify-between">
                        REST (JSON) Endpoint
                        <span className="text-xs font-normal text-slate-500">POST /api/v1/underwrite</span>
                    </h4>
                    <pre className="text-xs bg-slate-900 text-green-400 p-4 rounded-xl overflow-x-auto font-mono whitespace-pre-wrap shadow-inner border border-slate-800">
{`curl -X POST \${window.location.protocol}//\${window.location.hostname}:8000/api/v1/underwrite \\
  -H "X-Api-Key: \${keyToDisplay}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "age": 35,
    "product_type": "${schema.product}",
${Object.keys(schema.product_specific_fields).map(k => `    "${k}": "<${schema.product_specific_fields[k]}>"`).join(',\n')}${Object.keys(schema.product_specific_fields).length > 0 ? ',' : ''}
    "coverage_selection": [{"id": "${schema.product}"}]
  }'`}
                    </pre>
                </div>

                <div>
                    <h4 className="font-semibold text-sm mb-2 text-slate-800 flex items-center justify-between">
                        Enterprise SOAP (XML) Endpoint
                        <span className="text-xs font-normal text-slate-500">POST /api/v1/soap/underwrite</span>
                    </h4>
                    <pre className="text-xs bg-slate-900 text-purple-400 p-4 rounded-xl overflow-x-auto font-mono whitespace-pre-wrap shadow-inner border border-slate-800">
{`curl -X POST \${window.location.protocol}//\${window.location.hostname}:8000/api/v1/soap/underwrite \\
  -H "X-Api-Key: \${keyToDisplay}" \\
  -H "Content-Type: application/xml" \\
  -d '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <UnderwriteRequest>
      <age>35</age>
      <product_type>${schema.product}</product_type>
${Object.keys(schema.product_specific_fields).map(k => `      <${k}><![CDATA[${schema.product_specific_fields[k]}]]></${k}>`).join('\n')}
      <coverage_selection>
        <CoverageSelection>
          <id>${schema.product}</id>
        </CoverageSelection>
      </coverage_selection>
    </UnderwriteRequest>
  </soap:Body>
</soap:Envelope>'`}
                    </pre>
                </div>
            </div>
            )}
        </div>
    </div>
  );
}
