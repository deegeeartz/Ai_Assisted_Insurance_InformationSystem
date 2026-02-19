import { Shield, ChevronRight, Menu } from 'lucide-react';
import { useState } from 'react';

export function Header() {
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

        <nav className="hidden md:flex items-center gap-8">
          <a href="#policy-builder" onClick={(e) => { e.preventDefault(); document.getElementById('policy-builder')?.scrollIntoView({ behavior: 'smooth' }); }} className="text-sm font-medium text-white/70 hover:text-white transition-colors">Products</a>
          <a href="#policy-builder" onClick={(e) => { e.preventDefault(); document.getElementById('policy-builder')?.scrollIntoView({ behavior: 'smooth' }); }} className="text-sm font-medium text-white/70 hover:text-white transition-colors">Claims</a>
          <a href="http://localhost:3002" target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-white/70 hover:text-white transition-colors">Partners</a>
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
