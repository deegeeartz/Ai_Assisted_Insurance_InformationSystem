import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Login } from './pages/Login';
import { Layout } from './components/layout/Layout';
import { PartnerDashboard } from './pages/PartnerDashboard';
import { ComplianceDashboard } from './pages/ComplianceDashboard';
import React from 'react';

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
          user?.role === 'partner' ? <PartnerDashboard /> : <ComplianceDashboard />
        } />
        <Route path="api-keys" element={<div>API Keys Management (Coming Soon)</div>} />
        <Route path="wallet" element={<div>Commission Wallet (Coming Soon)</div>} />
        <Route path="sla" element={<div>SLA Monitor Detailed View</div>} />
        <Route path="rules" element={<div>Rules Inspector</div>} />
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
