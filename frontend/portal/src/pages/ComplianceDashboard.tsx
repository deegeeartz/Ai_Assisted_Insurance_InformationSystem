import { useEffect, useState } from 'react';
import { fetchAuditLog, exportBatchCsv, registerWebhook } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, AlertTriangle, Search } from 'lucide-react';
import clsx from 'clsx';

export function ComplianceDashboard() {
  const { token } = useAuth();
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [webhookUrl, setWebhookUrl] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        if (token) {
          const data = await fetchAuditLog(token);
          setLogs(data);
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [token]);

  const handleExport = async () => {
    if (!token) return;
    try {
      const blob = await exportBatchCsv(token);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `compliance_export_${new Date().toISOString()}.csv`;
      a.click();
    } catch (e) {
      alert("Export failed");
    }
  };

  const handleSaveWebhook = async () => {
    if (!token || !webhookUrl) return;
    try {
      await registerWebhook(token, { event_type: "policy.created", url: webhookUrl, secret: webhookSecret });
      alert("Webhook registered successfully!");
      setWebhookUrl("");
      setWebhookSecret("");
    } catch (e) {
      alert("Failed to register webhook");
    }
  };

  return (
    <div className="space-y-6">
       <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-900">Compliance & Audit</h1>
        <div className="flex gap-3">
          <button 
            onClick={handleExport}
            className="btn bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-6 border-l-4 border-green-500">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-slate-500">System Status</p>
              <h3 className="text-xl font-bold text-slate-900 mt-1">Compliant</h3>
            </div>
            <ShieldCheck className="w-8 h-8 text-green-500" />
          </div>
          <p className="text-sm text-slate-400 mt-4">Last audit: 2 mins ago</p>
        </div>

        <div className="card p-6 border-l-4 border-yellow-500">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-slate-500">SLA Breaches</p>
              <h3 className="text-xl font-bold text-slate-900 mt-1">0 Active</h3>
            </div>
            <AlertTriangle className="w-8 h-8 text-yellow-500" />
          </div>
          <p className="text-sm text-slate-400 mt-4">Target: 99.9% uptime</p>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="card">
        <div className="p-4 border-b border-slate-200 flex justify-between items-center">
          <h3 className="font-semibold text-slate-900">Live Decision Feed</h3>
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input 
              placeholder="Search policy..." 
              className="pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:border-blue-500 outline-none"
            />
          </div>
        </div>
        
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <th className="px-6 py-3 font-medium">Timestamp</th>
              <th className="px-6 py-3 font-medium">Policy ID</th>
              <th className="px-6 py-3 font-medium">Product</th>
              <th className="px-6 py-3 font-medium">Decision</th>
              <th className="px-6 py-3 font-medium">Customer</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
             {loading && (
               <tr><td colSpan={5} className="px-6 py-8 text-center">Loading audit trail...</td></tr>
             )}
             {!loading && logs.length === 0 && (
               <tr><td colSpan={5} className="px-6 py-8 text-center text-slate-500">No records found.</td></tr>
             )}
             {logs.map((log, i) => (
               <tr key={i} className="hover:bg-slate-50">
                 <td className="px-6 py-3 text-slate-600 font-mono text-xs">
                   {new Date(log.timestamp).toISOString()}
                 </td>
                 <td className="px-6 py-3 font-medium text-slate-900">
                   {log.policy_number}
                 </td>
                 <td className="px-6 py-3">
                   <span className="px-2 py-1 rounded bg-slate-100 text-slate-600 text-xs font-semibold uppercase">
                     {log.product_type}
                   </span>
                 </td>
                 <td className="px-6 py-3">
                   <span className={clsx(
                     "px-2 py-1 rounded text-xs font-semibold uppercase",
                     log.status === 'active' ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                   )}>
                     {log.status === 'active' ? 'Approved' : log.status}
                   </span>
                 </td>
                 <td className="px-6 py-3 text-slate-600">
                   {log.customer_email}
                 </td>
               </tr>
             ))}
          </tbody>
        </table>
      </div>

      {/* Regulatory Handshake Config */}
      <div className="card p-6 border-t-4 border-slate-900">
        <h3 className="text-lg font-bold text-slate-900 mb-2">Regulatory Handshake (NAICOM)</h3>
        <p className="text-sm text-slate-500 mb-6">
          Configure real-time data push to the regulator's endpoint.
        </p>
        
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-slate-700 mb-1">Webhook Endpoint URL</label>
            <input 
              type="url" 
              value={webhookUrl}
              onChange={e => setWebhookUrl(e.target.value)}
              placeholder="https://api.naicom.gov.ng/v1/insurbridge-webhook"
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <div className="w-1/3">
             <label className="block text-sm font-medium text-slate-700 mb-1">Secret Key (HMAC)</label>
             <input 
               type="password" 
               value={webhookSecret}
               onChange={e => setWebhookSecret(e.target.value)}
               placeholder="••••••••••••••••"
               className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
             />
          </div>
          <button 
            onClick={handleSaveWebhook}
            className="btn btn-primary bg-slate-900 hover:bg-slate-800"
          >
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
}
