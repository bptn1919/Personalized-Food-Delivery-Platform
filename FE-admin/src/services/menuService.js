import api from './api';
import { API_ENDPOINTS } from '../utils/constants';

export const menuService = {
  // ========== MENU APIs ==========
  
  // Get all my menus (for chef) - GET /api/menus/mine
  getMyMenus: async () => {
    try {
      console.log('📤 [getMyMenus] Fetching my menus');
      const response = await api.get(API_ENDPOINTS.MENUS.MY_LIST);
      console.log('📥 [getMyMenus] Response:', response.data);
      
      // API trả về array trực tiếp
      if (Array.isArray(response.data)) {
        return response.data;
      }
      // Nếu có data wrapper
      if (response.data?.data && Array.isArray(response.data.data)) {
        return response.data.data;
      }
      return [];
    } catch (error) {
      console.error('❌ Error fetching my menus:', error);
      throw error;
    }
  },

  // Get all menus of chef (public) - GET /api/menus/{chefId}
  getMenusOfChef: async (chefId) => {
    try {
      console.log('📤 [getMenusOfChef] Fetching menus of chef:', chefId);
      const response = await api.get(API_ENDPOINTS.MENUS.BY_CHEF(chefId));
      console.log('📥 [getMenusOfChef] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error fetching chef menus:', error);
      throw error;
    }
  },

  // Create new menu - POST /api/menus
  createMenu: async (menuData) => {
    try {
      console.log('📤 [createMenu] Creating menu with data:', menuData);
      const response = await api.post(API_ENDPOINTS.MENUS.CREATE, menuData);
      console.log('📥 [createMenu] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error creating menu:', error);
      throw error;
    }
  },

  // Update menu - PUT /api/menus/{uid}
  updateMenu: async (uid, menuData) => {
    try {
      console.log('📤 [updateMenu] Updating menu:', uid, menuData);
      const response = await api.put(API_ENDPOINTS.MENUS.UPDATE(uid), menuData);
      console.log('📥 [updateMenu] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error updating menu:', error);
      throw error;
    }
  },

  // Get menu detail - GET /api/menus/{uid}
  getMenuDetail: async (uid) => {
    try {
      console.log('📤 [getMenuDetail] Fetching menu detail:', uid);
      const response = await api.get(API_ENDPOINTS.MENUS.GET_BY_UID(uid));
      console.log('📥 [getMenuDetail] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error fetching menu detail:', error);
      throw error;
    }
  },

  // Soft delete menu - PUT /api/menus/{uid}/deleted
  softDeleteMenu: async (uid) => {
    try {
      console.log('📤 [softDeleteMenu] Soft deleting menu:', uid);
      const response = await api.put(API_ENDPOINTS.MENUS.SOFT_DELETE(uid));
      console.log('📥 [softDeleteMenu] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error soft deleting menu:', error);
      throw error;
    }
  },

  // Restore menu - PUT /api/menus/{uid}/restore
  restoreMenu: async (uid) => {
    try {
      console.log('📤 [restoreMenu] Restoring menu:', uid);
      const response = await api.put(API_ENDPOINTS.MENUS.RESTORE(uid));
      console.log('📥 [restoreMenu] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error restoring menu:', error);
      throw error;
    }
  },

  // Hard delete menu - DELETE /api/menus/{uid}
  hardDeleteMenu: async (uid) => {
    try {
      console.log('📤 [hardDeleteMenu] Hard deleting menu:', uid);
      const response = await api.delete(API_ENDPOINTS.MENUS.HARD_DELETE(uid));
      console.log('📥 [hardDeleteMenu] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error hard deleting menu:', error);
      throw error;
    }
  },

  // Activate menu - PATCH /api/menus/{uid}/activate
  activateMenu: async (uid) => {
    try {
      console.log('📤 [activateMenu] Activating menu:', uid);
      const response = await api.patch(API_ENDPOINTS.MENUS.ACTIVATE(uid));
      console.log('📥 [activateMenu] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error activating menu:', error);
      throw error;
    }
  },

  // Deactivate menu - PATCH /api/menus/{uid}/deactivate
  deactivateMenu: async (uid) => {
    try {
      console.log('📤 [deactivateMenu] Deactivating menu:', uid);
      const response = await api.patch(API_ENDPOINTS.MENUS.DEACTIVATE(uid));
      console.log('📥 [deactivateMenu] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error deactivating menu:', error);
      throw error;
    }
  },

  // ========== DISHES IN MENU APIs ==========
  
  // Get all dishes in menu (for chef) - GET /api/menus/{uid}/all-dishes
  getDishesInMenu: async (uid, active = null) => {
    try {
      console.log('📤 [getDishesInMenu] Fetching dishes in menu:', uid);
      const params = {};
      if (active !== null) params.active = active;
      
      const response = await api.get(API_ENDPOINTS.MENUS.DISHES_ALL(uid), { params });
      console.log('📥 [getDishesInMenu] Response:', response.data);
      
      if (Array.isArray(response.data)) {
        return response.data;
      }
      if (response.data?.data && Array.isArray(response.data.data)) {
        return response.data.data;
      }
      return [];
    } catch (error) {
      console.error('❌ Error fetching dishes in menu:', error);
      throw error;
    }
  },

  // Get public dishes in menu (for customer) - GET /api/menus/{uid}/dishes
  getPublicDishesInMenu: async (uid) => {
    try {
      console.log('📤 [getPublicDishesInMenu] Fetching public dishes in menu:', uid);
      const response = await api.get(API_ENDPOINTS.MENUS.DISHES_PUBLIC(uid));
      console.log('📥 [getPublicDishesInMenu] Response:', response.data);
      
      if (Array.isArray(response.data)) {
        return response.data;
      }
      return [];
    } catch (error) {
      console.error('❌ Error fetching public dishes in menu:', error);
      throw error;
    }
  },

  // Add dish to menu - POST /api/menus/{uid}/add-dish/
  addDishToMenu: async (uid, dishUid, position = 0, active = true) => {
    try {
      console.log('📤 [addDishToMenu] Adding dish to menu:', { uid, dishUid, position, active });
      const response = await api.post(API_ENDPOINTS.MENUS.ADD_DISH(uid), {
        dish_uid: dishUid,
        position,
        active
      });
      console.log('📥 [addDishToMenu] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error adding dish to menu:', error);
      throw error;
    }
  },

  // Activate dish in menu - PATCH /api/menus/{uid}/dishes/{dish_uid}/activate
  activateDishInMenu: async (uid, dishUid) => {
    try {
      console.log('📤 [activateDishInMenu] Activating dish in menu:', { uid, dishUid });
      const response = await api.patch(API_ENDPOINTS.MENUS.ACTIVATE_DISH(uid, dishUid));
      console.log('📥 [activateDishInMenu] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error activating dish in menu:', error);
      throw error;
    }
  },

  // Deactivate dish in menu - PATCH /api/menus/{uid}/dishes/{dish_uid}/deactivate
  deactivateDishInMenu: async (uid, dishUid) => {
    try {
      console.log('📤 [deactivateDishInMenu] Deactivating dish in menu:', { uid, dishUid });
      const response = await api.patch(API_ENDPOINTS.MENUS.DEACTIVATE_DISH(uid, dishUid));
      console.log('📥 [deactivateDishInMenu] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error deactivating dish in menu:', error);
      throw error;
    }
  }
};

export default menuService;