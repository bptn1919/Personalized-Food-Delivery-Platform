// ==================== API ENDPOINTS ====================
export const API_ENDPOINTS = {
  // Auth
  AUTH: {
    LOGIN: '/api/auth/login',
    LOGOUT: '/api/auth/logout',
    CHANGE_PASSWORD: '/api/auth/password/change',
    FORGOT_PASSWORD: '/api/auth/password/forget',
    VERIFY_OTP: '/api/auth/verify-otp',
    RESET_PASSWORD: '/api/auth/password/reset',
    REQUEST_EMAIL_CHANGE: '/api/auth/email-change/request',
    VERIFY_EMAIL_CHANGE: '/api/auth/email-change/verify',
    REFRESH_TOKEN: '/api/auth/refresh',
  },
  
  // Users
  USERS: {
    LIST: '/api/admin/users',
    DEACTIVATE: (id) => `/api/admin/users/${id}/deactivate`,
    ACTIVATE: (id) => `/api/admin/users/${id}/activate`,
  },
  
  // Dashboard
  DASHBOARD: {
    OVERVIEW: '/api/admin/dashboard/overview',
    REVENUE_CHART: '/api/admin/dashboard/revenue-chart',
    PAYMENT_METHODS: '/api/admin/dashboard/payment-methods',
    ORDER_STATUS: '/api/admin/dashboard/order-status',
    TOP_CHEFS: '/api/admin/dashboard/top-chefs',
    TOP_DISHES: '/api/dishes/top',
    SUCCESS_ORDERS_BY_DISTRICT: '/api/admin/dashboard/success-orders-by-district',
  },
  
  // Orders
  ORDERS: {
    LIST: '/api/admin/orders',
    DETAIL: (id) => `/api/admin/orders/${id}`,
  },
  
  // Vouchers
  VOUCHERS: {
    LIST: '/api/admin/voucher',
    CREATE: '/api/admin/voucher',
    DETAIL: (uid) => `/api/admin/voucher/${uid}`,
    UPDATE: (uid) => `/api/vouchers/${uid}`,
    DELETE: (uid) => `/api/vouchers/${uid}`,
    TOGGLE_STATUS: (uid) => `/api/admin/voucher/${uid}/status`,
  },
  
  // Certificates
  CERTIFICATES: {
    CREATE: '/api/certificates/',
    MY_LIST: '/api/certificates/',
    DETAIL: (uid) => `/api/certificates/${uid}`,
    UPDATE: (uid) => `/api/certificates/${uid}/`,
    SOFT_DELETE: (uid) => `/api/certificates/${uid}/deleted`,
    RESTORE: (uid) => `/api/certificates/${uid}/restored`,
    ADMIN_LIST: '/api/certificates/all',
    ADMIN_SET_STATUS: (uid) => `/api/certificates/${uid}/status`,
  },
  
  // Attachments
  ATTACHMENTS: {
    PRESIGNED_URL: '/api/attachments/presigned-url',
    COMPLETE: (uid) => `/api/attachments/${uid}/completed`,
    COMPLETE_WITH_INSTANCE: (uid, instance) => `/api/attachments/${uid}/completed/${instance}`,
  },

  // Dish Locations
  DISH_LOCATIONS: {
    CREATE: '/api/dish-locations/',
    LIST: '/api/dish-locations/',
    TREE: '/api/dish-locations/tree',
    DETAIL: (id) => `/api/dish-locations/${id}`,
    UPDATE: (id) => `/api/dish-locations/${id}`,
    DELETE: (id) => `/api/dish-locations/${id}`,
  },

  // Ingredients
// Ingredients - Gom tất cả API liên quan đến ingredient
INGREDIENTS: {
  // CRUD
  CREATE: '/api/ingredients/',
  LIST: '/api/ingredients/',
  DETAIL: (uid) => `/api/ingredients/${uid}`,
  UPDATE: (uid) => `/api/ingredients/${uid}`,
  SOFT_DELETE: (uid) => `/api/ingredients/${uid}/deleted`,
  RESTORE: (uid) => `/api/ingredients/${uid}/restored`,
  HARD_DELETE: (uid) => `/api/ingredients/${uid}`,
  
  // Import/Export
  EXPORT_TEMPLATE: '/api/ingredients/export-template',
  IMPORT_EXCEL: '/api/ingredients/import-excel',
  
  // Search
  SEARCH: '/api/ingredients/search',
  AUTOCOMPLETE: '/api/ingredients/autocomplete',
  
  // Alias
  ALIASES_LIST: '/api/ingredients/aliases',
  ALIASES_CREATE: '/api/ingredients/aliases',
  
  // Suggestions
  SUGGESTIONS_ALL: '/api/ingredients/suggestions/all',
  SUGGESTIONS_ME: '/api/ingredients/suggestions/me',
  SUGGESTION_APPROVE_NEW: (uid) => `/api/ingredients/suggestions/${uid}/approve-new`,
  SUGGESTION_APPROVE_ALIAS: (uid) => `/api/ingredients/suggestions/${uid}/approve-alias`,
  SUGGESTION_REJECT: (uid) => `/api/ingredients/suggestions/${uid}/reject`,
  
  // Favourites & Allergies (Chef)
  FAVOURITES_LIST: '/api/ingredients/me/favourites',
  FAVOURITES_ADD: '/api/ingredients/me/favourites',
  FAVOURITES_REMOVE: (uid) => `/api/ingredients/me/favourites/${uid}`,
  ALLERGIES_LIST: '/api/ingredients/me/allergies',
  ALLERGIES_ADD: '/api/ingredients/me/allergies',
  ALLERGIES_REMOVE: (uid) => `/api/ingredients/me/allergies/${uid}`,
  
  // Dish Ingredient Actions (gộp vào đây luôn)
  DISH_INGREDIENT_DETAIL: (uid) => `/api/dishingredients/${uid}`,
  DISH_INGREDIENT_UPDATE: (uid) => `/api/dishingredients/${uid}`,
  DISH_INGREDIENT_SOFT_DELETE: (uid) => `/api/dishingredients/${uid}/soft-deleted`,
  DISH_PREVIEW_INGREDIENT: (dishUid) => `/api/dishes/${dishUid}/ingredients/preview`,
  DISH_ADD_INGREDIENT: (dishUid) => `/api/dishes/${dishUid}/ingredients`,
  DISH_PREVIEW_SUGGESTION: (dishUid) => `/api/dishes/${dishUid}/ingredients/suggestion/preview`,
  DISH_SUGGEST_INGREDIENT: (dishUid) => `/api/dishes/${dishUid}/ingredients/suggestion`,
  DISH_AVAILABILITY_CREATE: (dishUid) => `/api/dishes/${dishUid}/availabilities`,

  
},

  // Certificate Attachments
  CERTIFICATE_ATTACHMENTS: {
    ADD: (uid) => `/api/certificates/${uid}/attachments/`,
    REMOVE: (uid, attachmentUid) => `/api/certificates/${uid}/attachments/${attachmentUid}`,
    REORDER: (uid) => `/api/certificates/${uid}/attachments/reorder`,
  },


  
  // Dishes
  DISHES: {
    CREATE: '/api/dishes/',
    LIST: '/api/dishes/',
    DETAIL: (uid) => `/api/dishes/${uid}`,
    UPDATE: (uid) => `/api/dishes/${uid}`,
    SOFT_DELETE: (uid) => `/api/dishes/${uid}/deleted`,
    RESTORE: (uid) => `/api/dishes/${uid}/restored`,
    HARD_DELETE: (uid) => `/api/dishes/${uid}`,
    AVAILABILITIES: (uid) => `/api/dishes/${uid}/availabilities`,
    AVAILABILITY_CREATE: (uid) => `/api/dishes/${uid}/availabilities`,
    INGREDIENTS_CHEF: (uid) => `/api/dishes/${uid}/ingredients/chef`,
    MINE: `/api/dishes/mine`,
  },
  
  // Menus
  MENUS: {
    MY_LIST: '/api/menus/mine',
    BY_CHEF: (chefId) => `/api/menus/chef/${chefId}`,
    GET_BY_UID: (uid) => `/api/menus/${uid}`,
    CREATE: '/api/menus',
    UPDATE: (uid) => `/api/menus/${uid}`,
    SOFT_DELETE: (uid) => `/api/menus/${uid}/deleted`,
    RESTORE: (uid) => `/api/menus/${uid}/restore`,
    HARD_DELETE: (uid) => `/api/menus/${uid}`,
    ACTIVATE: (uid) => `/api/menus/${uid}/activate`,
    DEACTIVATE: (uid) => `/api/menus/${uid}/deactivate`,
    DISHES_PUBLIC: (uid) => `/api/menus/${uid}/dishes`,
    DISHES_ALL: (uid) => `/api/menus/${uid}/all-dishes`,
    ADD_DISH: (uid) => `/api/menus/${uid}/add-dish/`,
    ACTIVATE_DISH: (uid, dishUid) => `/api/menus/${uid}/dishes/${dishUid}/activate`,
    DEACTIVATE_DISH: (uid, dishUid) => `/api/menus/${uid}/dishes/${dishUid}/deactivate`,
  },
    // Admin Bank Accounts
  ADMIN: {
    BANK_ACCOUNTS: {
      CUSTOMERS: '/api/admin/bank-accounts/customers',
      CHEFS: '/api/admin/bank-accounts/chefs',
      CUSTOMER_VERIFY: (id) => `/api/admin/bank-accounts/customers/${id}/verification`,
      CHEF_VERIFY: (id) => `/api/admin/bank-accounts/chefs/${id}/verification`,
    },
  },
};


// ==================== USER ====================
export const USER_TYPES = {
  CUSTOMER: 'CUSTOMER',
  CHEF: 'CHEF',
};

export const USER_TYPE_LABELS = {
  [USER_TYPES.CUSTOMER]: 'Customer',
  [USER_TYPES.CHEF]: 'Chef',
};

export const USER_STATUS = {
  ACTIVE: true,
  INACTIVE: false,
};

export const USER_STATUS_LABELS = {
  [USER_STATUS.ACTIVE]: 'Active',
  [USER_STATUS.INACTIVE]: 'Inactive',
};

export const USER_STATUS_COLORS = {
  [USER_STATUS.ACTIVE]: 'success',
  [USER_STATUS.INACTIVE]: 'error',
};


// ==================== ORDER ====================
export const ORDER_STATUS = {
  DRAFT: 'DRAFT',
  PENDING: 'PENDING',
  CONFIRMED_SYSTEM: 'CONFIRMED_SYSTEM',
  CONFIRMED_SHOP: 'CONFIRMED_SHOP',
  PROCESSING: 'PROCESSING',
  DELIVERING: 'DELIVERING',
  COMPLETED: 'COMPLETED',
  CANCELLED: 'CANCELLED',
};

export const ORDER_STATUS_LABELS = {
  [ORDER_STATUS.DRAFT]: 'Draft',
  [ORDER_STATUS.PENDING]: 'Pending',
  [ORDER_STATUS.CONFIRMED_SYSTEM]: 'Confirmed (System)',
  [ORDER_STATUS.CONFIRMED_SHOP]: 'Confirmed (Shop)',
  [ORDER_STATUS.PROCESSING]: 'Processing',
  [ORDER_STATUS.DELIVERING]: 'Delivering',
  [ORDER_STATUS.COMPLETED]: 'Completed',
  [ORDER_STATUS.CANCELLED]: 'Cancelled',
};

export const ORDER_STATUS_COLORS = {
  [ORDER_STATUS.DRAFT]: 'default',
  [ORDER_STATUS.PENDING]: 'warning',
  [ORDER_STATUS.CONFIRMED_SYSTEM]: 'info',
  [ORDER_STATUS.CONFIRMED_SHOP]: 'info',
  [ORDER_STATUS.PROCESSING]: 'primary',
  [ORDER_STATUS.DELIVERING]: 'primary',
  [ORDER_STATUS.COMPLETED]: 'success',
  [ORDER_STATUS.CANCELLED]: 'error',
};


// ==================== VOUCHER ====================
export const VOUCHER_TYPES = {
  SHOP_VOUCHER: 'SHOP_VOUCHER',
  PLATFORM_SUBTOTAL: 'PLATFORM_SUBTOTAL',
  PLATFORM_SHIPPING: 'PLATFORM_SHIPPING',
};

export const VOUCHER_TYPE_LABELS = {
  [VOUCHER_TYPES.SHOP_VOUCHER]: 'Shop Voucher',
  [VOUCHER_TYPES.PLATFORM_SUBTOTAL]: 'Platform Subtotal',
  [VOUCHER_TYPES.PLATFORM_SHIPPING]: 'Platform Shipping',
};

export const DISCOUNT_TYPES = {
  PERCENTAGE: 'PERCENTAGE',
  FIXED_AMOUNT: 'FIXED_AMOUNT',
};

export const DISCOUNT_TYPE_LABELS = {
  [DISCOUNT_TYPES.PERCENTAGE]: 'Percentage (%)',
  [DISCOUNT_TYPES.FIXED_AMOUNT]: 'Fixed Amount (VND)',
};


// ==================== CERTIFICATE ====================
export const CERTIFICATE_STATUS = {
  PENDING: 'PENDING',
  ACTIVE: 'ACTIVE',
  EXPIRED: 'EXPIRED',
  REVOKED: 'REVOKED',
};

export const CERTIFICATE_STATUS_LABELS = {
  [CERTIFICATE_STATUS.PENDING]: 'Pending',
  [CERTIFICATE_STATUS.ACTIVE]: 'Active',
  [CERTIFICATE_STATUS.EXPIRED]: 'Expired',
  [CERTIFICATE_STATUS.REVOKED]: 'Revoked',
};

export const CERTIFICATE_STATUS_COLORS = {
  [CERTIFICATE_STATUS.PENDING]: 'warning',
  [CERTIFICATE_STATUS.ACTIVE]: 'success',
  [CERTIFICATE_STATUS.EXPIRED]: 'default',
  [CERTIFICATE_STATUS.REVOKED]: 'error',
};

export const CERTIFICATE_TYPES = {
  FOOD_SAFETY: 'FOOD_SAFETY',
  BUSINESS_LICENSE: 'BUSINESS_LICENSE',
};

export const CERTIFICATE_TYPE_LABELS = {
  [CERTIFICATE_TYPES.FOOD_SAFETY]: 'Food Safety',
  [CERTIFICATE_TYPES.BUSINESS_LICENSE]: 'Business License',
};


// ==================== DISH ====================
export const DISH_CATEGORIES = {
  FOOD: 'FOOD',
  BEVERAGES: 'BEVERAGES',
  DESSERT: 'DESSERT',
};

export const DISH_CATEGORY_LABELS = {
  [DISH_CATEGORIES.FOOD]: 'Food',
  [DISH_CATEGORIES.BEVERAGES]: 'Beverages',
  [DISH_CATEGORIES.DESSERT]: 'Dessert',
};

export const DISH_STATUS = {
  AVAILABLE: 'AVAILABLE',
  UNAVAILABLE: 'UNAVAILABLE',
};

export const DISH_STATUS_LABELS = {
  [DISH_STATUS.AVAILABLE]: 'Available',
  [DISH_STATUS.UNAVAILABLE]: 'Unavailable',
};


// ==================== MENU ====================
export const MENU_STATUS = {
  ACTIVE: 'ACTIVE',
  INACTIVE: 'INACTIVE',
  DRAFT: 'DRAFT',
};

export const MENU_STATUS_LABELS = {
  [MENU_STATUS.ACTIVE]: 'Active',
  [MENU_STATUS.INACTIVE]: 'Inactive',
  [MENU_STATUS.DRAFT]: 'Draft',
};


// ==================== ATTACHMENT ====================
export const ATTACHMENT_TYPES = {
  FOOD: 'FOOD',
  DISH: 'DISH',
  CERTIFICATE: 'CERTIFICATE',
  CHEF_AVATAR: 'CHEF_AVATAR',
  CUSTOMER_AVATAR: 'CUSTOMER_AVATAR',
  REVIEW: 'REVIEW',
  OTHER: 'OTHER',
};


// ==================== COMMON ====================
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  SERVER_ERROR: 500,
};

export const DEFAULT_PAGE_SIZE = 10;
export const DEFAULT_PAGE = 1;
export const PASSWORD_MIN_LENGTH = 8;

export const ERROR_MESSAGES = {
  PASSWORD_INCORRECT: 'Password incorrect',
  PERMISSION_DENIED: "You don't have permission to perform this action",
};

export const DISH_LOCATION_TYPES = {
  REGION: 'REGION',
  SUBREGION: 'SUBREGION',
  COUNTRY: 'COUNTRY',
};

export const DISH_LOCATION_TYPE_LABELS = {
  [DISH_LOCATION_TYPES.REGION]: 'Region',
  [DISH_LOCATION_TYPES.SUBREGION]: 'Subregion',
  [DISH_LOCATION_TYPES.COUNTRY]: 'Country',
};

