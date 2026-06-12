// services/dishLocationService.js
import api from './api';
import { API_ENDPOINTS } from '../utils/constants';

export const dishLocationService = {
  // Create new dish location
  create: async (data) => {
    try {
      console.log('📤 [create] Creating dish location:', data);
      const response = await api.post(API_ENDPOINTS.DISH_LOCATIONS.CREATE, data);
      console.log('📥 [create] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error creating dish location:', error);
      throw error;
    }
  },

  // Get all dish locations
  getAll: async (params = {}) => {
    try {
      console.log('📤 [getAll] Fetching dish locations with params:', params);
      const response = await api.get(API_ENDPOINTS.DISH_LOCATIONS.LIST, { params });
      console.log('📥 [getAll] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching dish locations:', error);
      throw error;
    }
  },

  // Get dish location tree
  getTree: async () => {
    try {
      console.log('📤 [getTree] Fetching dish location tree');
      const response = await api.get(API_ENDPOINTS.DISH_LOCATIONS.TREE);
      console.log('📥 [getTree] Response status:', response.status);
      console.log('📥 [getTree] Response data:', response.data);
      console.log('📥 [getTree] Response data type:', typeof response.data);
      console.log('📥 [getTree] Is array?', Array.isArray(response.data));
      
      // Kiểm tra cấu trúc response
      if (response.data?.data) {
        console.log('📥 [getTree] Found data.data:', response.data.data);
        return response.data.data;
      }
      
      if (Array.isArray(response.data)) {
        return response.data;
      }
      
      return [];
    } catch (error) {
      console.error('Error fetching dish location tree:', error);
      throw error;
    }
  },

  // Get dish location by id
  getById: async (id) => {
    try {
      console.log('📤 [getById] Fetching dish location:', id);
      const response = await api.get(API_ENDPOINTS.DISH_LOCATIONS.DETAIL(id));
      console.log('📥 [getById] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching dish location:', error);
      throw error;
    }
  },

  // Update dish location
  update: async (id, data) => {
    try {
      console.log('📤 [update] Updating dish location:', id, data);
      const response = await api.patch(API_ENDPOINTS.DISH_LOCATIONS.UPDATE(id), data);
      console.log('📥 [update] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error updating dish location:', error);
      throw error;
    }
  },

  // Delete dish location
  delete: async (id) => {
    try {
      console.log('📤 [delete] Deleting dish location:', id);
      const response = await api.delete(API_ENDPOINTS.DISH_LOCATIONS.DELETE(id));
      console.log('📥 [delete] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error deleting dish location:', error);
      throw error;
    }
  },
getCountries: async () => {
  try {
    console.log('📤 [getCountries] Bắt đầu fetch danh sách quốc gia');
    console.log('📤 [getCountries] Endpoint: /api/dish-locations/countries');
    console.log('📤 [getCountries] Thời gian:', new Date().toISOString());
    
    const startTime = Date.now();
    const response = await api.get('/api/dish-locations/countries');
    const endTime = Date.now();
    
    console.log('✅ [getCountries] Fetch thành công sau', endTime - startTime, 'ms');
    console.log('📥 [getCountries] Status code:', response.status);
    console.log('📥 [getCountries] Response data:', response.data);
    
    // ✅ Lấy đúng mảng locations từ response.data.data
    const locations = response.data?.data || [];
    console.log('📥 [getCountries] Số lượng quốc gia:', locations.length);
    console.log('📥 [getCountries] Locations list:', locations);
    
    // ✅ Trả về mảng locations
    return locations;
  } catch (error) {
    console.error('❌ [getCountries] Lỗi khi fetch danh sách quốc gia:');
    console.error('❌ [getCountries] Error name:', error.name);
    console.error('❌ [getCountries] Error message:', error.message);
    
    if (error.response) {
      console.error('❌ [getCountries] Response status:', error.response.status);
      console.error('❌ [getCountries] Response data:', error.response.data);
    }
    
    throw error;
  }
},
};

export default dishLocationService;