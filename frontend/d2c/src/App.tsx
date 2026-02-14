import { Header } from './components/layout/Header';
import { Hero } from './components/layout/Hero';
import { PolicyBuilder } from './components/policy/PolicyBuilder';
import { ChatBot } from './components/chat/ChatBot';

function App() {
  return (
    <div className="min-h-screen selection:bg-blue-500/30">
      <Header />
      <main>
        <Hero />
        <PolicyBuilder />
      </main>
      
      <ChatBot />
      
      <footer className="py-8 text-center text-white/30 text-sm">
        <p>© 2026 InsurBridge AI. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;
