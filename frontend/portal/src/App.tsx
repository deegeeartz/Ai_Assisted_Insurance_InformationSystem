import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Login } from './pages/Login';
import { Layout } from './components/layout/Layout';
import { PartnerDashboard } from './pages/PartnerDashboard';
import { ComplianceDashboard } from './pages/ComplianceDashboard';
import { InsurerDashboard } from './pages/InsurerDashboard';
import React from 'react';

import { CommissionWallet } from './pages/CommissionWallet';
import { SlaMonitor } from './pages/SlaMonitor';
import { RulesInspector } from './pages/RulesInspector';
import { ApiKeys } from './pages/ApiKeys';
import { BatchIssuance } from './pages/BatchIssuance';
import { SuperadminDashboard } from './pages/SuperadminDashboard';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

function AppRoutes() {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      <Route path="/" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route index element={
          user?.role === 'admin' ? <SuperadminDashboard /> :
          user?.role === 'partner' ? <PartnerDashboard /> : 
          user?.role === 'insurer' ? <InsurerDashboard /> : <ComplianceDashboard />
        } />
        <Route path="api-keys" element={<ApiKeys />} />
        <Route path="wallet" element={<CommissionWallet />} />
        <Route path="batch" element={<BatchIssuance />} />
        <Route path="sla" element={<SlaMonitor />} />
        <Route path="rules" element={<RulesInspector />} />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
