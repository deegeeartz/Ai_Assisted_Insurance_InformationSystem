import { useState, useEffect } from 'react';
import { Heart, Activity, Zap, Umbrella, Check, Plus, Car, Shield, Home, Smartphone, Monitor, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { CoverageBlock } from '../../services/api';
import clsx from 'clsx';

// Icon mapping
const ICON_MAP: Record<string, any> = {
  Heart, Activity, Zap, Umbrella, Car, Shield, Home, Smartphone, Monitor, Clock
};

// Insurer brand colors (rendered as tiny badges on the cards now)
const INSURER_COLORS: Record<string, { accent: string; bg: string; border: string; badge: string }> = {
  "Heirs Life Assurance":   { accent: "text-rose-400",    bg: "bg-rose-500/10",    border: "border-rose-500/30", badge: "bg-rose-500/20 text-rose-300" },
  "Heirs General Insurance": { accent: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/30", badge: "bg-emerald-500/20 text-emerald-300" },
  "Heirs Gadget Insurance":  { accent: "text-violet-400",  bg: "bg-violet-500/10",  border: "border-violet-500/30", badge: "bg-violet-500/20 text-violet-300" },
};

const DEFAULT_COLORS = { accent: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/30", badge: "bg-blue-500/20 text-blue-300" };

interface Props {
  products: CoverageBlock[];
  selectedIds: string[];
  onToggle: (id: string) => void;
}

export function CoverageSelector({ products, selectedIds, onToggle }: Props) {
  // Extract unique categories (e.g. 'life', 'auto', 'gadget', 'home')
  const categories = Array.from(new Set(products.map(p => p.category || 'life')));
  
  // Extract unique insurers for the filter dropdown
  const insurers = Array.from(new Set(products.map(p => p.insurerName || 'Other'))).sort();
  
  const [activeCategory, setActiveCategory] = useState<string>('life');
  const [activeInsurer, setActiveInsurer] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'price_asc' | 'price_desc' | 'name'>('price_asc');

  // Initialize active tab to the first available category if 'life' isn't present
  useEffect(() => {
    if (categories.length > 0 && !categories.includes(activeCategory)) {
      setActiveCategory(categories[0]);
    }
  }, [categories, activeCategory]);

  // 1. Filter by Category
  let activeProducts = products.filter(p => (p.category || 'life') === activeCategory);
  
  // 2. Filter by Insurer
  if (activeInsurer !== 'all') {
    activeProducts = activeProducts.filter(p => (p.insurerName || 'Other') === activeInsurer);
  }

  // 3. Sort
  activeProducts.sort((a, b) => {
    if (sortBy === 'price_asc') return a.basePrice - b.basePrice;
    if (sortBy === 'price_desc') return b.basePrice - a.basePrice;
    return a.name.localeCompare(b.name);
  });

  return (
    <div className="space-y-6">
      {/* Top Bar: Tabs + Filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-4">
        {/* Category Tab Bar */}
        <div className="flex items-center gap-2 overflow-x-auto scrollbar-none">
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={clsx(
              "px-5 py-2.5 rounded-xl text-sm font-medium capitalize whitespace-nowrap transition-all duration-200",
              activeCategory === cat
                ? "bg-blue-600 text-white shadow-lg shadow-blue-500/25"
                : "bg-white/5 text-white/50 hover:bg-white/10 hover:text-white"
            )}
          >
            {cat} Insurance
          </button>
        ))}
        </div>

        {/* Filters & Sort */}
        <div className="flex items-center gap-3 shrink-0">
          <select 
            value={activeInsurer}
            onChange={(e) => setActiveInsurer(e.target.value)}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white/80 outline-none focus:border-blue-500 cursor-pointer"
            style={{ backgroundColor: 'hsl(220 30% 12%)' }}
          >
            <option value="all">All Insurers</option>
            {insurers.map(i => <option key={i} value={i}>{i}</option>)}
          </select>

          <select 
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white/80 outline-none focus:border-blue-500 cursor-pointer"
            style={{ backgroundColor: 'hsl(220 30% 12%)' }}
          >
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
            <option value="name">Name: A-Z</option>
          </select>
        </div>
      </div>

      {/* Product Cards Grid */}
      {activeProducts.length === 0 ? (
        <div className="py-12 text-center bg-white/5 rounded-2xl border border-white/10 border-dashed">
          <Shield className="w-12 h-12 text-white/20 mx-auto mb-4" />
          <h3 className="text-white font-medium mb-1">No products found</h3>
          <p className="text-white/40 text-sm">Try adjusting your insurer filter or selecting a different category.</p>
          <button 
            onClick={() => setActiveInsurer('all')}
            className="mt-4 px-4 py-2 bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 rounded-lg text-sm font-medium transition-colors"
          >
            Clear Filters
          </button>
        </div>
      ) : (
        <motion.div layout className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <AnimatePresence mode="popLayout">
          {activeProducts.map((block) => {
            const isSelected = selectedIds.includes(block.id);
            const Icon = ICON_MAP[block.icon] || Heart;
            const colors = INSURER_COLORS[block.insurerName || 'Other'] || DEFAULT_COLORS;

            return (
              <motion.div
                key={block.id}
                layout
                initial={{ opacity: 0, scale: 0.95, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -10 }}
                transition={{ duration: 0.2 }}
                onClick={() => onToggle(block.id)}
                className={clsx(
                  "relative group cursor-pointer p-5 rounded-xl border transition-all duration-300 flex flex-col h-full",
                  isSelected
                    ? `bg-blue-500/10 border-blue-500/50 shadow-[0_0_20px_rgba(59,130,246,0.15)]`
                    : "bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20"
                )}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={clsx(
                      "w-10 h-10 rounded-lg flex items-center justify-center transition-colors shrink-0",
                      isSelected ? "bg-blue-500 text-white" : `${colors.bg} ${colors.accent}`
                    )}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className={clsx("font-semibold text-sm line-clamp-1", isSelected ? "text-white" : "text-white/80")}>
                        {block.name}
                      </h3>
                      <span className={clsx("text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full mt-1 inline-block", colors.badge)}>
                        {block.insurerName}
                      </span>
                    </div>
                  </div>

                  <div className={clsx(
                    "w-7 h-7 rounded-full flex items-center justify-center border transition-all shrink-0 ml-2",
                    isSelected
                      ? "bg-blue-500 border-blue-500 text-white"
                      : "border-white/20 text-white/20 group-hover:border-white/40"
                  )}>
                    {isSelected ? <Check className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                  </div>
                </div>

                <p className="text-xs text-white/40 leading-relaxed flex-1">{block.description}</p>

                {/* Price Tag */}
                <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between text-xs">
                  <span className="text-white/30">From</span>
                  <span className={clsx("font-mono font-medium", isSelected ? "text-blue-300" : "text-white/60")}>
                    ₦{block.basePrice.toLocaleString()}/mo
                  </span>
                </div>

                {/* Active Glow Border */}
                {isSelected && (
                  <motion.div
                    layoutId={`outline-${block.id}`}
                    className="absolute inset-0 rounded-xl border-2 border-blue-500 pointer-events-none"
                    initial={false}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  />
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>
        </motion.div>
      )}
    </div>
  );
}
