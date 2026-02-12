import { LayoutDashboard, Key, Wallet, FileText, Activity, LogOut, ShieldAlert } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import clsx from 'clsx';

export function Sidebar() {
  const { user, logout } = useAuth();
  
  const partnerLinks = [
    { icon: LayoutDashboard, label: 'Overview', to: '/' },
    { icon: Key, label: 'API Keys', to: '/api-keys' },
    { icon: Wallet, label: 'Wallet', to: '/wallet' },
  ];

  const complianceLinks = [
    { icon: Activity, label: 'Audit Log', to: '/' },
    { icon: ShieldAlert, label: 'SLA Monitor', to: '/sla' },
    { icon: FileText, label: 'Rules Inspector', to: '/rules' },
  ];

  const links = user?.role === 'partner' ? partnerLinks : complianceLinks;

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-slate-900 text-white flex flex-col">
      <div className="p-6 border-b border-slate-800">
        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
          InsurBridge
        </h1>
        <p className="text-xs text-slate-500 mt-1 uppercase tracking-wider">
          {user?.role === 'partner' ? 'Partner Portal' : 'Compliance'}
        </p>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) => clsx(
              "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors",
              isActive 
                ? "bg-blue-600 text-white" 
                : "text-slate-400 hover:text-white hover:bg-slate-800"
            )}
          >
            <link.icon className="w-5 h-5" />
            {link.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3 px-4 py-3 mb-2">
          <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div className="overflow-hidden">
            <p className="text-sm font-medium truncate">{user?.full_name}</p>
            <p className="text-xs text-slate-500 truncate">{user?.email}</p>
          </div>
        </div>
        
        <button 
          onClick={logout}
          className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
