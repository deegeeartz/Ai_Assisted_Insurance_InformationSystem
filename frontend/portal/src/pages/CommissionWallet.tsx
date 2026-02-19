import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchPartnerDashboard } from '../services/api';
import { DollarSign, CreditCard, ArrowRight } from 'lucide-react';

export function CommissionWallet() {
  const { token } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
        fetchPartnerDashboard(token)
            .then(setData)
            .catch(console.error)
            .finally(() => setLoading(false));
    }
  }, [token]);

  if (loading) return <div className="p-8 text-center text-slate-500">Loading wallet...</div>;

  const balance = data?.metrics?.total_commission_earned || 0;

  return (
    <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Commission Wallet</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card p-8 bg-gradient-to-br from-slate-900 to-slate-800 text-white border-0">
                <p className="text-slate-400 font-medium mb-1">Total Balance</p>
                <h2 className="text-4xl font-bold mb-6">₦{balance.toLocaleString()}</h2>
                
                <div className="flex gap-4">
                    <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2">
                        <CreditCard className="w-4 h-4" /> Withdraw
                    </button>
                    <button className="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2 px-4 rounded-lg font-medium transition-colors">
                        History
                    </button>
                </div>
            </div>

            <div className="card p-6">
                <h3 className="font-bold text-slate-900 mb-4">Payout Settings</h3>
                <div className="space-y-4">
                    <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-white border border-slate-200 rounded-full flex items-center justify-center">
                                <span className="font-bold text-slate-700">GT</span>
                            </div>
                            <div>
                                <p className="font-medium text-slate-900">GTBank •••• 4281</p>
                                <p className="text-xs text-slate-500">Primary Payout Method</p>
                            </div>
                        </div>
                        <button className="text-blue-600 text-sm font-medium">Edit</button>
                    </div>
                    
                     <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-white border border-slate-200 rounded-full flex items-center justify-center">
                                <DollarSign className="w-5 h-5 text-green-600" />
                            </div>
                            <div>
                                <p className="font-medium text-slate-900">Auto-Withdraw</p>
                                <p className="text-xs text-slate-500">Trigger at ₦100,000</p>
                            </div>
                        </div>
                         <div className="relative inline-block w-10 mr-2 align-middle select-none transition duration-200 ease-in">
                            <input type="checkbox" name="toggle" id="toggle" className="toggle-checkbox absolute block w-5 h-5 rounded-full bg-white border-4 appearance-none cursor-pointer checked:right-0 checked:border-green-400"/>
                            <label htmlFor="toggle" className="toggle-label block overflow-hidden h-5 rounded-full bg-gray-300 cursor-pointer checked:bg-green-400"></label>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div className="card">
            <div className="p-6 border-b border-slate-200 flex justify-between items-center">
                <h3 className="text-lg font-bold text-slate-900">Recent Earnings</h3>
                <button className="text-blue-600 text-sm font-medium flex items-center hover:underline">
                    View All <ArrowRight className="w-4 h-4 ml-1" />
                </button>
            </div>
            <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-500">
                    <tr>
                        <th className="px-6 py-3">Date</th>
                        <th className="px-6 py-3">Source (Policy #)</th>
                        <th className="px-6 py-3 text-right">Amount</th>
                        <th className="px-6 py-3 text-right">Status</th>
                    </tr>
                </thead>
               <tbody className="divide-y divide-slate-200">
                  {data?.recent_transactions?.map((tx: any, i: number) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="px-6 py-4 text-slate-600">
                        {new Date(tx.date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 font-medium text-slate-900">
                        {tx.policy_id}
                      </td>
                      <td className="px-6 py-4 text-right text-green-600 font-bold">
                        +₦{tx.commission.toLocaleString()}
                      </td>
                       <td className="px-6 py-4 text-right">
                        <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">Settled</span>
                      </td>
                    </tr>
                  ))}
                   {(!data?.recent_transactions || data.recent_transactions.length === 0) && (
                        <tr><td colSpan={4} className="p-6 text-center text-slate-500">No earnings yet.</td></tr>
                   )}
                </tbody>
            </table>
        </div>
    </div>
  );
}
