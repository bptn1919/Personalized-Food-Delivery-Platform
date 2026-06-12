import api from './api';

const cleanVoucherData = (voucherData) => {
  const cleaned = { ...voucherData };
  
  // Convert empty strings to null for optional fields
  if (cleaned.max_discount_amount === '') {
    cleaned.max_discount_amount = null;
  }
  if (cleaned.usage_limit === '') {
    cleaned.usage_limit = null;
  }
  if (cleaned.description === '') {
    cleaned.description = null;
  }
  
  // Make sure numeric values are numbers/decimals
  if (cleaned.discount_value !== undefined && cleaned.discount_value !== null) {
    cleaned.discount_value = parseFloat(cleaned.discount_value);
  }
  if (cleaned.min_order_amount !== undefined && cleaned.min_order_amount !== null) {
    cleaned.min_order_amount = parseFloat(cleaned.min_order_amount);
  }
  if (cleaned.max_discount_amount !== undefined && cleaned.max_discount_amount !== null) {
    cleaned.max_discount_amount = parseFloat(cleaned.max_discount_amount);
  }
  if (cleaned.usage_limit !== undefined && cleaned.usage_limit !== null) {
    cleaned.usage_limit = parseInt(cleaned.usage_limit, 10);
  }
  if (cleaned.usage_limit_per_user !== undefined && cleaned.usage_limit_per_user !== null) {
    cleaned.usage_limit_per_user = parseInt(cleaned.usage_limit_per_user, 10);
  }
  
  return cleaned;
};

export const voucherService = {
  // Create new voucher
  createVoucher: async (voucherData) => {
    try {
      const cleanedData = cleanVoucherData(voucherData);
      const response = await api.post('/api/admin/voucher', cleanedData);
      return response.data;
    } catch (error) {
      console.error('Error creating voucher:', error);
      throw error;
    }
  },

  // Get all vouchers
  getVouchers: async () => {
    try {
      const response = await api.get('/api/admin/voucher');
      return response.data; 
    } catch (error) {
      console.error('Error fetching vouchers:', error);
      throw error;
    }
  },

  // Update voucher (Platform vouchers created by Admin are owned by Admin)
  updateVoucher: async (voucherUid, voucherData) => {
    try {
      const cleanedData = cleanVoucherData(voucherData);
      const response = await api.patch(`/api/vouchers/${voucherUid}`, cleanedData);
      return response.data;
    } catch (error) {
      console.error('Error updating voucher:', error);
      throw error;
    }
  },

  // Delete voucher (Platform vouchers created by Admin are owned by Admin)
  deleteVoucher: async (voucherUid) => {
    try {
      const response = await api.delete(`/api/vouchers/${voucherUid}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting voucher:', error);
      throw error;
    }
  }
};