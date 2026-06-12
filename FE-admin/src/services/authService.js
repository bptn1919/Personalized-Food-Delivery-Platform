import api from './api';
import { API_ENDPOINTS } from '../utils/constants';

const TOKEN_KEY = 'admin_token';
const REFRESH_TOKEN_KEY = 'admin_refresh_token';
const USER_KEY = 'admin_user';

const authService = {
  // Login with email/password
  login: async (credentials) => {
    try {
      console.log('Login attempt for:', credentials.email);
      
      const response = await api.post('/api/auth/login', {
        email: credentials.email,
        password: credentials.password
      });
      
      console.log('Login response:', response.data);
      
      // API trả về data trong response.data.data
      const responseData = response.data;
      
      if (responseData.message_code === 'SUCCESS' && responseData.data?.access_token) {
        const token = responseData.data.access_token;
        const refreshToken = responseData.data.refresh_token;
        const user = responseData.data.user || {};
        
        console.log('Token received, saving to localStorage');
        localStorage.setItem(TOKEN_KEY, token);
        if (refreshToken) {
          localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
        }
        localStorage.setItem(USER_KEY, JSON.stringify(user));
        
        // Verify token was saved
        const savedToken = localStorage.getItem(TOKEN_KEY);
        console.log('Token saved successfully:', savedToken ? 'Yes' : 'No');
        
        return responseData.data;
      } else {
        console.warn('No token in response:', responseData);
        throw new Error('Invalid Account or Password');
      }
      
    } catch (error) {
      console.error('Login error in service:', error);
      throw error;
    }
  },

  // Logout
  logout: async () => {
    try {
      const token = authService.getToken();
      if (token) {
        await api.put('/api/auth/logout');
      }
    } catch (error) {
      console.error('Logout API error:', error);
    } finally {
      console.log('Clearing localStorage');
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_KEY);

      // Notify App that we logged out
      window.dispatchEvent(new CustomEvent('auth-change', {
        detail: {
          token: null,
          isChef: false
        }
      }));
    }
  },

  // Change password
  changePassword: async (oldPassword, newPassword) => {
    try {
      const response = await api.put('/api/auth/password/change', {
        old_password: oldPassword,
        new_password: newPassword
      });
      return response.data; // Returns true if successful
    } catch (error) {
      console.error('Change password error:', error);
      throw error;
    }
  },

  // Forgot password - send email to get OTP
  forgotPassword: async (email) => {
    try {
      const response = await api.post('/api/auth/password/forget', { email });
      console.log('Forgot password API response:', response.data);
      return response.data; // Trả về toàn bộ response.data
    } catch (error) {
      console.error('Forgot password error:', error);
      throw error;
    }
  },

  // Verify OTP
  verifyOTP: async (resetSessionToken, otp) => {
    try {
      const response = await api.post('/api/auth/verify-otp', {
        reset_session_token: resetSessionToken,
        otp: otp
      });
      console.log('Verify OTP response:', response.data);
      return response.data; // Returns true if valid
    } catch (error) {
      console.error('Verify OTP error:', error);
      throw error;
    }
  },

  // Reset password with token
  resetPassword: async (resetSessionToken, newPassword, confirmPassword) => {
    try {
      const response = await api.put('/api/auth/password/reset', {
        reset_session_token: resetSessionToken,
        new_password: newPassword,
        confirm_password: confirmPassword
      });
      console.log('Reset password response:', response.data);
      return response.data; // Returns true if successful
    } catch (error) {
      console.error('Reset password error:', error);
      throw error;
    }
  },

  // Request email change
  requestEmailChange: async (newEmail) => {
    try {
      console.log('📤 [requestEmailChange] Requesting email change:', newEmail);
      const response = await api.post(API_ENDPOINTS.AUTH.REQUEST_EMAIL_CHANGE, {
        new_email: newEmail
      });
      console.log('📥 [requestEmailChange] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error requesting email change:', error);
      throw error;
    }
  },

  // Verify email change
  verifyEmailChange: async (resetSessionToken, otp) => {
    try {
      console.log('📤 [verifyEmailChange] Verifying email change:', { resetSessionToken, otp });
      const response = await api.post(API_ENDPOINTS.AUTH.VERIFY_EMAIL_CHANGE, {
        reset_session_token: resetSessionToken,
        otp: otp
      });
      console.log('📥 [verifyEmailChange] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error verifying email change:', error);
      throw error;
    }
  },

  // Get current user
  getCurrentUser: () => {
    const userStr = localStorage.getItem(USER_KEY);
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch {
        return null;
      }
    }
    return null;
  },

  // Get token
  getToken: () => {
    const token = localStorage.getItem(TOKEN_KEY);
    return token;
  },

  // Get refresh token
  getRefreshToken: () => {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  // Refresh access token
  refreshToken: async () => {
    const refreshToken = authService.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    const response = await api.post(API_ENDPOINTS.AUTH.REFRESH_TOKEN, {
      refresh_token: refreshToken,
    });
    const responseData = response.data;
    if (responseData.message_code === 'SUCCESS' && responseData.data?.access_token) {
      const newToken = responseData.data.access_token;
      const newRefreshToken = responseData.data.refresh_token;
      localStorage.setItem(TOKEN_KEY, newToken);
      if (newRefreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken);
      }
      return newToken;
    }
    throw new Error('Failed to refresh token');
  },

  // Check if authenticated
  isAuthenticated: () => {
    const token = localStorage.getItem(TOKEN_KEY);
    return !!token;
  },

// Sửa method checkIsChef
checkIsChef: async () => {
  try {
    const response = await api.get('/api/auth/is-chef');
    console.log('👨‍🍳 Check is chef raw response:', response.data);
    
    // API trả về { data: { is_chef, chef_id }, message_code, ... }
    if (response.data?.data) {
      const result = {
        is_chef: response.data.data.is_chef || false,
        chef_id: response.data.data.chef_id || null
      };
      console.log('👨‍🍳 Extracted chef data:', result);
      return result;
    }
    
    // Fallback nếu không có wrapper
    return {
      is_chef: response.data?.is_chef || false,
      chef_id: response.data?.chef_id || null
    };
  } catch (error) {
    console.error('Error checking chef status:', error);
    return { is_chef: false, chef_id: null };
  }
},
};

export default authService;