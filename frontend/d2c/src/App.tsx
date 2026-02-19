import { useState } from 'react';
import { Header } from './components/layout/Header';
import { Hero } from './components/layout/Hero';
import { PolicyBuilder } from './components/policy/PolicyBuilder';
import { MyPolicies } from './components/policy/MyPolicies';
import { ChatBot } from './components/chat/ChatBot';
import { AuthModal } from './components/auth/AuthModal';
import { isLoggedIn, logout } from './services/api';

function App() {
  const [showAuth, setShowAuth] = useState(false);
  const [loggedIn, setLoggedIn] = useState(isLoggedIn());
  const [showPolicies, setShowPolicies] = useState(false);

  return (
    <div className="min-h-screen selection:bg-blue-500/30">
      <Header
        onAuthClick={() => setShowAuth(true)}
        onPoliciesClick={() => setShowPolicies(!showPolicies)}
        isLoggedIn={loggedIn}
        onLogout={() => { logout(); setLoggedIn(false); }}
      />
      <main>
        <Hero />
        <PolicyBuilder />
        {showPolicies && <MyPolicies />}
      </main>

      <ChatBot />

      <AuthModal
        isOpen={showAuth}
        onClose={() => setShowAuth(false)}
        onSuccess={() => setLoggedIn(true)}
      />

      <footer className="py-8 text-center text-white/30 text-sm">
        <p>© 2026 InsurBridge AI. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;
