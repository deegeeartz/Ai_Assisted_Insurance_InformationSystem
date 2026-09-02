import { Heart, Activity, Zap, Umbrella, CheckCircle, AlertCircle, Clock, CreditCard, FileText, Shield } from 'lucide-react';
import { payForPolicy } from '../../services/api';
import { useState } from 'react';

interface ChatActionsProps {
  action: string;
  data: Record<string, any>;
  onSuggestionClick?: (text: string) => void;
}

const iconMap: Record<string, any> = {
  Heart, Activity, Zap, Umbrella, Shield
};

export function ChatActions({ action, data, onSuggestionClick }: ChatActionsProps) {
  const [paying, setPaying] = useState(false);
  const [payResult, setPayResult] = useState<any>(null);

  if (action === 'text_reply') return null;

  // ---- SHOW PRODUCTS ----
  if (action === 'show_products' && data.products) {
    return (
      <div className="mt-2 space-y-2">
        {data.products.map((p: any) => {
          const Icon = iconMap[p.icon] || Shield;
          return (
            <button
              key={p.id}
              onClick={() => onSuggestionClick?.(`Tell me more about ${p.name}`)}
              className="w-full flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/10 hover:border-blue-500/40 transition-all text-left group"
            >
              <div className="w-9 h-9 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400 shrink-0">
                <Icon size={16} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white">{p.name}</p>
                <p className="text-xs text-white/40 truncate">{p.description}</p>
              </div>
              <span className="text-xs text-blue-400 font-mono">₦{p.base_price?.toLocaleString()}/yr</span>
            </button>
          );
        })}
      </div>
    );
  }

  // ---- QUOTE RESULT ----
  if (action === 'start_quote' && data.quote) {
    const q = data.quote;
    const isApproved = q.status === 'approved';
    const StatusIcon = isApproved ? CheckCircle : q.status === 'declined' ? AlertCircle : Clock;
    const statusColor = isApproved ? 'green' : q.status === 'declined' ? 'red' : 'yellow';

    return (
      <div className={`mt-2 rounded-xl border border-${statusColor}-500/30 bg-${statusColor}-500/5 p-4`}>
        <div className="flex items-center gap-2 mb-3">
          <StatusIcon size={18} className={`text-${statusColor}-400`} />
          <span className={`text-sm font-bold text-${statusColor}-400 uppercase`}>{q.status}</span>
          {q.product_type && (
            <span className="text-xs bg-white/10 px-2 py-0.5 rounded-full text-white/60">{q.product_type}</span>
          )}
        </div>

        {q.premium_monthly && (
          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="bg-black/20 rounded-lg p-2 text-center">
              <p className="text-xs text-white/40">Monthly</p>
              <p className="text-lg font-bold text-white">₦{q.premium_monthly?.toLocaleString()}</p>
            </div>
            <div className="bg-black/20 rounded-lg p-2 text-center">
              <p className="text-xs text-white/40">Annual</p>
              <p className="text-lg font-bold text-white">₦{q.premium_annual?.toLocaleString()}</p>
            </div>
          </div>
        )}

        <p className="text-xs text-white/60 mb-3">{q.summary || q.reason}</p>

        {isApproved && q.policy_number && !payResult && (
          <button
            onClick={async () => {
              setPaying(true);
              try {
                const result = await payForPolicy(q.policy_number);
                setPayResult(result);
              } catch (e: any) {
                setPayResult({ status: 'error', message: e.message });
              } finally {
                setPaying(false);
              }
            }}
            disabled={paying}
            className="w-full py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <CreditCard size={14} />
            {paying ? 'Processing...' : `Pay ₦${(q.premium_annual || 0).toLocaleString()} (Simulated)`}
          </button>
        )}

        {payResult && (
          <div className={`mt-2 p-2 rounded-lg text-xs ${payResult.status === 'success' ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}>
            {payResult.status === 'success' ? (
              <>
                <p>✅ {payResult.message} Ref: {payResult.gateway_reference}</p>
                <a
                  href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/documents/key-facts/${q.policy_number}?format=pdf${q.key_facts_token ? `&token=${q.key_facts_token}` : ''}`}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 flex items-center justify-center gap-1.5 py-1.5 bg-green-600/50 hover:bg-green-600 rounded text-white font-medium transition-colors"
                >
                  <FileText size={14} /> Download Policy Certificate
                </a>
              </>
            ) : (
              <>❌ {payResult.message}</>
            )}
          </div>
        )}
      </div>
    );
  }

  // ---- SHOW POLICIES ----
  if (action === 'show_policies' && data.policies) {
    if (data.policies.length === 0) {
      return (
        <div className="mt-2 p-3 rounded-xl bg-white/5 border border-white/10 text-center">
          <FileText size={20} className="mx-auto text-white/30 mb-1" />
          <p className="text-xs text-white/40">No policies found.</p>
        </div>
      );
    }
    return (
      <div className="mt-2 space-y-2">
        {data.policies.map((p: any) => (
          <div key={p.policy_number} className="p-3 rounded-xl bg-white/5 border border-white/10">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-mono text-blue-400">{p.policy_number}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                p.status === 'active' ? 'bg-green-500/20 text-green-400' :
                p.status === 'pending_payment' ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-gray-500/20 text-gray-400'
              }`}>{p.status}</span>
            </div>
            <p className="text-sm text-white">{p.holder_name}</p>
            <p className="text-xs text-white/40">{p.product_type} · ₦{(p.premium_annual || 0).toLocaleString()}/yr</p>
            {p.status === 'pending_payment' && (
              <button
                onClick={() => onSuggestionClick?.(`Pay for policy ${p.policy_number}`)}
                className="mt-2 text-xs text-blue-400 hover:text-blue-300"
              >
                → Pay now
              </button>
            )}
          </div>
        ))}
      </div>
    );
  }

  // ---- INITIATE PAYMENT ----
  if (action === 'initiate_payment' && data.payment) {
    const pm = data.payment;
    return (
      <div className="mt-2 rounded-xl border border-blue-500/30 bg-blue-500/5 p-4">
        <div className="flex items-center gap-2 mb-2">
          <CreditCard size={16} className="text-blue-400" />
          <span className="text-sm font-medium text-white">Payment for {pm.policy_number}</span>
        </div>
        <p className="text-lg font-bold text-white mb-2">₦{pm.amount?.toLocaleString()} {pm.currency}</p>
        {!payResult ? (
          <button
            onClick={async () => {
              setPaying(true);
              try {
                const result = await payForPolicy(pm.policy_number);
                setPayResult(result);
              } catch (e: any) {
                setPayResult({ status: 'error', message: e.message });
              } finally {
                setPaying(false);
              }
            }}
            disabled={paying}
            className="w-full py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors disabled:opacity-50"
          >
            {paying ? 'Processing...' : 'Confirm Payment (Simulated)'}
          </button>
        ) : (
          <div className={`p-2 rounded-lg text-xs ${payResult.status === 'success' ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}>
            {payResult.status === 'success' ? (
              <>
                <p>✅ {payResult.message}</p>
                <a
                  href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/documents/key-facts/${pm.policy_number}?format=pdf${pm.key_facts_token ? `&token=${pm.key_facts_token}` : ''}`}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 flex items-center justify-center gap-1.5 py-1.5 bg-green-600/50 hover:bg-green-600 rounded text-white font-medium transition-colors"
                >
                  <FileText size={14} /> Download Policy Certificate
                </a>
              </>
            ) : (
              <>❌ {payResult.message}</>
            )}
          </div>
        )}
      </div>
    );
  }

  // ---- DASHBOARD (for partner mode) ----
  if (action === 'show_dashboard' && data.dashboard) {
    const d = data.dashboard;
    return (
      <div className="mt-2 grid grid-cols-2 gap-2">
        {[
          { label: 'Total Policies', value: d.total_policies, color: 'blue' },
          { label: 'Active', value: d.active_policies, color: 'green' },
          { label: 'Pending', value: d.pending_policies, color: 'yellow' },
          { label: 'Premium Value', value: `₦${(d.total_premium_value || 0).toLocaleString()}`, color: 'purple' },
        ].map(m => (
          <div key={m.label} className={`p-2 rounded-lg bg-${m.color}-500/10 border border-${m.color}-500/20 text-center`}>
            <p className="text-[10px] text-white/40">{m.label}</p>
            <p className="text-sm font-bold text-white">{m.value}</p>
          </div>
        ))}
      </div>
    );
  }

  // ---- WIDGET CODE ----
  if (action === 'show_widget_code' && data.widget_code) {
    return (
      <div className="mt-2 rounded-xl bg-black/40 p-3 border border-white/10">
        <pre className="text-[10px] text-green-400 font-mono whitespace-pre-wrap overflow-x-auto">{data.widget_code}</pre>
        <button
          onClick={() => navigator.clipboard.writeText(data.widget_code)}
          className="mt-2 text-xs text-blue-400 hover:text-blue-300"
        >
          📋 Copy to clipboard
        </button>
      </div>
    );
  }

  return null;
}
