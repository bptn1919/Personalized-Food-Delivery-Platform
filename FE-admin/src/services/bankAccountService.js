// services/bankAccountService.js
import api from './api';
import { API_ENDPOINTS } from '../utils/constants';

export const bankAccountService = {
  // ========== CUSTOMER BANK ACCOUNTS ==========
  
  // Get all customer bank accounts with filters
  getCustomerBankAccounts: async (params = {}) => {
    try {
      console.log('📤 [getCustomerBankAccounts] Request params:', params);
      const response = await api.get(API_ENDPOINTS.ADMIN.BANK_ACCOUNTS.CUSTOMERS, { params });
      
      console.log('📥 [getCustomerBankAccounts] Response status:', response.status);
      console.log('📥 [getCustomerBankAccounts] Response data:', response.data);
      
      if (response.data?.data) {
        return response.data.data;
      }
      
      return response.data;
    } catch (error) {
      console.error('❌ [getCustomerBankAccounts] Error:', error);
      throw error;
    }
  },

  // Verify customer bank account
  verifyCustomerBankAccount: async (bankAccountId, status) => {
    try {
      console.log('📤 [verifyCustomerBankAccount] ID:', bankAccountId, 'Status:', status);
      const response = await api.patch(
        API_ENDPOINTS.ADMIN.BANK_ACCOUNTS.CUSTOMER_VERIFY(bankAccountId), 
        { status }
      );
      
      console.log('📥 [verifyCustomerBankAccount] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [verifyCustomerBankAccount] Error:', error);
      throw error;
    }
  },

  // ========== CHEF BANK ACCOUNTS ==========
  
  // Get all chef bank accounts with filters
  getChefBankAccounts: async (params = {}) => {
    try {
      console.log('📤 [getChefBankAccounts] Request params:', params);
      const response = await api.get(API_ENDPOINTS.ADMIN.BANK_ACCOUNTS.CHEFS, { params });
      
      console.log('📥 [getChefBankAccounts] Response status:', response.status);
      console.log('📥 [getChefBankAccounts] Response data:', response.data);
      
      if (response.data?.data) {
        return response.data.data;
      }
      
      return response.data;
    } catch (error) {
      console.error('❌ [getChefBankAccounts] Error:', error);
      throw error;
    }
  },

  // Verify chef bank account
  verifyChefBankAccount: async (bankAccountId, status) => {
    try {
      console.log('📤 [verifyChefBankAccount] ID:', bankAccountId, 'Status:', status);
      const response = await api.patch(
        API_ENDPOINTS.ADMIN.BANK_ACCOUNTS.CHEF_VERIFY(bankAccountId), 
        { status }
      );
      
      console.log('📥 [verifyChefBankAccount] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [verifyChefBankAccount] Error:', error);
      throw error;
    }
  },
};