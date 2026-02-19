import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchSlaDashboard } from '../services/api';
import { FileText, TrendingUp } from 'lucide-react';
import { ProductManager } from '../components/admin/ProductManager';
import { PolicyConfig } from '../components/admin/PolicyConfig';

export function InsurerDashboard() {
  const { user, token } = useAuth();
  const [activeTab, setActiveTab] = useState<'overview' | 'products' | 'config'>('overview');
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    if (token) {
        fetchSlaDashboard(token)
            .then(setStats)
            .catch(console.error);
    }
  }, [token]);

  return (
    <div className="space-y-6">
       <div className="flex justify-between items-center">
        <div>
            <h1 className="text-2xl font-bold text-slate-900">Insurer Admin</h1>
            <p className="text-slate-500 text-sm">Welcome back, {user?.full_name}</p>
        </div>
        
        {/* Navigation Tabs */}
        <div className="flex bg-slate-100 p-1 rounded-lg">
            <button 
                onClick={() => setActiveTab('overview')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'overview' ? 'bg-white shadow text-slate-900' : 'text-slate-500 hover:text-slate-900'}`}
            >
                Overview
            </button>
            <button 
                onClick={() => setActiveTab('products')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'products' ? 'bg-white shadow text-slate-900' : 'text-slate-500 hover:text-slate-900'}`}
            >
                Product Manager
            </button>
            <button 
                onClick={() => setActiveTab('config')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'config' ? 'bg-white shadow text-slate-900' : 'text-slate-500 hover:text-slate-900'}`}
            >
                Configuration
            </button>
        </div>
      </div>

      {activeTab === 'overview' && (
        <>
            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="card p-6 border-t-4 border-blue-500">
                <div className="flex justify-between items-start">
                    <div>
                    <p className="text-sm font-medium text-slate-500">Active Policies</p>
                    <h3 className="text-2xl font-bold text-slate-900 mt-1">{stats?.sla_metrics?.total_policies || 0}</h3>
                    </div>
                    <FileText className="w-8 h-8 text-blue-500 bg-blue-50 p-1.5 rounded-lg" />
                </div>
                <p className="text-sm text-green-600 mt-4 flex items-center">
                    <TrendingUp className="w-4 h-4 mr-1" /> Live Data
                </p>
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
            
            {/* Disclaimer */}
            <div className="card p-6 text-center text-slate-500 mt-6 bg-slate-50 border-dashed border-2 border-slate-200">
                <p>Data is streamed in real-time from the {stats?.tenant || 'InsurBridge'} tenant.</p>
            </div>
        </>
      )}

      {activeTab === 'products' && <ProductManager />}
      {activeTab === 'config' && <PolicyConfig />}
    </div>
  );
}
