import { Heart, Activity, Zap, Umbrella, Check, Plus } from 'lucide-react';
import { motion } from 'framer-motion';
import { AVAILABLE_COVERAGE } from '../../services/api';
import clsx from 'clsx';

// Icon mapping
const ICON_MAP: Record<string, any> = {
  Heart, Activity, Zap, Umbrella
};

interface Props {
  selectedIds: string[];
  onToggle: (id: string) => void;
}

export function CoverageSelector({ selectedIds, onToggle }: Props) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
      {AVAILABLE_COVERAGE.map((block) => {
        const isSelected = selectedIds.includes(block.id);
        const Icon = ICON_MAP[block.icon] || Heart;

        return (
          <motion.div
            key={block.id}
            layout
            onClick={() => onToggle(block.id)}
            className={clsx(
              "relative group cursor-pointer p-6 rounded-xl border transition-all duration-300",
              isSelected 
                ? "bg-blue-500/10 border-blue-500/50 shadow-[0_0_20px_rgba(59,130,246,0.15)]" 
                : "bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20"
            )}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className={clsx(
                  "w-12 h-12 rounded-lg flex items-center justify-center transition-colors",
                  isSelected ? "bg-blue-500 text-white" : "bg-white/10 text-white/50"
                )}>
                  <Icon className="w-6 h-6" />
                </div>
                <div>
                  <h3 className={clsx("font-semibold text-lg", isSelected ? "text-white" : "text-white/80")}>
                    {block.name}
                  </h3>
                  <p className="text-sm text-white/50 leading-tight mt-1">{block.description}</p>
                </div>
              </div>

              <div className={clsx(
                "w-8 h-8 rounded-full flex items-center justify-center border transition-all",
                isSelected 
                  ? "bg-blue-500 border-blue-500 text-white" 
                  : "border-white/20 text-white/20 group-hover:border-white/40"
              )}>
                {isSelected ? <Check className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
              </div>
            </div>

            {/* Price Tag */}
            <div className="mt-4 flex items-center justify-between text-sm">
              <span className="text-white/40">Estimated cost</span>
              <span className={clsx("font-mono font-medium", isSelected ? "text-blue-300" : "text-white/60")}>
                ₦{block.basePrice.toLocaleString()}/mo
              </span>
            </div>
            
            {/* Active Glow Border */}
            {isSelected && (
              <motion.div
                layoutId="outline"
                className="absolute inset-0 rounded-xl border-2 border-blue-500 pointer-events-none"
                initial={false}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            )}
          </motion.div>
        );
      })}
    </div>
  );
}
