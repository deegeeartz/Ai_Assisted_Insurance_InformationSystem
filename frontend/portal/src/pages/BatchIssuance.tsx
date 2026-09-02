import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { UploadCloud, FileText, CheckCircle, AlertCircle } from 'lucide-react';

import { API_URL } from '../services/api';

export function BatchIssuance() {
  const { token } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState('');

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.name.endsWith('.csv')) {
      setFile(dropped);
      setError('');
    } else {
      setError('Please upload a valid .csv file.');
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    setResults(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_URL}/partners/batch-underwrite`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      if (!res.ok) {
        throw new Error(await res.text() || 'Upload failed');
      }

      const data = await res.json();
      setResults(data);
    } catch (err: any) {
      setError(err.message || 'An error occurred during upload.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Batch Issuance</h1>
        <p className="text-slate-500 text-sm">Upload a CSV to bulk-underwrite and bind policies instantly.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card p-6 lg:col-span-1 border-t-4 border-indigo-500">
          <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center">
            <UploadCloud className="w-5 h-5 mr-2 text-indigo-500" />
            Upload Client List
          </h3>

          <div 
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:bg-slate-50 transition-colors cursor-pointer"
          >
            <FileText className="w-12 h-12 text-slate-400 mx-auto mb-3" />
            <p className="text-sm font-medium text-slate-700">Drag and drop your CSV here</p>
            <p className="text-xs text-slate-500 mt-1">or click below to browse</p>
            
            <input 
              type="file" 
              accept=".csv" 
              id="csvUpload" 
              className="hidden" 
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f && f.name.endsWith('.csv')) {
                  setFile(f);
                  setError('');
                } else {
                  setError('Please select a valid .csv file.');
                }
              }}
            />
            <label 
              htmlFor="csvUpload" 
              className="mt-4 inline-block px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors"
            >
              Browse Files
            </label>
          </div>

          {file && (
            <div className="mt-4 p-3 bg-indigo-50 border border-indigo-100 rounded-lg flex justify-between items-center">
              <span className="text-sm font-medium text-indigo-900 truncate pr-4">{file.name}</span>
              <button 
                onClick={handleUpload}
                disabled={loading}
                className="px-4 py-1.5 bg-indigo-600 text-white text-xs font-semibold rounded hover:bg-indigo-700 disabled:opacity-50"
              >
                {loading ? 'Processing...' : 'Process Batch'}
              </button>
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 bg-red-50 text-red-600 rounded flex items-start text-sm">
              <AlertCircle className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
              {error}
            </div>
          )}
          
          <div className="mt-6 pt-6 border-t border-slate-100">
             <h4 className="text-sm font-medium text-slate-700 mb-2">CSV Requirements</h4>
             <ul className="text-xs text-slate-500 space-y-1 list-disc pl-4">
                 <li>Must include <code className="bg-slate-100 px-1 rounded">age</code>, <code className="bg-slate-100 px-1 rounded">product_type</code></li>
                 <li>Optional: <code className="bg-slate-100 px-1 rounded">holder_name</code>, <code className="bg-slate-100 px-1 rounded">holder_email</code></li>
                 <li>Use exact product types (e.g., <code className="bg-slate-100 px-1 rounded">life</code>, <code className="bg-slate-100 px-1 rounded">gadget</code>)</li>
             </ul>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
            {results ? (
                <>
                <div className="grid grid-cols-3 gap-4">
                    <div className="card p-4 border-l-4 border-blue-500">
                        <p className="text-xs text-slate-500 font-medium tracking-wider uppercase mb-1">Total Rows</p>
                        <p className="text-2xl font-bold text-slate-900">{results.total_rows}</p>
                    </div>
                    <div className="card p-4 border-l-4 border-green-500">
                        <p className="text-xs text-slate-500 font-medium tracking-wider uppercase mb-1">Bound Policies</p>
                        <p className="text-2xl font-bold text-green-600">{results.approved}</p>
                    </div>
                    <div className="card p-4 border-l-4 border-red-500">
                        <p className="text-xs text-slate-500 font-medium tracking-wider uppercase mb-1">Declined/Errors</p>
                        <p className="text-2xl font-bold text-red-500">{results.declined + results.failed}</p>
                    </div>
                </div>
                
                <div className="card p-6">
                    <h3 className="text-lg font-bold text-slate-900 mb-4">Execution Log</h3>
                    <div className="bg-slate-900 rounded-lg p-4 h-64 overflow-y-auto font-mono text-xs space-y-2">
                        {results.logs.map((log: string, idx: number) => (
                            <div key={idx} className={
                                log.includes('Approved') ? 'text-green-400' :
                                log.includes('Declined') ? 'text-yellow-400' : 'text-red-400'
                            }>
                                &gt; {log}
                            </div>
                        ))}
                    </div>
                </div>
                </>
            ) : (
                <div className="card p-12 flex flex-col items-center justify-center text-slate-500 border-dashed border-2 border-slate-200 h-full">
                    <CheckCircle className="w-12 h-12 text-slate-300 mb-4" />
                    <p>Awaiting batch upload...</p>
                    <p className="text-sm mt-2 max-w-sm text-center">Process up to 1,000 policies simultaneously without writing a single line of API code.</p>
                </div>
            )}
        </div>

      </div>
    </div>
  );
}
