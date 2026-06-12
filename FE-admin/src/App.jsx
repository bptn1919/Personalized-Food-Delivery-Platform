import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/common/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import Orders from './pages/Orders';
import Vouchers from './pages/Vouchers';
import AdminIngredients from './pages/AdminIngredients';
import AdminBankAccounts from './pages/AdminBankAccounts';
import ProtectedRoute from './components/common/ProtectedRoute';
import { createGlobalStyle } from 'styled-components';
import ForgotPassword from './pages/ForgotPassword';
import VerifyOTP from './pages/VerifyOTP';
import ResetPassword from './pages/ResetPassword';
import AdminCertificates from './pages/AdminCertificates';
import ChefCertificates from './pages/ChefCertificates';
import AdminDishLocations from './pages/AdminDishLocations';
import Dishes from './pages/Dishes';
import Menus from './pages/Menus';
import authService from './services/authService';
import { Loading } from './components/common/Loading';

const GlobalStyle = createGlobalStyle`
  body { margin: 0; }
`;

function App() {
  console.log('📱 App component rendered');
  
  const initialToken = localStorage.getItem('admin_token');
  const [token, setToken] = useState(initialToken);
  const [isChef, setIsChef] = useState(initialToken ? null : false);
  const [loading, setLoading] = useState(initialToken ? true : false);
  const [key, setKey] = useState(0);

  useEffect(() => {
    const handleAuthChange = (e) => {
      const detail = e.detail || {};
      console.log('🔔 [App] auth-change event details:', detail);
      
      if ('token' in detail) {
        setToken(detail.token);
      } else {
        setToken(localStorage.getItem('admin_token'));
      }

      if ('isChef' in detail) {
        setIsChef(detail.isChef);
        setLoading(false);
        setKey(prev => prev + 1);
      } else {
        // If logged out or token cleared
        if (!localStorage.getItem('admin_token')) {
          setIsChef(false);
          setLoading(false);
        } else {
          setIsChef(null);
          setLoading(true);
        }
      }
    };

    window.addEventListener('auth-change', handleAuthChange);
    window.addEventListener('storage', handleAuthChange);

    return () => {
      window.removeEventListener('auth-change', handleAuthChange);
      window.removeEventListener('storage', handleAuthChange);
    };
  }, []);

  useEffect(() => {
    console.log('🔄 App useEffect checkChefStatus. token:', !!token, 'isChef:', isChef);
    
    const checkChefStatus = async () => {
      console.log('👨‍🍳 Starting checkChefStatus...');
      setLoading(true);
      
      try {
        console.log('👨‍🍳 Calling authService.checkIsChef()');
        const result = await authService.checkIsChef();
        console.log('👨‍🍳 Chef status result:', result);
        
        setIsChef(result.is_chef);
        setKey(prev => prev + 1);
      } catch (error) {
        console.error('❌ Error checking chef status:', error);
        setIsChef(false);
      } finally {
        setLoading(false);
        console.log('👨‍🍳 checkChefStatus completed, isChef:', isChef);
      }
    };

    // Only fetch if isChef is null and token is present
    if (token && isChef === null) {
      checkChefStatus();
    } else if (!token) {
      setIsChef(false);
      setLoading(false);
    }
  }, [token, isChef]);

  if (loading) {
    console.log('⏳ App loading...');
    return <Loading fullPage text="Loading..." />;
  }

  console.log('✅ App ready, isChef:', isChef, 'key:', key);
  console.log('🔄 Rendering with isChef:', isChef);

  const getDefaultRedirect = () => {
    console.log('👨‍🍳 getDefaultRedirect - isChef:', isChef);
    if (isChef) {
      return <Navigate to="/chefcertificates" replace />;
    }
    return <Navigate to="/dashboard" replace />;
  };

  return (
    <>
      <GlobalStyle />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/verify-otp" element={<VerifyOTP />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          
          <Route path="/" element={
            <ProtectedRoute>
              {/* Chỉ render Layout khi isChef đã được xác định */}
              {isChef !== null && <Layout key={key} isChef={isChef} />}
            </ProtectedRoute>
          }>
            <Route index element={getDefaultRedirect()} />
            
            {/* Admin routes */}
            {!isChef && (
              <>
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="users" element={<Users />} />
                <Route path="orders" element={<Orders />} />
                <Route path="admincertificates" element={<AdminCertificates />} />
                <Route path="vouchers" element={<Vouchers />} />
                <Route path="ingredients" element={<AdminIngredients />} />
                <Route path="bank-accounts" element={<AdminBankAccounts />} />
                <Route path="dish-locations" element={<AdminDishLocations />} />
              </>
            )}
            
            {/* Chef routes */}
            {isChef && (
              <>
                <Route path="chefcertificates" element={<ChefCertificates />} />
                <Route path="dishes" element={<Dishes />} />
                <Route path="menus" element={<Menus />} />
              </>
            )}
          </Route>
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </>
  );
}

export default App;