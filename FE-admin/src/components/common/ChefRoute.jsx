import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { Loading } from './Loading';
import authService from '../../services/authService';

export const ChefRoute = ({ children }) => {
  const [isChef, setIsChef] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkChefStatus = async () => {
      try {
        const result = await authService.checkIsChef();
        setIsChef(result.is_chef);
      } catch (error) {
        console.error('Error in ChefRoute:', error);
        setIsChef(false);
      } finally {
        setLoading(false);
      }
    };

    if (authService.isAuthenticated()) {
      checkChefStatus();
    } else {
      setIsChef(false);
      setLoading(false);
    }
  }, []);

  if (loading) {
    return <Loading fullPage text="Checking permissions..." />;
  }

  return isChef ? children : <Navigate to="/dashboard" replace />;
};