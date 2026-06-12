// services/ingredientService.js
import api from './api';
import authService from './authService';
import { API_ENDPOINTS } from '../utils/constants';

export const ingredientService = {
  
  // ========== INGREDIENT CRUD (Admin + Chef) ==========
  
  // Get all ingredients with filters
  getAllIngredients: async (params = {}) => {
    try {
      console.log('📤 [getAllIngredients] Request params:', params);
      const response = await api.get(API_ENDPOINTS.INGREDIENTS.LIST, { params });
      
      console.log('📥 [getAllIngredients] Response status:', response.status);
      console.log('📥 [getAllIngredients] Response data:', response.data);
      
      if (response.data?.data) {
        console.log('✅ Found data.data:', response.data.data);
        return response.data.data;
      }
      
      if (response.data?.content) {
        return response.data;
      }
      
      return response.data;
    } catch (error) {
      console.error('❌ [getAllIngredients] Error:', error);
      throw error;
    }
  },

  // Get ingredient detail
// Get ingredient detail
// Trong ingredientService.js
getIngredientDetail: async (uid) => {
  try {
    console.log('📤 [getIngredientDetail] ===== START =====');
    console.log('📤 [getIngredientDetail] UID:', uid);
    console.log('🔗 [getIngredientDetail] Endpoint:', API_ENDPOINTS.INGREDIENTS.DETAIL(uid));
    
    const response = await api.get(API_ENDPOINTS.INGREDIENTS.DETAIL(uid));
    
    console.log('📥 [getIngredientDetail] Response status:', response.status);
    console.log('📥 [getIngredientDetail] Full response:', response);
    console.log('📥 [getIngredientDetail] Response data:', response.data);
    console.log('📥 [getIngredientDetail] Response data type:', typeof response.data);
    
    // Log chi tiết các field dinh dưỡng
    if (response.data) {
      const data = response.data.data || response.data;
      console.log('📥 [getIngredientDetail] Extracted data:', data);
      console.log('📥 [getIngredientDetail] Nutrition fields check:', {
        has_natri: 'natri' in data,
        natri_value: data.natri,
        has_kali: 'kali' in data,
        kali_value: data.kali,
        has_calcium: 'calcium' in data,
        calcium_value: data.calcium,
        has_fe: 'fe' in data,
        fe_value: data.fe,
        all_keys: Object.keys(data)
      });
    }
    
    console.log('✅ [getIngredientDetail] ===== SUCCESS =====');
    return response.data;
  } catch (error) {
    console.error('❌ [getIngredientDetail] ===== ERROR =====');
    console.error('❌ [getIngredientDetail] Error message:', error.message);
    console.error('❌ [getIngredientDetail] Error response:', error.response?.data);
    console.error('❌ [getIngredientDetail] Error status:', error.response?.status);
    throw error;
  }
},

  // Autocomplete ingredients
autocompleteIngredients: async (query, limit = 10) => {
  try {
    console.log('📤 [autocompleteIngredients] Request:', { query, limit });
    const response = await api.get(API_ENDPOINTS.INGREDIENTS.AUTOCOMPLETE, {
      params: { query, limit }
    });
    
    console.log('📥 [autocompleteIngredients] Response data:', response.data);
    
    // API trả về array trực tiếp
    if (Array.isArray(response.data)) {
      return response.data;
    }
    
    // Nếu có wrapper data
    if (response.data?.data && Array.isArray(response.data.data)) {
      console.log('✅ Found response.data.data:', response.data.data);
      return response.data.data;
    }
    
    return [];
  } catch (error) {
    console.error('❌ [autocompleteIngredients] Error:', error);
    return [];
  }
},

  // Search ingredients (advanced search)
  searchIngredients: async (query, params = {}) => {
    try {
      console.log('📤 [searchIngredients] Request:', { query, params });
      const response = await api.get(API_ENDPOINTS.INGREDIENTS.SEARCH, {
        params: { query, ...params }
      });
      
      console.log('📥 [searchIngredients] Response data:', response.data);
      
      if (response.data?.content && Array.isArray(response.data.content)) {
        return response.data.content;
      }
      
      if (response.data?.data && Array.isArray(response.data.data)) {
        return response.data.data;
      }
      
      if (Array.isArray(response.data)) {
        return response.data;
      }
      
      return [];
    } catch (error) {
      console.error('❌ [searchIngredients] Error:', error);
      return [];
    }
  },

  // ========== INGREDIENT ADMIN APIS (Admin only) ==========
  
// ingredientService.js - thêm log vào các hàm

createIngredient: async (data) => {
  try {
    console.log('📤 [createIngredient] Request data:', data);
    console.log('🔗 [createIngredient] Endpoint:', API_ENDPOINTS.INGREDIENTS.CREATE);
    
    const response = await api.post(API_ENDPOINTS.INGREDIENTS.CREATE, data);
    
    console.log('📥 [createIngredient] Response status:', response.status);
    console.log('📥 [createIngredient] Response data:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ [createIngredient] Error:', error);
    console.error('❌ [createIngredient] Error response:', error.response?.data);
    console.error('❌ [createIngredient] Error status:', error.response?.status);
    throw error;
  }
},

updateIngredient: async (uid, data) => {
  try {
    console.log('📤 [updateIngredient] UID:', uid);
    console.log('📤 [updateIngredient] Update data:', data);
    console.log('🔗 [updateIngredient] Endpoint:', API_ENDPOINTS.INGREDIENTS.UPDATE(uid));
    
    const response = await api.put(API_ENDPOINTS.INGREDIENTS.UPDATE(uid), data);
    
    console.log('📥 [updateIngredient] Response status:', response.status);
    console.log('📥 [updateIngredient] Response data:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ [updateIngredient] Error:', error);
    console.error('❌ [updateIngredient] Error response:', error.response?.data);
    console.error('❌ [updateIngredient] Error status:', error.response?.status);
    throw error;
  }
},

softDeleteIngredient: async (uid) => {
  try {
    console.log('📤 [softDeleteIngredient] UID:', uid);
    console.log('🔗 [softDeleteIngredient] Endpoint:', API_ENDPOINTS.INGREDIENTS.SOFT_DELETE(uid));
    
    const response = await api.put(API_ENDPOINTS.INGREDIENTS.SOFT_DELETE(uid));
    
    console.log('📥 [softDeleteIngredient] Response status:', response.status);
    console.log('📥 [softDeleteIngredient] Response data:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ [softDeleteIngredient] Error:', error);
    console.error('❌ [softDeleteIngredient] Error response:', error.response?.data);
    console.error('❌ [softDeleteIngredient] Error status:', error.response?.status);
    throw error;
  }
},

restoreIngredient: async (uid) => {
  try {
    console.log('📤 [restoreIngredient] UID:', uid);
    console.log('🔗 [restoreIngredient] Endpoint:', API_ENDPOINTS.INGREDIENTS.RESTORE(uid));
    
    const response = await api.put(API_ENDPOINTS.INGREDIENTS.RESTORE(uid));
    
    console.log('📥 [restoreIngredient] Response status:', response.status);
    console.log('📥 [restoreIngredient] Response data:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ [restoreIngredient] Error:', error);
    console.error('❌ [restoreIngredient] Error response:', error.response?.data);
    console.error('❌ [restoreIngredient] Error status:', error.response?.status);
    throw error;
  }
},

hardDeleteIngredient: async (uid) => {
  try {
    console.log('📤 [hardDeleteIngredient] UID:', uid);
    console.log('🔗 [hardDeleteIngredient] Endpoint:', API_ENDPOINTS.INGREDIENTS.HARD_DELETE(uid));
    
    const response = await api.delete(API_ENDPOINTS.INGREDIENTS.HARD_DELETE(uid));
    
    console.log('📥 [hardDeleteIngredient] Response status:', response.status);
    console.log('📥 [hardDeleteIngredient] Response data:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ [hardDeleteIngredient] Error:', error);
    console.error('❌ [hardDeleteIngredient] Error response:', error.response?.data);
    console.error('❌ [hardDeleteIngredient] Error status:', error.response?.status);
    throw error;
  }
},

  exportTemplate: async () => {
    try {
      const response = await api.get(API_ENDPOINTS.INGREDIENTS.EXPORT_TEMPLATE, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('Error exporting template:', error);
      throw error;
    }
  },

importIngredients: async (file) => {
  try {
    console.log('📤 [importIngredients] ===== START =====');
    console.log('📤 [importIngredients] File name:', file?.name);
    console.log('📤 [importIngredients] File size:', file?.size, 'bytes');
    console.log('📤 [importIngredients] File type:', file?.type);
    console.log('🔗 [importIngredients] Endpoint:', API_ENDPOINTS.INGREDIENTS.IMPORT_EXCEL);
    
    const formData = new FormData();
    formData.append('file', file);
    
    console.log('📤 [importIngredients] FormData created, sending request...');
    console.log('📤 [importIngredients] FormData keys:', Array.from(formData.keys()));
    console.log('📤 [importIngredients] FormData entries:', Array.from(formData.entries()).map(([k, v]) => [k, v instanceof File ? {name: v.name, size: v.size, type: v.type} : v]));
    
    const startTime = Date.now();
    
    // Thử dùng fetch thay vì axios để đảm bảo gửi đúng multipart
    const token = authService.getToken();
    const response = await fetch(API_ENDPOINTS.INGREDIENTS.IMPORT_EXCEL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
        // KHÔNG set Content-Type - browser tự động thêm boundary
      },
      body: formData
    });
    
    const responseData = await response.json();
    console.log('📥 [importIngredients] Response status:', response.status);
    console.log('📥 [importIngredients] Response data:', responseData);
    
    if (!response.ok) {
      throw new Error(responseData.message || 'Import failed');
    }
    
    const endTime = Date.now();
    console.log('📥 [importIngredients] Response time:', endTime - startTime, 'ms');
    console.log('✅ [importIngredients] ===== SUCCESS =====');
    return responseData;
    
    console.log('📥 [importIngredients] Response status:', response.status);
    console.log('📥 [importIngredients] Response time:', endTime - startTime, 'ms');
    console.log('📥 [importIngredients] Response data:', response.data);
    console.log('📥 [importIngredients] Success:', response.data?.message);
    
    // Log số lượng ingredient import được
    if (response.data?.data) {
      const importedCount = response.data.data.imported_count || response.data.data.length || 0;
      console.log('📥 [importIngredients] Imported count:', importedCount);
    }
    
    console.log('✅ [importIngredients] ===== SUCCESS =====');
    return response.data;
  } catch (error) {
    console.error('❌ [importIngredients] ===== ERROR =====');
    console.error('❌ [importIngredients] File name:', file?.name);
    console.error('❌ [importIngredients] Error message:', error.message);
    console.error('❌ [importIngredients] Error response:', error.response?.data);
    console.error('❌ [importIngredients] Error status:', error.response?.status);
    
    // Log chi tiết lỗi validation nếu có
    if (error.response?.data?.message_code === 'VALIDATION_ERROR') {
      console.error('❌ [importIngredients] Validation details:', error.response?.data?.data);
    }
    
    throw error;
  }
},

  // ========== ALIAS APIS (Admin only) ==========
  
  createAlias: async (ingredientUid, alias) => {
    try {
      const response = await api.post(API_ENDPOINTS.INGREDIENTS.ALIASES_CREATE, {
        ingredient_uid: ingredientUid,
        alias
      });
      return response.data;
    } catch (error) {
      console.error('Error creating alias:', error);
      throw error;
    }
  },

  listAliases: async (search = '') => {
    try {
      const response = await api.get(API_ENDPOINTS.INGREDIENTS.ALIASES_LIST, {
        params: { search }
      });
      return response.data;
    } catch (error) {
      console.error('Error listing aliases:', error);
      throw error;
    }
  },

  // ========== SUGGESTION APIS ==========
  
// Get all ingredient suggestions (Admin only)
getAllSuggestions: async (params = {}) => {
  try {
    console.log('📤 [getAllSuggestions] ===== START =====');
    console.log('📤 [getAllSuggestions] Request params:', params);
    console.log('🔗 [getAllSuggestions] Endpoint:', API_ENDPOINTS.INGREDIENTS.SUGGESTIONS_ALL);
    
    const response = await api.get(API_ENDPOINTS.INGREDIENTS.SUGGESTIONS_ALL, { params });
    
    console.log('📥 [getAllSuggestions] Response status:', response.status);
    console.log('📥 [getAllSuggestions] Response data:', response.data);
    
    // ✅ Sửa: lấy đúng content từ data.data
    const content = response.data?.data?.content || response.data?.content || [];
    const totalRows = response.data?.data?.total_rows || response.data?.total_rows || 0;
    
    console.log('📥 [getAllSuggestions] Total suggestions:', totalRows);
    console.log('📥 [getAllSuggestions] Content length:', content.length);
    
    if (content.length > 0) {
      console.log('📥 [getAllSuggestions] First suggestion sample:', content[0]);
    }
    
    console.log('✅ [getAllSuggestions] ===== SUCCESS =====');
    return response.data;
  } catch (error) {
    console.error('❌ [getAllSuggestions] ===== ERROR =====');
    console.error('❌ [getAllSuggestions] Error message:', error.message);
    console.error('❌ [getAllSuggestions] Error response:', error.response?.data);
    throw error;
  }
},
  getMySuggestions: async (params = {}) => {
    try {
      const response = await api.get(API_ENDPOINTS.INGREDIENTS.SUGGESTIONS_ME, { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching my suggestions:', error);
      throw error;
    }
  },

  approveNewSuggestion: async (uid, resolutionNote = '') => {
    try {
      const response = await api.post(API_ENDPOINTS.INGREDIENTS.SUGGESTION_APPROVE_NEW(uid), {
        resolution_note: resolutionNote
      });
      return response.data;
    } catch (error) {
      console.error('Error approving new suggestion:', error);
      throw error;
    }
  },

  approveAliasSuggestion: async (uid, ingredientUid, resolutionNote = '') => {
    try {
      const response = await api.post(API_ENDPOINTS.INGREDIENTS.SUGGESTION_APPROVE_ALIAS(uid), {
        ingredient_uid: ingredientUid,
        resolution_note: resolutionNote
      });
      return response.data;
    } catch (error) {
      console.error('Error approving alias suggestion:', error);
      throw error;
    }
  },

  rejectSuggestion: async (uid, rejectionReason) => {
    try {
      const response = await api.post(API_ENDPOINTS.INGREDIENTS.SUGGESTION_REJECT(uid), {
        rejection_reason: rejectionReason
      });
      return response.data;
    } catch (error) {
      console.error('Error rejecting suggestion:', error);
      throw error;
    }
  },

  // ========== FAVOURITES & ALLERGIES APIS (Chef only) ==========
  
  getFavourites: async () => {
    try {
      const response = await api.get(API_ENDPOINTS.INGREDIENTS.FAVOURITES_LIST);
      return response.data;
    } catch (error) {
      console.error('Error fetching favourites:', error);
      throw error;
    }
  },

  addFavourite: async (ingredientUid) => {
    try {
      const response = await api.post(API_ENDPOINTS.INGREDIENTS.FAVOURITES_ADD, {
        ingredient_uid: ingredientUid
      });
      return response.data;
    } catch (error) {
      console.error('Error adding favourite:', error);
      throw error;
    }
  },

  removeFavourite: async (ingredientUid) => {
    try {
      const response = await api.delete(API_ENDPOINTS.INGREDIENTS.FAVOURITES_REMOVE(ingredientUid));
      return response.data;
    } catch (error) {
      console.error('Error removing favourite:', error);
      throw error;
    }
  },

  getAllergies: async () => {
    try {
      const response = await api.get(API_ENDPOINTS.INGREDIENTS.ALLERGIES_LIST);
      return response.data;
    } catch (error) {
      console.error('Error fetching allergies:', error);
      throw error;
    }
  },

  addAllergy: async (ingredientUid) => {
    try {
      const response = await api.post(API_ENDPOINTS.INGREDIENTS.ALLERGIES_ADD, {
        ingredient_uid: ingredientUid
      });
      return response.data;
    } catch (error) {
      console.error('Error adding allergy:', error);
      throw error;
    }
  },

  removeAllergy: async (ingredientUid) => {
    try {
      const response = await api.delete(API_ENDPOINTS.INGREDIENTS.ALLERGIES_REMOVE(ingredientUid));
      return response.data;
    } catch (error) {
      console.error('Error removing allergy:', error);
      throw error;
    }
  },

  // ========== DISH INGREDIENT APIS ==========
  
getDishIngredient: async (uid) => {
  try {
    console.log('📤 [getDishIngredient] Fetching dish ingredient:', uid);
    const response = await api.get(API_ENDPOINTS.INGREDIENTS.DISH_INGREDIENT_DETAIL(uid));
    console.log('📥 [getDishIngredient] Response:', response.data);
    console.log('📥 [getDishIngredient] Nutrition values:', {
      energy: response.data?.data?.energy || response.data?.energy,
      protein: response.data?.data?.protein || response.data?.protein,
      natri: response.data?.data?.natri || response.data?.natri,
      kali: response.data?.data?.kali || response.data?.kali
    });
    return response.data;
  } catch (error) {
    console.error('❌ [getDishIngredient] Error:', error.message);
    throw error;
  }
},

// ========== DISH INGREDIENT APIS ==========

// Update dish ingredient
updateDishIngredient: async (uid, data) => {
  try {
    console.log('📤 [updateDishIngredient] ===== START =====');
    console.log('📤 [updateDishIngredient] UID:', uid);
    console.log('📤 [updateDishIngredient] Update data:', JSON.stringify(data, null, 2));
    console.log('📤 [updateDishIngredient] Data keys:', Object.keys(data));
    console.log('🔗 [updateDishIngredient] Endpoint:', API_ENDPOINTS.INGREDIENTS.DISH_INGREDIENT_UPDATE(uid));
    
    // Log chi tiết các giá trị quan trọng
    console.log('📤 [updateDishIngredient] Weight:', data.weight);
    console.log('📤 [updateDishIngredient] Energy:', data.energy);
    console.log('📤 [updateDishIngredient] Protein:', data.protein);
    console.log('📤 [updateDishIngredient] Lipid:', data.lipid);
    console.log('📤 [updateDishIngredient] Carbohydrate:', data.carbohydrate);
    console.log('📤 [updateDishIngredient] Fiber:', data.fiber);
    console.log('📤 [updateDishIngredient] Natri:', data.natri);
    console.log('📤 [updateDishIngredient] Chili:', data.chili);
    console.log('📤 [updateDishIngredient] Ingredient UID:', data.ingredient_uid);
    console.log('📤 [updateDishIngredient] Custom name:', data.custom_name);
    console.log('📤 [updateDishIngredient] Source:', data.source);
    
    const response = await api.patch(API_ENDPOINTS.INGREDIENTS.DISH_INGREDIENT_UPDATE(uid), data);
    
    console.log('📥 [updateDishIngredient] Response status:', response.status);
    console.log('📥 [updateDishIngredient] Response data:', response.data);
    console.log('📥 [updateDishIngredient] Response message:', response.data?.message);
    console.log('📥 [updateDishIngredient] Response message_code:', response.data?.message_code);
    
    if (response.data?.message_code === 'VALIDATION_ERROR') {
      console.error('❌ Validation error details:', response.data?.data);
    }
    
    // Log response data chi tiết
    if (response.data?.data) {
      console.log('📥 [updateDishIngredient] Response dish_ingredient_uid:', response.data.data.dish_ingredient_uid);
      console.log('📥 [updateDishIngredient] Response confidence:', response.data.data.confidence);
      console.log('📥 [updateDishIngredient] Response warnings:', response.data.data.warnings);
    }
    
    console.log('✅ [updateDishIngredient] ===== SUCCESS =====');
    return response.data;
  } catch (error) {
    console.error('❌ [updateDishIngredient] ===== ERROR =====');
    console.error('❌ [updateDishIngredient] Error message:', error.message);
    console.error('❌ [updateDishIngredient] Error response:', error.response?.data);
    console.error('❌ [updateDishIngredient] Error status:', error.response?.status);
    console.error('❌ [updateDishIngredient] Error status text:', error.response?.statusText);
    
    // Log chi tiết error response nếu có
    if (error.response?.data) {
      console.error('❌ [updateDishIngredient] Error message_code:', error.response.data.message_code);
      console.error('❌ [updateDishIngredient] Error details:', error.response.data.data);
    }
    
    throw error;
  }
},

// Soft delete dish ingredient
softDeleteDishIngredient: async (uid) => {
  try {
    console.log('📤 [softDeleteDishIngredient] ===== START =====');
    console.log('📤 [softDeleteDishIngredient] UID:', uid);
    console.log('🔗 [softDeleteDishIngredient] Endpoint:', API_ENDPOINTS.INGREDIENTS.DISH_INGREDIENT_SOFT_DELETE(uid));
    
    const response = await api.patch(API_ENDPOINTS.INGREDIENTS.DISH_INGREDIENT_SOFT_DELETE(uid));
    
    console.log('📥 [softDeleteDishIngredient] Response status:', response.status);
    console.log('📥 [softDeleteDishIngredient] Response data:', response.data);
    console.log('✅ [softDeleteDishIngredient] ===== SUCCESS =====');
    return response.data;
  } catch (error) {
    console.error('❌ [softDeleteDishIngredient] ===== ERROR =====');
    console.error('❌ [softDeleteDishIngredient] Error message:', error.message);
    console.error('❌ [softDeleteDishIngredient] Error response:', error.response?.data);
    console.error('❌ [softDeleteDishIngredient] Error status:', error.response?.status);
    throw error;
  }
},

// Preview ingredient before adding to dish (Chef only)
// ingredientService.js
previewIngredientForDish: async (dishUid, data) => {
  try {
    console.log('📤 [previewIngredientForDish] dishUid:', dishUid);
    console.log('📤 [previewIngredientForDish] data:', data);
    
    const response = await api.post(API_ENDPOINTS.INGREDIENTS.DISH_PREVIEW_INGREDIENT(dishUid), data);
    
    console.log('📥 [previewIngredientForDish] Response:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Error previewing ingredient:', error);
    throw error;
  }
},

  addIngredientToDish: async (dishUid, data) => {
    try {
      const response = await api.post(API_ENDPOINTS.INGREDIENTS.DISH_ADD_INGREDIENT(dishUid), data);
      return response.data;
    } catch (error) {
      console.error('Error adding ingredient to dish:', error);
      throw error;
    }
  },

  previewSuggestIngredient: async (dishUid, data) => {
    try {
      const response = await api.post(API_ENDPOINTS.INGREDIENTS.DISH_PREVIEW_SUGGESTION(dishUid), data);
      return response.data;
    } catch (error) {
      console.error('Error previewing suggestion:', error);
      throw error;
    }
  },

  suggestIngredientForDish: async (dishUid, data) => {
    try {
      const response = await api.post(API_ENDPOINTS.INGREDIENTS.DISH_SUGGEST_INGREDIENT(dishUid), data);
      return response.data;
    } catch (error) {
      console.error('Error suggesting ingredient:', error);
      throw error;
    }
  },
  // Get all ingredients of dish for chefs
getDishIngredientsForChef: async (dishUid) => {
  try {
    console.log('📤 [getDishIngredientsForChef] Fetching ingredients for dish:', dishUid);
    const response = await api.get(API_ENDPOINTS.DISHES.INGREDIENTS_CHEF(dishUid));
    console.log('📥 [getDishIngredientsForChef] Response:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Error fetching dish ingredients:', error);
    throw error;
  }
},
};

export default ingredientService;