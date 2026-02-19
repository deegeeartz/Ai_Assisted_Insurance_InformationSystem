import { useState, useEffect } from 'react';
import { IntegrationCenter } from '../components/partner/IntegrationCenter';
import { fetchPartnerDashboard, rotateApiKey } from '../services/api';
import { useAuth } from '../context/AuthContext';

export function ApiKeys() {
  const { token } = useAuth();
  const [apiKey, setApiKey] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [rotating, setRotating] = useState(false);

  useEffect(() => {
    const loadKey = async () => {
      if (!token) return;
      try {
        const res = await fetchPartnerDashboard(token);
        setApiKey(res.api_key);
      } catch (err) {
        console.error("Failed to fetch API key", err);
      } finally {
        setLoading(false);
      }
    };
    loadKey();
  }, [token]);

  const handleRotateKey = async () => {
    if (!token || !confirm('Are you sure? Old key will stop working immediately.')) return;
    setRotating(true);
    try {
      const res = await rotateApiKey(token);
      setApiKey(res.api_key);
    } finally {
      setRotating(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading API details...</div>;

  return (
    <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Integration Settings</h1>
        <IntegrationCenter apiKey={apiKey} onRotate={handleRotateKey} rotating={rotating} />
    </div>
  );
}
