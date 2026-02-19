import { useEffect, useState } from 'react';
import { fetchPartnerDashboard, rotateApiKey } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { DollarSign, FileCheck, TrendingUp } from 'lucide-react';
import { QuoteWizard } from '../components/partner/QuoteWizard';
import { IntegrationCenter } from '../components/partner/IntegrationCenter';

export function PartnerDashboard() {
  const { token } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [rotating, setRotating] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'quote' | 'integration'>('overview');

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
        <h1 className="text-2xl font-bold text-slate-900">Partner Portal</h1>
        
        {/* Navigation Tabs */}
        <div className="flex bg-slate-100 p-1 rounded-lg">
            <button 
                onClick={() => setActiveTab('overview')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'overview' ? 'bg-white shadow text-slate-900' : 'text-slate-500 hover:text-slate-900'}`}
            >
                Overview
            </button>
            <button 
                onClick={() => setActiveTab('quote')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'quote' ? 'bg-white shadow text-slate-900' : 'text-slate-500 hover:text-slate-900'}`}
            >
                New Quote
            </button>
            <button 
                onClick={() => setActiveTab('integration')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'integration' ? 'bg-white shadow text-slate-900' : 'text-slate-500 hover:text-slate-900'}`}
            >
                Integration
            </button>
        </div>
      </div>

      {activeTab === 'overview' && (
      <>
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
            <p className="text-2xl font-bold text-slate-900">42%</p>
          </div>
        </div>
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
      </>
      )}

      {activeTab === 'quote' && <QuoteWizard />}
      {activeTab === 'integration' && <IntegrationCenter apiKey={data?.api_key} onRotate={handleRotateKey} rotating={rotating} />}
    </div>
  );
}
