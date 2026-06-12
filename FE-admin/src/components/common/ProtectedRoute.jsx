import React from 'react';
import { Navigate } from 'react-router-dom';
import  authService  from '../../services/authService'; // Điều chỉnh đường dẫn cho đúng với dự án của bạn

const ProtectedRoute = ({ children }) => {
  // Thay vì tự gọi localStorage.getItem('adminToken'), hãy dùng authService
  if (!authService.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

export default ProtectedRoute;