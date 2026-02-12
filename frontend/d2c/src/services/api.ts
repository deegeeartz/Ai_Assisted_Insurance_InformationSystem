export interface CoverageBlock {
    id: string;
    name: string;
    description: string;
    basePrice: number;
    icon: string; // Lucide icon name
  }
  
  export interface PolicyState {
    age: number;
    gender: string;
    occupation: string;
    selectedCoverage: string[]; // IDs
    estimatedPremium: number;
  }
  
  // Mock Data for "Lego Blocks"
  export const AVAILABLE_COVERAGE: CoverageBlock[] = [
    {
      id: "life_basic",
      name: "Life Protection",
      description: "Lump sum payout to your beneficiaries.",
      basePrice: 5000,
      icon: "Heart"
    },
    {
      id: "critical_illness",
      name: "Critical Illness",
      description: "Coverage for cancer, stroke, and heart attack.",
      basePrice: 3000,
      icon: "Activity"
    },
    {
      id: "accidental_death",
      name: "Accidental Death",
      description: "Double payout for accidental passing.",
      basePrice: 1500,
      icon: "Zap"
    },
    {
      id: "funeral_cover",
      name: "Funeral Expenses",
      description: "Immediate cash for funeral costs.",
      basePrice: 1000,
      icon: "Umbrella"
    }
  ];
  
  export async function calculatePremium(state: PolicyState): Promise<number> {
    // Simulate API call to backend
    await new Promise(resolve => setTimeout(resolve, 600));
    
    let total = 0;
    AVAILABLE_COVERAGE.forEach(block => {
      if (state.selectedCoverage.includes(block.id)) {
        total += block.basePrice;
      }
    });
    
    // Simple age loading
    const ageLoad = state.age > 30 ? (state.age - 30) * 100 : 0;
    return total + ageLoad;
  }
