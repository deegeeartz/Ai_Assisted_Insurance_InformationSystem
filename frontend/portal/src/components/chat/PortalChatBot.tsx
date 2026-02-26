import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Bot, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { sendChatMessage, ChatAction } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { PortalChatActions } from './PortalChatActions';
import clsx from 'clsx';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  action?: string;
  data?: Record<string, any>;
  suggestions?: string[];
}

export function PortalChatBot() {
  const { user, token } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      text: user?.role === 'admin' 
        ? "Greetings, Superadmin. I'm your God-Mode assistant. I can fetch global metrics, manage tenants, or adjust configurations. How can I assist?"
        : "Hi! I'm your InsurBridge partner assistant. I can help with your dashboard, API keys, commissions, widget integration, and more. What do you need?",
      sender: 'bot',
      timestamp: new Date(),
      suggestions: user?.role === 'admin' 
        ? ['Show global dashboard', 'Show active tenants']
        : ['Show my dashboard', 'Generate a new API key', 'Show widget code'],
    }
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isOpen]);

  const handleSend = async (text?: string) => {
    const msgText = text || input.trim();
    if (!msgText) return;

    setMessages(prev => [...prev, { id: Date.now().toString(), text: msgText, sender: 'user', timestamp: new Date() }]);
    setInput('');
    setLoading(true);

    try {
      const response: ChatAction = await sendChatMessage(msgText, user?.role || 'partner', token || undefined);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        text: response.message,
        sender: 'bot',
        timestamp: new Date(),
        action: response.action,
        data: response.data,
        suggestions: response.suggestions,
      }]);
    } catch {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        text: "Something went wrong. Please try again.",
        sender: 'bot',
        timestamp: new Date(),
        suggestions: ['Show dashboard', 'Show API key'],
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <motion.button
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 rounded-full flex items-center justify-center text-white shadow-lg hover:bg-blue-700 transition-colors z-50"
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        {isOpen ? <X size={22} /> : <MessageCircle size={22} />}
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed bottom-24 right-6 w-[400px] h-[600px] bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="p-4 bg-blue-600 text-white flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center">
                <Bot size={18} />
              </div>
              <div>
                <h3 className="font-semibold text-sm">
                  {user?.role === 'admin' ? "InsurBridge God-Mode AI" : "InsurBridge Partner AI"}
                </h3>
                <p className="text-xs text-blue-200">
                  {user?.role === 'admin' ? "Global Metrics · Tenants · Config" : "Dashboard · API Keys · Commissions"}
                </p>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50">
              {messages.map((msg) => (
                <div key={msg.id}>
                  <div className={clsx("flex gap-2 max-w-[90%]", msg.sender === 'user' ? "ml-auto flex-row-reverse" : "")}>
                    <div className={clsx("w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs",
                      msg.sender === 'user' ? "bg-blue-100 text-blue-600" : "bg-slate-200 text-slate-600"
                    )}>
                      {msg.sender === 'user' ? <User size={13} /> : <Bot size={13} />}
                    </div>
                    <div className={clsx("p-3 rounded-2xl text-sm",
                      msg.sender === 'user'
                        ? "bg-blue-600 text-white rounded-tr-none"
                        : "bg-white border border-slate-200 text-slate-700 rounded-tl-none shadow-sm"
                    )}>
                      {msg.text}
                    </div>
                  </div>

                  {/* Action Data */}
                  {msg.action && msg.action !== 'text_reply' && msg.data && (
                    <div className="ml-9 mt-2">
                      <PortalChatActions 
                        action={msg.action} 
                        data={msg.data} 
                        onSuggestionClick={handleSend} 
                      />
                    </div>
                  )}

                  {/* Suggestions */}
                  {msg.sender === 'bot' && msg.suggestions && msg.suggestions.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2 ml-9">
                      {msg.suggestions.map((s, i) => (
                        <button key={i} onClick={() => handleSend(s)} className="text-[11px] px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-600 hover:bg-blue-100 transition-all">
                          {s}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="flex gap-2">
                  <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center"><Bot size={13} /></div>
                  <div className="bg-white border border-slate-200 p-3 rounded-2xl rounded-tl-none shadow-sm">
                    <div className="flex gap-1">
                      {[0, 0.1, 0.2].map((d, i) => (
                        <motion.div key={i} className="w-1.5 h-1.5 bg-blue-400 rounded-full" animate={{ y: [0, -4, 0] }} transition={{ repeat: Infinity, duration: 0.5, delay: d }} />
                      ))}
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-3 bg-white border-t border-slate-200">
              <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask about dashboard, API keys, commissions..."
                  className="flex-1 bg-slate-100 border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-400 outline-none"
                />
                <button type="submit" disabled={!input.trim() || loading} className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white hover:bg-blue-700 disabled:opacity-50 transition-colors">
                  <Send size={16} />
                </button>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
