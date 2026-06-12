import api from './api';
import { API_ENDPOINTS } from '../utils/constants';

export const dishService = {
  // Create new dish
  create: async (dishData) => {
    try {
      console.log('📤 [dish] Creating dish:', dishData);
      const response = await api.post(API_ENDPOINTS.DISHES.CREATE, dishData);
      return response.data;
    } catch (error) {
      console.error('❌ Error creating dish:', error);
      throw error;
    }
  },

  // Alias for create (used by Dishes.jsx)
  createDish: async (dishData) => {
    return dishService.create(dishData);
  },

// Trong dishService.js
getAll: async (params = {}) => {
  try {
    console.log('📤 [dish] Fetching dishes with params:', params);
    const response = await api.get(API_ENDPOINTS.DISHES.LIST, { params });
    
    // ✅ Log chi tiết response
    console.log('📥 [dish] GET /api/dishes/ response status:', response.status);
    console.log('📥 [dish] Response data structure:', Object.keys(response.data || {}));
    
    // ✅ Log dish cụ thể để xem location
    if (response.data?.data?.content && response.data.data.content.length > 0) {
      const firstDish = response.data.data.content[0];
      console.log('🍽️ First dish in list:', {
        uid: firstDish.uid,
        name: firstDish.name,
        location: firstDish.location,      // Có field location không?
        location_id: firstDish.location_id, // Có field location_id không?
        fullDish: firstDish
      });
      
      // ✅ Tìm dish cụ thể
      const targetDish = response.data.data.content.find(
        d => d.uid === '50266426-e5b4-4c25-8a71-3d64913eaac0'
      );
      if (targetDish) {
        console.log('🎯 TARGET DISH found:', {
          uid: targetDish.uid,
          name: targetDish.name,
          location: targetDish.location,
          location_id: targetDish.location_id,
          hasLocationField: 'location' in targetDish,
          hasLocationIdField: 'location_id' in targetDish,
          allFields: Object.keys(targetDish)
        });
      } else {
        console.log('❌ Target dish NOT found in response');
      }
    }
    
    return response.data;
  } catch (error) {
    console.error('❌ Error fetching dishes:', error);
    throw error;
  }
},

  // Alias for getAll (used by Dishes.jsx)
  getDishes: async (params = {}) => {
    return dishService.getAll(params);
  },

  getMyDishes: async (params = {}) => {
  try {
    console.log(`📤 [my-dishes] Fetching my dishes with params:`, params);
    
    // Sử dụng endpoint MINE mới cấu hình
    const endpoint = API_ENDPOINTS.DISHES.MINE || '/api/dishes/mine';

    const response = await api.get(endpoint, { params });
    
    // ✅ Log chi tiết response
    console.log(`📥 [my-dishes] GET ${endpoint} response status:`, response.status);
    console.log('📥 [my-dishes] Response data structure:', Object.keys(response.data || {}));
    
    // ✅ Log dish cụ thể để tiếp tục debug các field như location
    if (response.data?.data?.content && response.data.data.content.length > 0) {
      const firstDish = response.data.data.content[0];
      console.log('🍽️ First dish in my list:', {
        uid: firstDish.uid,
        name: firstDish.name,
        location: firstDish.location,      // Kiểm tra field location
        location_id: firstDish.location_id, // Kiểm tra field location_id
        owner_id: firstDish.owner_id || firstDish.owner?.id, // Kiểm tra xem owner_id có khớp với user hiện tại không
        fullDish: firstDish
      });
      
      // ✅ Tìm dish cụ thể (Giữ nguyên UUID mà bạn đang debug)
      const targetDish = response.data.data.content.find(
        d => d.uid === '50266426-e5b4-4c25-8a71-3d64913eaac0'
      );
      if (targetDish) {
        console.log('🎯 TARGET DISH found in my list:', {
          uid: targetDish.uid,
          name: targetDish.name,
          location: targetDish.location,
          location_id: targetDish.location_id,
          hasLocationField: 'location' in targetDish,
          hasLocationIdField: 'location_id' in targetDish,
          allFields: Object.keys(targetDish)
        });
      } else {
        console.log('❌ Target dish NOT found in my response');
      }
    } else {
      console.log('⚠️ [my-dishes] You have no dishes yet or the list is empty.');
    }
    
    return response.data;
  } catch (error) {
    console.error(`❌ Error fetching my dishes:`, error);
    throw error;
  }
},

  // Get top dishes
  getTop: async (limit = 10) => {
    try {
      console.log('📤 [dish] Fetching top dishes:', limit);
      const response = await api.get(API_ENDPOINTS.DASHBOARD.TOP_DISHES, {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error('❌ Error fetching top dishes:', error);
      throw error;
    }
  },

  // Get dish detail
  getDetail: async (uid) => {
    try {
      console.log('📤 [dish] Fetching dish detail:', uid);
      const response = await api.get(API_ENDPOINTS.DISHES.DETAIL(uid));
      return response.data;
    } catch (error) {
      console.error('❌ Error fetching dish detail:', error);
      throw error;
    }
  },

  // Update dish
update: async (uid, dishData) => {
  try {
    console.log('📤 [dish] Updating dish:', uid);
    console.log('📤 [dish] Update data:', JSON.stringify(dishData, null, 2));
    console.log('📍 [dish] Location ID in update:', dishData.location_id);
    
    const response = await api.patch(API_ENDPOINTS.DISHES.UPDATE(uid), dishData);
    
    console.log('✅ [dish] Updated successfully');
    console.log('✅ [dish] Response location_id:', response.data?.data?.location_id);
    
    return response.data;
  } catch (error) {
    console.error('❌ Error updating dish:', error);
    throw error;
  }
},

  // Alias for update (used by Dishes.jsx)
  updateDish: async (uid, dishData) => {
    return dishService.update(uid, dishData);
  },

  // Soft delete dish
  softDelete: async (uid) => {
    try {
      console.log('📤 [dish] Soft deleting dish:', uid);
      const response = await api.put(API_ENDPOINTS.DISHES.SOFT_DELETE(uid));
      return response.data;
    } catch (error) {
      console.error('❌ Error soft deleting dish:', error);
      throw error;
    }
  },

  // Alias for softDelete (used by Dishes.jsx)
  softDeleteDish: async (uid) => {
    return dishService.softDelete(uid);
  },

  // Restore dish
  restore: async (uid) => {
    try {
      console.log('📤 [dish] Restoring dish:', uid);
      const response = await api.put(API_ENDPOINTS.DISHES.RESTORE(uid));
      return response.data;
    } catch (error) {
      console.error('❌ Error restoring dish:', error);
      throw error;
    }
  },

  // Hard delete dish
  hardDelete: async (uid) => {
    try {
      console.log('📤 [dish] Hard deleting dish:', uid);
      const response = await api.delete(API_ENDPOINTS.DISHES.HARD_DELETE(uid));
      return response.data;
    } catch (error) {
      console.error('❌ Error hard deleting dish:', error);
      throw error;
    }
  },

  // Get dish availabilities
  getAvailabilities: async (uid) => {
    try {
      console.log('📤 [dish] Fetching availabilities:', uid);
      const response = await api.get(API_ENDPOINTS.DISHES.AVAILABILITIES(uid));
      return response.data;
    } catch (error) {
      console.error('❌ Error fetching availabilities:', error);
      throw error;
    }
  },

  // Create dish availability
  createAvailability: async (uid, availabilityData) => {
    try {
      console.log('📤 [dish] Creating availability:', uid, availabilityData);
      const response = await api.post(`/api/dishes/${uid}/availabilities`, availabilityData);
      return response.data;
    } catch (error) {
      console.error('❌ Error creating availability:', error);
      throw error;
    }
  },

  // Add ingredient to dish
  addIngredient: async (uid, ingredientData) => {
    try {
      console.log('📤 [dish] Adding ingredient to dish:', uid, ingredientData);
      const response = await api.post(API_ENDPOINTS.INGREDIENTS.DISH_ADD_INGREDIENT(uid), ingredientData);
      return response.data;
    } catch (error) {
      console.error('❌ Error adding ingredient to dish:', error);
      throw error;
    }
  },

  // Preview ingredient for dish
// Preview ingredient for dish
previewIngredient: async (uid, previewData) => {
  try {
    console.log('📤 [previewIngredient] ===== START =====');
    console.log('📤 [previewIngredient] Dish UID:', uid);
    console.log('📤 [previewIngredient] Preview data:', JSON.stringify(previewData, null, 2));
    console.log('📤 [previewIngredient] Ingredient UID:', previewData?.ingredient_uid);
    console.log('📤 [previewIngredient] Weight:', previewData?.weight);
    console.log('🔗 [previewIngredient] Endpoint:', API_ENDPOINTS.INGREDIENTS.DISH_PREVIEW_INGREDIENT(uid));
    
    const startTime = Date.now();
    const response = await api.post(API_ENDPOINTS.INGREDIENTS.DISH_PREVIEW_INGREDIENT(uid), previewData);
    const endTime = Date.now();
    
    console.log('📥 [previewIngredient] Response status:', response.status);
    console.log('📥 [previewIngredient] Response time:', endTime - startTime, 'ms');
    console.log('📥 [previewIngredient] Response data:', response.data);
    console.log('📥 [previewIngredient] Confidence:', response.data?.confidence);
    console.log('📥 [previewIngredient] Warnings:', response.data?.warnings);
    console.log('✅ [previewIngredient] ===== SUCCESS =====');
    return response.data;
  } catch (error) {
    console.error('❌ [previewIngredient] ===== ERROR =====');
    console.error('❌ [previewIngredient] Dish UID:', uid);
    console.error('❌ [previewIngredient] Preview data:', previewData);
    console.error('❌ [previewIngredient] Error message:', error.message);
    console.error('❌ [previewIngredient] Error response:', error.response?.data);
    console.error('❌ [previewIngredient] Error status:', error.response?.status);
    throw error;
  }
},

// Suggest ingredient for dish
suggestIngredient: async (uid, suggestionData) => {
  try {
    console.log('📤 [suggestIngredient] ===== START =====');
    console.log('📤 [suggestIngredient] Dish UID:', uid);
    console.log('📤 [suggestIngredient] Suggestion data:', JSON.stringify(suggestionData, null, 2));
    console.log('📤 [suggestIngredient] Custom name:', suggestionData?.custom_name);
    console.log('📤 [suggestIngredient] Category:', suggestionData?.category);
    console.log('📤 [suggestIngredient] Weight:', suggestionData?.weight);
    console.log('🔗 [suggestIngredient] Endpoint:', API_ENDPOINTS.INGREDIENTS.DISH_SUGGEST_INGREDIENT(uid));
    
    const startTime = Date.now();
    const response = await api.post(API_ENDPOINTS.INGREDIENTS.DISH_SUGGEST_INGREDIENT(uid), suggestionData);
    const endTime = Date.now();
    
    console.log('📥 [suggestIngredient] Response status:', response.status);
    console.log('📥 [suggestIngredient] Response time:', endTime - startTime, 'ms');
    console.log('📥 [suggestIngredient] Response data:', response.data);
    console.log('📥 [suggestIngredient] Suggestion UID:', response.data?.uid);
    console.log('📥 [suggestIngredient] Status:', response.data?.status);
    console.log('✅ [suggestIngredient] ===== SUCCESS =====');
    return response.data;
  } catch (error) {
    console.error('❌ [suggestIngredient] ===== ERROR =====');
    console.error('❌ [suggestIngredient] Dish UID:', uid);
    console.error('❌ [suggestIngredient] Suggestion data:', suggestionData);
    console.error('❌ [suggestIngredient] Error message:', error.message);
    console.error('❌ [suggestIngredient] Error response:', error.response?.data);
    console.error('❌ [suggestIngredient] Error status:', error.response?.status);
    throw error;
  }
},

// Preview suggest ingredient for dish
previewSuggestIngredient: async (uid, previewData) => {
  try {
    console.log('📤 [previewSuggestIngredient] ===== START =====');
    console.log('📤 [previewSuggestIngredient] Dish UID:', uid);
    console.log('📤 [previewSuggestIngredient] Preview data:', JSON.stringify(previewData, null, 2));
    console.log('📤 [previewSuggestIngredient] Custom name:', previewData?.custom_name);
    console.log('📤 [previewSuggestIngredient] Category:', previewData?.category);
    console.log('📤 [previewSuggestIngredient] Weight:', previewData?.weight);
    console.log('🔗 [previewSuggestIngredient] Endpoint:', API_ENDPOINTS.INGREDIENTS.DISH_PREVIEW_SUGGESTION(uid));
    
    const startTime = Date.now();
    const response = await api.post(API_ENDPOINTS.INGREDIENTS.DISH_PREVIEW_SUGGESTION(uid), previewData);
    const endTime = Date.now();
    
    console.log('📥 [previewSuggestIngredient] Response status:', response.status);
    console.log('📥 [previewSuggestIngredient] Response time:', endTime - startTime, 'ms');
    console.log('📥 [previewSuggestIngredient] Response data:', response.data);
    console.log('📥 [previewSuggestIngredient] Confidence:', response.data?.confidence);
    console.log('📥 [previewSuggestIngredient] Candidates:', response.data?.candidates?.length);
    console.log('✅ [previewSuggestIngredient] ===== SUCCESS =====');
    return response.data;
  } catch (error) {
    console.error('❌ [previewSuggestIngredient] ===== ERROR =====');
    console.error('❌ [previewSuggestIngredient] Dish UID:', uid);
    console.error('❌ [previewSuggestIngredient] Preview data:', previewData);
    console.error('❌ [previewSuggestIngredient] Error message:', error.message);
    console.error('❌ [previewSuggestIngredient] Error response:', error.response?.data);
    console.error('❌ [previewSuggestIngredient] Error status:', error.response?.status);
    throw error;
  }
},
};
