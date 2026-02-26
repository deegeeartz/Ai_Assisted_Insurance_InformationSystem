import { ShieldCheck, CheckCircle, Shield, Activity, Umbrella, Zap, FileText } from 'lucide-react';

interface PortalChatActionsProps {
  action: string;
  data: Record<string, any>;
  onSuggestionClick?: (text: string) => void;
}

const iconMap: Record<string, any> = {
  Heart: ShieldCheck, Activity, Zap, Umbrella, Shield
};

export function PortalChatActions({ action, data, onSuggestionClick }: PortalChatActionsProps) {

  if (action === 'text_reply') return null;

  // ---- SHOW DASHBOARD ----
  if (action === 'show_dashboard' && data.dashboard) {
    const d = data.dashboard;
    return (
      <div className="mt-2 grid grid-cols-2 gap-2">
        {[
          { label: 'Total Policies', value: d.total_policies, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-100' },
          { label: 'Active', value: d.active_policies, color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-100' },
          { label: 'Pending', value: d.pending_policies, color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-100' },
          { label: 'Premium Value', value: `₦${(d.total_premium_value || 0).toLocaleString()}`, color: 'text-purple-600', bg: 'bg-purple-50', border: 'border-purple-100' },
        ].map(m => (
          <div key={m.label} className={`p-2 rounded-lg ${m.bg} border ${m.border} text-center`}>
            <p className="text-[10px] text-slate-500 font-medium">{m.label}</p>
            <p className={`text-sm font-bold ${m.color}`}>{m.value}</p>
          </div>
        ))}
      </div>
    );
  }

  // ---- COMMISSIONS ----
  if (action === 'show_commissions' && data.commissions) {
    const c = data.commissions;
    return (
      <div className="mt-2 p-4 rounded-xl bg-gradient-to-br from-green-50 to-emerald-50 border border-green-100">
        <p className="text-xs text-green-700 font-medium mb-1">Total Earned Commissions</p>
        <p className="text-2xl font-bold text-green-700">₦{c.total_earned.toLocaleString()}</p>
        <button 
          onClick={() => onSuggestionClick?.('Withdraw my commissions')}
          className="mt-3 w-full py-2 bg-green-600 hover:bg-green-700 text-white text-xs font-semibold rounded-lg transition-colors"
        >
          Withdraw to Bank
        </button>
      </div>
    );
  }

  // ---- WITHDRAWAL ----
  if (action === 'withdraw_commission' && data.withdrawal) {
    return (
      <div className={`mt-2 p-3 rounded-xl border ${data.withdrawal.status === 'success' ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'} text-xs`}>
        {data.withdrawal.status === 'success' ? `✅ ${data.withdrawal.message}` : `❌ ${data.withdrawal.message}`}
      </div>
    );
  }

  // ---- API KEY ----
  if (action === 'rotate_api_key' && data.api_key_action) {
    return (
      <div className="mt-2 p-3 rounded-xl bg-orange-50 border border-orange-200">
        <p className="text-xs text-orange-800 whitespace-pre-wrap font-medium">{data.message}</p>
      </div>
    );
  }

  // ---- WIDGET CODE ----
  if (action === 'show_widget_code' && data.widget_code) {
    return (
      <div className="mt-2 rounded-xl bg-slate-900 p-3 border border-slate-700 relative group">
        <pre className="text-[10px] text-emerald-400 font-mono whitespace-pre-wrap overflow-x-auto">{data.widget_code}</pre>
        <button
          onClick={() => navigator.clipboard.writeText(data.widget_code)}
          className="absolute top-2 right-2 p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[10px] opacity-0 group-hover:opacity-100 transition-opacity"
        >
          Copy
        </button>
      </div>
    );
  }

  // ---- POLICIES ----
  if (action === 'show_policies' && data.policies) {
    if (data.policies.length === 0) {
      return (
        <div className="mt-2 p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
          <FileText size={20} className="mx-auto text-slate-400 mb-1" />
          <p className="text-xs text-slate-500">No policies found.</p>
        </div>
      );
    }
    return (
      <div className="mt-2 space-y-2">
        {data.policies.slice(0, 3).map((p: any) => (
          <div key={p.policy_number} className="p-3 rounded-xl bg-white border border-slate-200 shadow-sm">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-mono text-blue-600">{p.policy_number}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                p.status === 'active' ? 'bg-green-100 text-green-700' :
                p.status === 'pending_payment' ? 'bg-yellow-100 text-yellow-700' :
                'bg-slate-100 text-slate-700'
              }`}>{p.status.replace('_', ' ')}</span>
            </div>
            <p className="text-sm font-medium text-slate-800">{p.holder_name}</p>
            <p className="text-xs text-slate-500">{p.product_type} · ₦{(p.premium_annual || 0).toLocaleString()}/yr</p>
          </div>
        ))}
        {data.policies.length > 3 && (
          <p className="text-xs text-center text-slate-500 pt-1">...and {data.policies.length - 3} more</p>
        )}
      </div>
    );
  }

  // ---- QUOTE RESULT / PAYMENT ----
  if ((action === 'start_quote' && data.quote) || (action === 'initiate_payment' && data.payment)) {
    const q = data.quote || data.payment;
    const isApproved = q.status === 'approved' || q.status === 'pending_payment';
    
    return (
      <div className={`mt-2 rounded-xl border ${isApproved ? 'border-green-200 bg-green-50' : 'border-yellow-200 bg-yellow-50'} p-4`}>
        <div className="flex items-center gap-2 mb-3">
          <CheckCircle size={18} className={isApproved ? 'text-green-600' : 'text-yellow-600'} />
          <span className={`text-sm font-bold ${isApproved ? 'text-green-700' : 'text-yellow-700'} uppercase`}>
            {q.status.replace('_', ' ')}
          </span>
        </div>
        {(q.amount || q.premium_annual) && (
          <p className={`text-lg font-bold ${isApproved ? 'text-green-800' : 'text-yellow-800'} mb-2`}>
            ₦{(q.amount || q.premium_annual).toLocaleString()} / yr
          </p>
        )}
        {(q.summary || q.reason) && <p className="text-xs text-slate-600 mb-3">{q.summary || q.reason}</p>}
      </div>
    );
  }

  // ---- SHOW PRODUCTS ----
  if (action === 'show_products' && data.products) {
    return (
      <div className="mt-2 space-y-2">
        {data.products.map((p: any) => {
          const Icon = iconMap[p.icon] || Shield;
          return (
            <button
              key={p.id}
              onClick={() => onSuggestionClick?.(`Get me a quote for ${p.name}`)}
              className="w-full flex items-center gap-3 p-3 rounded-xl bg-white border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-all text-left"
            >
              <div className="w-9 h-9 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600 shrink-0">
                <Icon size={16} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-800">{p.name}</p>
                <p className="text-xs text-slate-500 truncate">{p.description}</p>
              </div>
            </button>
          );
        })}
      </div>
    );
  }

  return null;
}
