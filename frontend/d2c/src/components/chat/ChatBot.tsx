import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Bot, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { sendChatMessage, ChatAction } from '../../services/api';
import { ChatActions } from './ChatActions';
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

export function ChatBot() {
  const [isOpen, setIsOpen] = useState(false);
  const [role, setRole] = useState<'consumer' | 'agent' | 'partner'>('consumer');
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      text: "Hi! I'm InsurBridge AI — your full-service insurance assistant. I can help you browse products, get quotes, purchase policies, and more. What would you like to do?",
      sender: 'bot',
      timestamp: new Date(),
      suggestions: ['Show me your products', 'I need life insurance', 'Get me a quote'],
    }
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  const handleSend = async (text?: string) => {
    const msgText = text || input.trim();
    if (!msgText) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      text: msgText,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      // Prepare history (excluding the very first welcome message if desired, or keep it)
      const history = messages.map(m => ({
        role: m.sender === 'user' ? 'user' : 'model',
        content: m.text
      })) as { role: 'user' | 'model'; content: string }[];

      const response: ChatAction = await sendChatMessage(msgText, role, history);

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: response.message,
        sender: 'bot',
        timestamp: new Date(),
        action: response.action,
        data: response.data,
        suggestions: response.suggestions,
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        text: "Sorry, something went wrong. Please try again.",
        sender: 'bot',
        timestamp: new Date(),
        suggestions: ['Show products', 'Get a quote'],
      }]);
    } finally {
      setLoading(false);
    }
  };

  const roleLabels: Record<string, string> = {
    consumer: '👤 Customer',
    agent: '🏢 Agent',
    partner: '🤝 Partner',
  };

  const roleOrder: ('consumer' | 'agent' | 'partner')[] = ['consumer', 'agent', 'partner'];

  return (
    <>
      {/* Floating Toggle Button */}
      <motion.button
        layoutId="chat-button"
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 rounded-full flex items-center justify-center text-white shadow-lg hover:bg-blue-700 transition-colors z-50"
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        {isOpen ? <X /> : <MessageCircle />}
      </motion.button>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed bottom-24 right-6 w-[420px] h-[650px] bg-gray-900 rounded-2xl shadow-2xl border border-white/10 flex flex-col z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="p-4 bg-gray-800 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400">
                  <Bot size={20} />
                </div>
                <div>
                  <h3 className="font-semibold text-white">InsurBridge AI</h3>
                  <p className="text-xs text-white/40 flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    Agentic Assistant
                  </p>
                </div>
              </div>

              {/* Role Toggle */}
              <button
                onClick={() => {
                  const idx = roleOrder.indexOf(role);
                  setRole(roleOrder[(idx + 1) % roleOrder.length]);
                }}
                className="text-xs px-2 py-1 rounded bg-white/5 border border-white/10 text-white/60 hover:text-white transition-colors"
                title="Switch Role"
              >
                {roleLabels[role]}
              </button>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg) => (
                <div key={msg.id}>
                  <div
                    className={clsx(
                      "flex gap-3 max-w-[90%]",
                      msg.sender === 'user' ? "ml-auto flex-row-reverse" : ""
                    )}
                  >
                    <div className={clsx(
                      "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                      msg.sender === 'user' ? "bg-purple-500/20 text-purple-400" : "bg-blue-500/20 text-blue-400"
                    )}>
                      {msg.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
                    </div>

                    <div className="flex flex-col gap-1 min-w-0">
                      <div className={clsx(
                        "p-3 rounded-2xl text-sm leading-relaxed",
                        msg.sender === 'user'
                          ? "bg-purple-500/10 text-purple-100 rounded-tr-none border border-purple-500/20"
                          : "bg-blue-500/10 text-blue-100 rounded-tl-none border border-blue-500/20"
                      )}>
                        {msg.text}
                      </div>

                      {/* Action Cards */}
                      {msg.action && msg.data && (
                        <ChatActions
                          action={msg.action}
                          data={msg.data}
                          onSuggestionClick={(text) => handleSend(text)}
                        />
                      )}
                    </div>
                  </div>

                  {/* Suggestion Chips */}
                  {msg.sender === 'bot' && msg.suggestions && msg.suggestions.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2 ml-11">
                      {msg.suggestions.map((s, i) => (
                        <button
                          key={i}
                          onClick={() => handleSend(s)}
                          className="text-[11px] px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 hover:bg-blue-500/20 hover:border-blue-500/40 transition-all"
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center shrink-0">
                    <Bot size={14} />
                  </div>
                  <div className="bg-blue-500/10 p-4 rounded-2xl rounded-tl-none border border-blue-500/20">
                    <div className="flex gap-1">
                      <motion.div className="w-2 h-2 bg-blue-400 rounded-full" animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.5, delay: 0 }} />
                      <motion.div className="w-2 h-2 bg-blue-400 rounded-full" animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.5, delay: 0.1 }} />
                      <motion.div className="w-2 h-2 bg-blue-400 rounded-full" animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.5, delay: 0.2 }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-gray-800 border-t border-white/10">
              <form
                onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                className="flex gap-2"
              >
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={role === 'partner' ? "Ask about dashboard, API keys, commissions..." : "Ask about insurance, get quotes, buy policies..."}
                  className="flex-1 bg-black/20 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/30 focus:border-blue-500 outline-none transition-colors text-sm"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || loading}
                  className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Send size={18} />
                </button>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
