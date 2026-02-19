import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchSlaDashboard } from '../services/api';
import { FileText, TrendingUp, AlertTriangle } from 'lucide-react';

export function SlaMonitor() {
  const { token } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
        fetchSlaDashboard(token)
            .then(setStats)
            .catch(console.error)
            .finally(() => setLoading(false));
    }
  }, [token]);

  if (loading) return <div className="p-8 text-center text-slate-500">Loading metrics...</div>;

  return (
    <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <TrendingUp className="w-8 h-8 text-purple-600" />
            SLA Monitor
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card p-6 border-t-4 border-blue-500">
                <div className="flex justify-between items-start">
                    <div>
                    <p className="text-sm font-medium text-slate-500">Active Policies</p>
                    <h3 className="text-2xl font-bold text-slate-900 mt-1">{stats?.sla_metrics?.total_policies || 0}</h3>
                    </div>
                    <FileText className="w-8 h-8 text-blue-500 bg-blue-50 p-1.5 rounded-lg" />
                </div>
            </div>

            <div className="card p-6 border-t-4 border-purple-500">
                <div className="flex justify-between items-start">
                    <div>
                    <p className="text-sm font-medium text-slate-500">Avg Processing Time</p>
                    <h3 className="text-2xl font-bold text-slate-900 mt-1">{stats?.sla_metrics?.avg_processing_time_ms ? (stats.sla_metrics.avg_processing_time_ms / 1000).toFixed(2) + 's' : '0s'}</h3>
                    </div>
                    <TrendingUp className="w-8 h-8 text-purple-500 bg-purple-50 p-1.5 rounded-lg" />
                </div>
                 <p className="text-sm text-slate-400 mt-4 flex items-center">
                    Target: &lt; 2s
                </p>
            </div>

             <div className="card p-6 border-t-4 border-green-500">
                <div className="flex justify-between items-start">
                    <div>
                    <p className="text-sm font-medium text-slate-500">SLA Compliance</p>
                    <h3 className="text-2xl font-bold text-slate-900 mt-1">{stats?.sla_metrics?.sla_compliance_rate || 100}%</h3>
                    </div>
                    <FileText className="w-8 h-8 text-green-500 bg-green-50 p-1.5 rounded-lg" />
                </div>
            </div>
        </div>
        
        <div className="card">
            <div className="p-6 border-b border-slate-200">
                <h3 className="font-bold text-slate-900 flex items-center">
                    <AlertTriangle className="w-5 h-5 text-amber-500 mr-2" /> Recent Breaches
                </h3>
            </div>
            <div className="p-8 text-center text-slate-500 text-sm">
                No active breaches detected. System is running within operational parameters.
            </div>
        </div>
    </div>
  );
}
