import axios from 'axios';
import authService from './authService';
import { handleApiError } from '../utils/helpers';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:5173';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

let isRefreshing = false;
let failedQueue = [];

function processQueue(error, token = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
}

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = authService.getToken();
    console.log('Token from storage:', token ? 'Present' : 'Not found');
    
    if (token && !config.url?.includes('/api/auth/refresh') && !config.url?.includes('/api/auth/login')) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('Added Authorization header');
    } else if (token) {
      console.log('Skipping Authorization header for auth route:', config.url);
    } else {
      console.warn('No token found for request:', config.url);
    }
    
    console.log('API Request:', config.method.toUpperCase(), config.url);
    console.log('API Request headers:', config.headers);
    console.log('API Request data:', config.data instanceof FormData ? 'FormData' : config.data);
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    
    if (response.config.url.includes('/api/admin/users')) {
      console.log('Users response structure:', Object.keys(response.data));
    }
    
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    console.error('API Error:', error.response?.status, originalRequest?.url, error.message);
    
    if (!originalRequest) {
      return Promise.reject(handleApiError(error));
    }
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (originalRequest?.url?.includes('/api/auth/refresh')) {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_refresh_token');
        localStorage.removeItem('admin_user');
        window.location.href = '/login';
        return Promise.reject(error);
      }
      
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((newToken) => {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        });
      }
      
      originalRequest._retry = true;
      isRefreshing = true;
      
      try {
        const newToken = await authService.refreshToken();
        processQueue(null, newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_refresh_token');
        localStorage.removeItem('admin_user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    
    return Promise.reject(handleApiError(error));
  }
);

export default api;