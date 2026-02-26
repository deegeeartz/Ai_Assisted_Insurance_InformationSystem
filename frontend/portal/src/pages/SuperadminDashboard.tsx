import React, { useState, useEffect } from 'react';
import { ShieldAlert, Globe, Activity, Users, Settings, Zap, DollarSign, Database, PowerOff } from 'lucide-react';
import { fetchGlobalMetrics, fetchTenants, toggleTenantStatus, fetchPlatformConfigs, updatePlatformConfig } from '../services/api';
import { useAuth } from '../context/AuthContext';

interface GlobalMetrics {
  gross_written_premium: number;
  total_active_policies: number;
  active_insurers: number;
  active_partners: number;
  total_consumers: number;
}

interface Tenant {
  id: number;
  company_name: string;
  tenant_id: string;
  email: string;
  is_active: boolean;
  total_policies: number;
}

interface PlatformConfig {
  key: string;
  value: string;
  description: string;
}

export const SuperadminDashboard: React.FC = () => {
  const { token } = useAuth();
  const [metrics, setMetrics] = useState<GlobalMetrics | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [configs, setConfigs] = useState<PlatformConfig[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    if (!token) return;
    try {
      const [m, t, c] = await Promise.all([
        fetchGlobalMetrics(token),
        fetchTenants(token),
        fetchPlatformConfigs(token)
      ]);
      setMetrics(m);
      setTenants(t);
      setConfigs(c);
    } catch (err) {
      console.error("Failed to load superadmin data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const handleToggleTenant = async (tenantId: string) => {
    if (!token) return;
    try {
      await toggleTenantStatus(token, tenantId);
      loadData();
    } catch (err) {
      alert("Failed to toggle tenant status");
    }
  };

  const handleUpdateConfig = async (key: string, currentValue: string) => {
    if (!token) return;
    const newValue = prompt(`Update value for ${key}:`, currentValue);
    if (newValue === null) return;
    try {
      await updatePlatformConfig(token, key, newValue);
      loadData();
    } catch (err) {
      alert("Failed to update config");
    }
  };

  if (loading || !metrics) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const isKillSwitchActive = configs.find(c => c.key === 'kill_switch')?.value === 'true';

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      
      {/* GOD MODE HEADER */}
      <div className="flex justify-between items-end pb-4 border-b border-gray-800">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            <Globe className="h-8 w-8 text-indigo-500" />
            Global Command Center
          </h1>
          <p className="text-gray-400 mt-1">Platform-wide overview and multi-tenant management.</p>
        </div>
        
        {isKillSwitchActive && (
          <div className="bg-red-900/40 border border-red-500/50 text-red-400 px-4 py-2 rounded-lg flex items-center gap-2 animate-pulse">
            <ShieldAlert className="h-5 w-5" />
            <span className="font-semibold">GLOBAL KILL SWITCH ACTIVE</span>
          </div>
        )}
      </div>

      {/* GLOBAL METRICS CARDS */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 shadow-sm relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-indigo-500/10 bg-opacity-10">
              <DollarSign className="h-6 w-6 text-indigo-400" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-400 truncate">Total GWP</dt>
                <dd className="text-2xl font-semibold text-white">₦{metrics.gross_written_premium.toLocaleString()}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 shadow-sm relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-emerald-500/10 bg-opacity-10">
              <Activity className="h-6 w-6 text-emerald-400" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-400 truncate">Active Policies</dt>
                <dd className="text-2xl font-semibold text-white">{metrics.total_active_policies}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 shadow-sm relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-blue-500/10 bg-opacity-10">
              <Database className="h-6 w-6 text-blue-400" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-400 truncate">Tenant Hubs</dt>
                <dd className="text-2xl font-semibold text-white">{metrics.active_insurers}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 shadow-sm relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-orange-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-orange-500/10 bg-opacity-10">
              <Users className="h-6 w-6 text-orange-400" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-400 truncate">B2B Partners</dt>
                <dd className="text-2xl font-semibold text-white">{metrics.active_partners}</dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* TENANT MANAGEMENT (Spans 2 columns) */}
        <div className="lg:col-span-2 bg-gray-800 rounded-xl border border-gray-700 overflow-hidden shadow-sm">
          <div className="border-b border-gray-700 bg-gray-800/50 px-6 py-4">
            <h3 className="text-lg font-medium text-white flex items-center gap-2">
              <Database className="h-5 w-5 text-gray-400" />
              Tenant Provisioning & Status
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-800/80">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Tenant</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Policies</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                  <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-700">
                {tenants.map((tenant) => (
                  <tr key={tenant.id} className="hover:bg-gray-750 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div>
                          <div className="text-sm font-medium text-white">{tenant.company_name}</div>
                          <div className="text-sm text-gray-400">{tenant.tenant_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {tenant.total_policies.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${tenant.is_active ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-500/20' : 'bg-red-900/50 text-red-400 border border-red-500/20'}`}>
                        {tenant.is_active ? 'Active' : 'Suspended'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleToggleTenant(tenant.tenant_id)}
                        className={`inline-flex items-center gap-1 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                          tenant.is_active 
                            ? 'bg-red-500/10 text-red-500 hover:bg-red-500/20' 
                            : 'bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20'
                        }`}
                      >
                        <PowerOff className="h-3 w-3" />
                        {tenant.is_active ? 'Suspend' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* PLATFORM CONFIGS */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden shadow-sm flex flex-col">
          <div className="border-b border-gray-700 bg-gray-800/50 px-6 py-4">
            <h3 className="text-lg font-medium text-white flex items-center gap-2">
              <Settings className="h-5 w-5 text-gray-400" />
              Global Configuration
            </h3>
          </div>
          <div className="p-6 flex-1 space-y-4">
            {configs.map(config => (
              <div key={config.key} className="p-4 bg-gray-900/50 rounded-lg border border-gray-700/50">
                <div className="flex justify-between items-start mb-2">
                  <div className="text-sm font-semibold text-white uppercase tracking-wider">{config.key.replace(/_/g, ' ')}</div>
                  <button 
                    onClick={() => handleUpdateConfig(config.key, config.value)}
                    className="text-indigo-400 hover:text-indigo-300 text-xs font-medium"
                  >
                    Edit
                  </button>
                </div>
                <div className="text-2xl font-bold text-gray-200 mb-1">{config.value}</div>
                <div className="text-xs text-gray-500">{config.description}</div>
                
                {config.key === 'kill_switch' && config.value === 'true' && (
                  <div className="mt-3 text-xs text-red-400 flex items-center gap-1 bg-red-900/20 p-2 rounded">
                    <ShieldAlert className="h-3 w-3" /> Underwriting disabled globally.
                  </div>
                )}
                {config.key === 'global_commission_rate' && (
                  <div className="mt-3 text-xs text-emerald-400 flex items-center gap-1 bg-emerald-900/20 p-2 rounded">
                    <Zap className="h-3 w-3" /> Current take-rate applied to all new policies.
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
