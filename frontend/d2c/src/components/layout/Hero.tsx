import { ArrowRight, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';
import { motion } from 'framer-motion';

export function Hero() {
  return (
    <section className="relative pt-32 pb-20 overflow-hidden">
      {/* Background Glows */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-[128px] pointer-events-none" 
           style={{ background: 'radial-gradient(circle, hsl(var(--color-primary-hue) var(--color-primary-sat) 50% / 0.2), transparent 70%)' }} />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-[128px] pointer-events-none"
           style={{ background: 'radial-gradient(circle, hsl(var(--color-accent-hue) var(--color-accent-sat) 50% / 0.2), transparent 70%)' }} />

      <div className="container mx-auto px-6 relative z-10">
        <div className="text-center max-w-4xl mx-auto space-y-8">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-sm"
          >
            <span className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_10px_theme(colors.green.400)] animate-pulse" />
            <span className="text-sm font-medium text-white/80">AI-Powered Coverage • Instant Approval</span>
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl md:text-7xl font-bold tracking-tight leading-tight"
          >
            Insurance that <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              Adapts to You
            </span>
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-xl text-white/60 max-w-2xl mx-auto leading-relaxed"
          >
            Build your perfect policy with AI. Select only the coverage blocks you need, understand every detail in plain English, and get protected in minutes.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
          >
            <button className="btn btn-primary text-lg px-8 py-4 w-full sm:w-auto group">
              Design My Policy
              <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
            </button>
            <button className="btn btn-secondary text-lg px-8 py-4 w-full sm:w-auto">
              View Demo
            </button>
          </motion.div>

          {/* Trust Indicators */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.5 }}
            className="pt-12 grid grid-cols-1 md:grid-cols-3 gap-6 text-left"
          >
            {[
              { icon: Zap, title: "Instant", desc: "AI Underwriting in < 60s" },
              { icon: ShieldCheck, title: "Secure", desc: "Bank-grade encryption" },
              { icon: CheckCircle2, title: "Clear", desc: "No hidden clauses" },
            ].map((item, i) => (
              <div key={i} className="flex items-start gap-4 p-4 rounded-xl border border-white/5 bg-white/5 backdrop-blur-sm">
                <item.icon className="w-8 h-8 text-blue-400 shrink-0" style={{ color: 'hsl(var(--color-primary-hue) 80% 60%)' }} />
                <div>
                  <h3 className="text-lg font-semibold text-white">{item.title}</h3>
                  <p className="text-sm text-white/50">{item.desc}</p>
                </div>
              </div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
}
