import { Shield, ChevronRight, Menu, LogIn, FileText, LogOut } from 'lucide-react';
import { useState } from 'react';

interface HeaderProps {
  onAuthClick?: () => void;
  onPoliciesClick?: () => void;
  isLoggedIn?: boolean;
  onLogout?: () => void;
}

export function Header({ onAuthClick, onPoliciesClick, isLoggedIn, onLogout }: HeaderProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 w-full z-50 bg-opacity-90 backdrop-blur-md border-b border-white/10" style={{ background: 'hsl(var(--bg-dark) / 0.8)' }}>
      <div className="container mx-auto px-6 h-20 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20"
               style={{ background: 'linear-gradient(135deg, hsl(var(--color-primary-hue) var(--color-primary-sat) 50%), hsl(var(--color-accent-hue) var(--color-accent-sat) 50%))' }}>
            <Shield className="text-white w-6 h-6" />
          </div>
          <span className="text-2xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70">
            InsurBridge
          </span>
        </div>

        <nav className="hidden md:flex items-center gap-6">
          <a href="#policy-builder" onClick={(e) => { e.preventDefault(); document.getElementById('policy-builder')?.scrollIntoView({ behavior: 'smooth' }); }} className="text-sm font-medium text-white/70 hover:text-white transition-colors">Products</a>
          <a href="http://localhost:3002" target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-white/70 hover:text-white transition-colors">Partners</a>

          {isLoggedIn && (
            <button onClick={onPoliciesClick} className="text-sm font-medium text-white/70 hover:text-white transition-colors flex items-center gap-1">
              <FileText size={14} /> My Policies
            </button>
          )}

          {isLoggedIn ? (
            <button onClick={onLogout} className="text-sm px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white/60 hover:text-white hover:border-white/30 transition-all flex items-center gap-1.5">
              <LogOut size={14} /> Sign Out
            </button>
          ) : (
            <button onClick={onAuthClick} className="text-sm px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white/60 hover:text-white hover:border-white/30 transition-all flex items-center gap-1.5">
              <LogIn size={14} /> Sign In
            </button>
          )}

          <button onClick={() => document.getElementById('policy-builder')?.scrollIntoView({ behavior: 'smooth' })} className="btn btn-primary text-sm px-6 py-2.5">
            Get Started <ChevronRight className="w-4 h-4 ml-1" />
          </button>
        </nav>

        <button className="md:hidden text-white" onClick={() => setIsMenuOpen(!isMenuOpen)}>
          <Menu className="w-6 h-6" />
        </button>
      </div>
    </header>
  );
}
