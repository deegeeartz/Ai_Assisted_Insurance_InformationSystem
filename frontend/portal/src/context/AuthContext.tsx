import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { fetchMe } from '../services/api';

interface User {
  email: string;
  role: 'partner' | 'compliance_officer' | 'admin' | 'insurer';
  full_name: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

  useEffect(() => {
    async function initAuth() {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          // Import fetchMe dynamically to avoid circular dependency if any, 
          // or ideally import at top level but this block is just replacing the effect.
          // We'll assume fetchMe is imported or available. 
          // Wait, I need to import it. 
          // For now, I'll just use the logic here or I should have added import in previous step.
          // Let's use the full replacement to include imports if needed, but for now I'll just use fetch in the effect or better, 
          // let's update the file imports in a separate step or assume I can't easily add import here without reading whole file.
          // Actually, I can use a separate step to add the import.
          // But I'll use the proper way: fetch directly here or rely on the service.
          // Let's rely on the service. I'll simply add the functionality.
          // But I need to import `fetchMe`. 
          // The previous tool call modify `api.ts` export `fetchMe`.
          // I will use `view_file` to see imports first?
          // No, I'll just assume I can add the import. 
          // Actually, I'll just replace the whole file content for safety in next step? 
          // No, that's too big.
          
          // I'll stick to the plan:
          // 1. Update api.ts (done)
          // 2. Update AuthContext.tsx (this step)
          // I'll assume I can add the import at the top.
          
          // Use fetchMe from services
          const userData = await fetchMe(storedToken);
          
          setUser(userData);
          setToken(storedToken);
        } catch (err) {
          logout();
        }
      }
    }
    
    initAuth();
  }, []);

  const login = (newToken: string, newUser: User) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setUser(newUser);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
