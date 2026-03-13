import { useState, useEffect } from 'react';
import { FileText, RefreshCw, CheckCircle, Clock, AlertCircle, CreditCard } from 'lucide-react';
import { motion } from 'framer-motion';
import { getMyPolicies, isLoggedIn, payForPolicy } from '../../services/api';

export function MyPolicies() {
  const [policies, setPolicies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState<string | null>(null);
  const [authRequired, setAuthRequired] = useState(false);

  const fetchPolicies = async () => {
    if (!isLoggedIn()) {
      setPolicies([]);
      setAuthRequired(true);
      setLoading(false);
      return;
    }

    setLoading(true);
    setAuthRequired(false);
    try {
      const data = await getMyPolicies();
      setPolicies(data || []);
    } catch (err) {
      console.error(err);
      setPolicies([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  const handlePay = async (policyNumber: string) => {
    setPaying(policyNumber);
    try {
      await payForPolicy(policyNumber);
      await fetchPolicies(); // Refresh
    } catch (err) {
      console.error(err);
    } finally {
      setPaying(null);
    }
  };

  const statusConfig: Record<string, { icon: any; color: string }> = {
    active: { icon: CheckCircle, color: 'green' },
    pending_payment: { icon: Clock, color: 'yellow' },
    lapsed: { icon: AlertCircle, color: 'red' },
  };

  return (
    <section id="my-policies" className="max-w-4xl mx-auto px-6 py-16">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white">My Policies</h2>
          <p className="text-white/40 text-sm">Your active and pending insurance policies</p>
        </div>
        <button
          onClick={fetchPolicies}
          aria-label="Refresh policies"
          title="Refresh policies"
          className="p-2 rounded-lg bg-white/5 border border-white/10 text-white/40 hover:text-white transition-colors"
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {loading && (
        <div className="text-center py-12 text-white/30">
          <RefreshCw size={24} className="mx-auto mb-3 animate-spin" />
          <p>Loading policies...</p>
        </div>
      )}

      {!loading && policies.length === 0 && (
        <div className="text-center py-12 bg-white/5 rounded-2xl border border-white/10">
          <FileText size={32} className="mx-auto text-white/20 mb-3" />
          {authRequired ? (
            <>
              <p className="text-white/40">Sign in to view your policy history.</p>
              <p className="text-white/20 text-sm mt-1">Your policies are now loaded from your authenticated account.</p>
            </>
          ) : (
            <>
              <p className="text-white/40">No policies yet.</p>
              <p className="text-white/20 text-sm mt-1">Use the chat assistant to get a quote and purchase a policy!</p>
            </>
          )}
        </div>
      )}

      <div className="grid gap-4">
        {policies.map((p: any, i: number) => {
          const cfg = statusConfig[p.status] || statusConfig.lapsed;
          const StatusIcon = cfg.icon;
          return (
            <motion.div
              key={p.policy_number}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-white/5 rounded-xl border border-white/10 p-5 flex items-center gap-4"
            >
              <div className={`w-12 h-12 rounded-xl bg-${cfg.color}-500/10 flex items-center justify-center`}>
                <StatusIcon size={20} className={`text-${cfg.color}-400`} />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-sm font-mono text-blue-400">{p.policy_number}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium bg-${cfg.color}-500/20 text-${cfg.color}-400`}>
                    {p.status?.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-white font-medium">{p.holder_name}</p>
                <p className="text-white/40 text-xs">{p.product_type} Insurance</p>
              </div>

              <div className="text-right">
                <p className="text-white font-bold">₦{(p.premium_annual || 0).toLocaleString()}</p>
                <p className="text-white/30 text-xs">per year</p>

                {p.status === 'pending_payment' && (
                  <button
                    onClick={() => handlePay(p.policy_number)}
                    disabled={paying === p.policy_number}
                    className="mt-2 text-xs px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-700 text-white transition-colors flex items-center gap-1 disabled:opacity-50"
                  >
                    <CreditCard size={12} />
                    {paying === p.policy_number ? 'Paying...' : 'Pay Now'}
                  </button>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}
