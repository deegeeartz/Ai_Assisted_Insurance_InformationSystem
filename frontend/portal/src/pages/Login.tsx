import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { login, fetchMe } from '../services/api';
import { useState } from 'react';
import { Lock } from 'lucide-react';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login: authLogin } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = await login(email, password);
      // Fetch full user details to get the role
      const user = await fetchMe(data.access_token);
      
      authLogin(data.access_token, user);
      navigate('/');
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-md bg-white p-8 rounded-xl shadow-lg border border-slate-200">
        <div className="flex justify-center mb-6">
          <div className="p-3 bg-blue-100 rounded-full">
            <Lock className="w-6 h-6 text-blue-600" />
          </div>
        </div>
        
        <h2 className="text-center text-2xl font-bold text-slate-900 mb-2">Portal Access</h2>
        <p className="text-center text-slate-500 mb-8">Sign in to manage your integration or compliance.</p>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
            <input 
              type="email" 
              required
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              value={email}
              onChange={e => setEmail(e.target.value)}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
            <input 
              type="password" 
              required
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              value={password}
              onChange={e => setPassword(e.target.value)}
            />
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full btn btn-primary py-2.5"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        
        <div className="mt-6 text-center text-xs text-slate-400">
          <p>Demo Credentials:</p>
          <p>partner@example.com / password</p>
          <p>compliance@example.com / password</p>
        </div>
      </div>
    </div>
  );
}
