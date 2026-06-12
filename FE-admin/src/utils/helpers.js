/**
 * Format date string to localized format
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date or 'N/A'
 */
export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(dateString));
};

/**
 * Format phone number to Vietnamese format (xxxx xxx xxx)
 * @param {string} phone - Raw phone number
 * @returns {string} Formatted phone number
 */
export const formatPhoneNumber = (phone) => {
  if (!phone) return '';
  const cleaned = phone.replace(/\D/g, '');
  const match = cleaned.match(/^(\d{4})(\d{3})(\d{3})$/);
  return match ? `${match[1]} ${match[2]} ${match[3]}` : phone;
};

/**
 * Format user's full name from first_name, last_name, username
 * @param {Object} user - User object
 * @returns {string} Formatted full name
 */
export const formatFullName = (user) => {
  if (!user) return '';
  const { first_name, last_name, username } = user;
  if (first_name && last_name) return `${first_name} ${last_name}`;
  if (first_name) return first_name;
  if (last_name) return last_name;
  return username || 'N/A';
};

/**
 * Format currency to VND
 * @param {number} amount - Amount in VND
 * @returns {string} Formatted currency
 */
export const formatCurrency = (amount) => {
  if (amount === undefined || amount === null) return '0₫';
  return new Intl.NumberFormat('vi-VN', { 
    style: 'currency', 
    currency: 'VND',
    minimumFractionDigits: 0
  }).format(amount);
};

/**
 * Handle API error responses
 * @param {Error} error - Axios error object
 * @returns {Object} Standardized error object
 */
export const handleApiError = (error) => {
  if (error.response) {
    return {
      status: error.response.status,
      message: error.response.data?.message || 'An error occurred from server',
      message_code: error.response.data?.message_code || 'UNKNOWN_ERROR',
      errors: error.response.data?.errors || {}
    };
  }
  if (error.request) {
    return {
      status: 503,
      message: 'Cannot connect to server',
      message_code: 'CONNECTION_ERROR',
      errors: {}
    };
  }
  return {
    status: 500,
    message: error.message || 'An error occurred',
    message_code: 'CLIENT_ERROR',
    errors: {}
  };
};

/**
 * Build query string from object
 * @param {Object} params - Query parameters
 * @returns {string} URL query string
 */
export const buildQueryString = (params) => {
  const queryParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      queryParams.append(key, value);
    }
  });
  return queryParams.toString();
};

/**
 * Debounce function for search inputs
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export const debounce = (func, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
};