import { useEffect, useState } from 'react';
import { fetchPartnerDashboard, rotateApiKey } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Copy, RefreshCw, DollarSign, FileCheck, TrendingUp } from 'lucide-react';

export function PartnerDashboard() {
  const { token } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [rotating, setRotating] = useState(false);

  const loadData = async () => {
    try {
      if (token) {
        const res = await fetchPartnerDashboard(token);
        setData(res);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const handleRotateKey = async () => {
    if (!token || !confirm('Are you sure? Old key will stop working immediately.')) return;
    setRotating(true);
    try {
      const res = await rotateApiKey(token);
      setData((prev: any) => ({ ...prev, api_key: res.api_key }));
    } finally {
      setRotating(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading dashboard...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-900">Partner Overview</h1>
        <div className="flex gap-2">
          <button onClick={loadData} className="btn btn-secondary text-slate-600 bg-white border">
            <RefreshCw className="w-4 h-4 mr-2" /> Refresh
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-6 flex items-center gap-4">
          <div className="p-3 bg-blue-100 text-blue-600 rounded-full">
            <FileCheck className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm text-slate-500 font-medium">Policies Sold</p>
            <p className="text-2xl font-bold text-slate-900">{data?.metrics?.total_policies_sold}</p>
          </div>
        </div>

        <div className="card p-6 flex items-center gap-4">
          <div className="p-3 bg-green-100 text-green-600 rounded-full">
            <DollarSign className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm text-slate-500 font-medium">Commission Earned</p>
            <p className="text-2xl font-bold text-slate-900">
              ₦{data?.metrics?.total_commission_earned?.toLocaleString()}
            </p>
          </div>
        </div>

        <div className="card p-6 flex items-center gap-4">
          <div className="p-3 bg-purple-100 text-purple-600 rounded-full">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm text-slate-500 font-medium">Conversion Rate</p>
            <p className="text-2xl font-bold text-slate-900">--%</p>
          </div>
        </div>
      </div>

      {/* API Key Section */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">API Integration</h3>
        <div className="bg-slate-900 rounded-lg p-4 flex items-center justify-between">
          <code className="text-green-400 font-mono text-sm max-w-xl truncate">
            {data?.api_key || 'No API Key Generated'}
          </code>
          <div className="flex gap-2">
            <button 
              onClick={() => navigator.clipboard.writeText(data?.api_key)}
              className="p-2 text-slate-400 hover:text-white transition-colors"
              title="Copy"
            >
              <Copy className="w-4 h-4" />
            </button>
            <button 
              onClick={handleRotateKey}
              disabled={rotating}
              className="p-2 text-slate-400 hover:text-red-400 transition-colors"
              title="Rotate Key"
            >
              <RefreshCw className={`w-4 h-4 ${rotating ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
        <p className="text-xs text-slate-500 mt-2">
          Use this key in the <code>X-API-Key</code> header for all requests to the Headless API.
        </p>
      </div>

      {/* Recent Transactions */}
      <div className="card">
        <div className="p-6 border-b border-slate-200">
          <h3 className="text-lg font-semibold text-slate-900">Recent Transactions</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-6 py-3 font-medium">Date</th>
                <th className="px-6 py-3 font-medium">Policy #</th>
                <th className="px-6 py-3 font-medium text-right">Premium</th>
                <th className="px-6 py-3 font-medium text-right">Commission</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {data?.recent_transactions?.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                    No transactions found.
                  </td>
                </tr>
              )}
              {data?.recent_transactions?.map((tx: any, i: number) => (
                <tr key={i} className="hover:bg-slate-50">
                  <td className="px-6 py-4 text-slate-600">
                    {new Date(tx.date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 font-medium text-slate-900">
                    {tx.policy_id}
                  </td>
                  <td className="px-6 py-4 text-right text-slate-600">
                    ₦{tx.amount.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right text-green-600 font-medium">
                    +₦{tx.commission.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
