import api from './api';

export const userService = {
  // Get users list
  getUsers: async (params = {}) => {
    try {
      const response = await api.get('/api/admin/users', { params });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Deactivate user
  deactivateUser: async (userId) => {
    try {
      const response = await api.patch(`/api/admin/users/${userId}/deactivate`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Activate user
  activateUser: async (userId) => {
    try {
      const response = await api.patch(`/api/admin/users/${userId}/activate`);
      return response.data;
    } catch (error) {
      throw error;
    }
  }
};