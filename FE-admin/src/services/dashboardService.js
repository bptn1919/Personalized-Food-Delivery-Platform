import api from './api';
import { API_ENDPOINTS } from '../utils/constants';

export const dashboardService = {
  // Get dashboard overview stats
  getOverview: async () => {
    try {
      console.log('📤 [getOverview] Requesting dashboard overview stats');
      console.log('📤 [getOverview] URL:', API_ENDPOINTS.DASHBOARD.OVERVIEW);

      const response = await api.get(API_ENDPOINTS.DASHBOARD.OVERVIEW);

      console.log('📥 [getOverview] Response status:', response.status);
      console.log('📥 [getOverview] Response data:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [getOverview] Error:', error);
      console.error('❌ [getOverview] Error response:', error.response?.data);
      throw error;
    }
  },

  // Get revenue chart data
  getRevenueChart: async (fromDate, toDate) => {
    try {
      console.log(`📤 [getRevenueChart] Requesting revenue chart from ${fromDate} to ${toDate}`);
      console.log('📤 [getRevenueChart] URL:', API_ENDPOINTS.DASHBOARD.REVENUE_CHART);

      const params = {
        from_date: fromDate,
        to_date: toDate
      };
      const response = await api.get(API_ENDPOINTS.DASHBOARD.REVENUE_CHART, { params });

      console.log('📥 [getRevenueChart] Response status:', response.status);
      console.log('📥 [getRevenueChart] Response data length:', response.data?.data?.data?.length || response.data?.data?.length || 0);
      return response.data;
    } catch (error) {
      console.error('❌ [getRevenueChart] Error:', error);
      console.error('❌ [getRevenueChart] Error response:', error.response?.data);
      throw error;
    }
  },

  // Get revenue chart for last 30 days
  getLast30DaysRevenue: async () => {
    try {
      console.log('📤 [getLast30DaysRevenue] Fetching last 30 days revenue');
      const toDate = new Date();
      const fromDate = new Date();
      fromDate.setDate(fromDate.getDate() - 30);
      
      const formatDate = (date) => {
        return date.toISOString().split('T')[0];
      };

      const result = await dashboardService.getRevenueChart(
        formatDate(fromDate),
        formatDate(toDate)
      );
      console.log('📥 [getLast30DaysRevenue] Successfully retrieved revenue chart data');
      return result;
    } catch (error) {
      console.error('❌ [getLast30DaysRevenue] Error:', error);
      throw error;
    }
  },

  // Get revenue chart for custom date range
  getCustomRangeRevenue: async (fromDate, toDate) => {
    try {
      console.log(`📤 [getCustomRangeRevenue] Fetching custom range revenue from ${fromDate} to ${toDate}`);
      const result = await dashboardService.getRevenueChart(fromDate, toDate);
      console.log('📥 [getCustomRangeRevenue] Successfully retrieved custom range revenue chart data');
      return result;
    } catch (error) {
      console.error('❌ [getCustomRangeRevenue] Error:', error);
      throw error;
    }
  },

  // Get payment method distribution stats
  getPaymentMethodDistribution: async () => {
    try {
      console.log('📤 [getPaymentMethodDistribution] Requesting payment method stats');
      console.log('📤 [getPaymentMethodDistribution] URL:', API_ENDPOINTS.DASHBOARD.PAYMENT_METHODS);
      
      const response = await api.get(API_ENDPOINTS.DASHBOARD.PAYMENT_METHODS);
      
      console.log('📥 [getPaymentMethodDistribution] Response status:', response.status);
      console.log('📥 [getPaymentMethodDistribution] Response data:', response.data);
      console.log('📥 [getPaymentMethodDistribution] Total orders:', response.data?.total_orders);
      console.log('📥 [getPaymentMethodDistribution] Payment data:', response.data?.data);
      
      return response.data;
    } catch (error) {
      console.error('❌ [getPaymentMethodDistribution] Error:', error);
      console.error('❌ [getPaymentMethodDistribution] Error response:', error.response?.data);
      throw error;
    }
  },

  // Get order status distribution stats
  getOrderStatusDistribution: async () => {
    try {
      console.log('📤 [getOrderStatusDistribution] Requesting order status distribution stats');
      console.log('📤 [getOrderStatusDistribution] URL:', API_ENDPOINTS.DASHBOARD.ORDER_STATUS);

      const response = await api.get(API_ENDPOINTS.DASHBOARD.ORDER_STATUS);

      console.log('📥 [getOrderStatusDistribution] Response status:', response.status);
      console.log('📥 [getOrderStatusDistribution] Response data:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [getOrderStatusDistribution] Error:', error);
      console.error('❌ [getOrderStatusDistribution] Error response:', error.response?.data);
      throw error;
    }
  },

  // Get top chefs
  getTopChefs: async (limit = 5) => {
    try {
      console.log(`📤 [getTopChefs] Requesting top ${limit} chefs`);
      console.log('📤 [getTopChefs] URL:', API_ENDPOINTS.DASHBOARD.TOP_CHEFS);

      const params = { limit };
      const response = await api.get(API_ENDPOINTS.DASHBOARD.TOP_CHEFS, { params });

      console.log('📥 [getTopChefs] Response status:', response.status);
      console.log('📥 [getTopChefs] Response data:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [getTopChefs] Error:', error);
      console.error('❌ [getTopChefs] Error response:', error.response?.data);
      throw error;
    }
  },

  // Get top dishes
  getTopDishes: async (limit = 10) => {
    try {
      console.log(`📤 [getTopDishes] Requesting top ${limit} dishes`);
      console.log('📤 [getTopDishes] URL:', API_ENDPOINTS.DASHBOARD.TOP_DISHES);

      const params = { limit };
      const response = await api.get(API_ENDPOINTS.DASHBOARD.TOP_DISHES, { params });

      console.log('📥 [getTopDishes] Response status:', response.status);
      console.log('📥 [getTopDishes] Response data:', response.data);
      return response.data; 
    } catch (error) {
      console.error('❌ [getTopDishes] Error:', error);
      console.error('❌ [getTopDishes] Error response:', error.response?.data);
      throw error;
    }
  },

  // Get success orders by district
  getSuccessOrdersByDistrict: async (fromDate, toDate) => {
    try {
      console.log(`📤 [getSuccessOrdersByDistrict] Requesting success orders by district from ${fromDate} to ${toDate}`);
      console.log('📤 [getSuccessOrdersByDistrict] URL:', API_ENDPOINTS.DASHBOARD.SUCCESS_ORDERS_BY_DISTRICT);

      const params = {};
      if (fromDate) params.from_date = fromDate;
      if (toDate) params.to_date = toDate;
      
      const response = await api.get(API_ENDPOINTS.DASHBOARD.SUCCESS_ORDERS_BY_DISTRICT, { params });

      console.log('📥 [getSuccessOrdersByDistrict] Response status:', response.status);
      console.log('📥 [getSuccessOrdersByDistrict] Response data:', response.data);
      return response.data; 
    } catch (error) {
      console.error('❌ [getSuccessOrdersByDistrict] Error:', error);
      console.error('❌ [getSuccessOrdersByDistrict] Error response:', error.response?.data);
      throw error;
    }
  },

  // Get success orders by district for last 30 days
  getLast30DaysSuccessOrdersByDistrict: async () => {
    try {
      console.log('📤 [getLast30DaysSuccessOrdersByDistrict] Fetching last 30 days success orders by district');
      const toDate = new Date();
      const fromDate = new Date();
      fromDate.setDate(fromDate.getDate() - 30);
      
      const formatDate = (date) => {
        return date.toISOString().split('T')[0];
      };

      const result = await dashboardService.getSuccessOrdersByDistrict(
        formatDate(fromDate),
        formatDate(toDate)
      );
      console.log('📥 [getLast30DaysSuccessOrdersByDistrict] Successfully retrieved success orders by district');
      return result;
    } catch (error) {
      console.error('❌ [getLast30DaysSuccessOrdersByDistrict] Error:', error);
      throw error;
    }
  },
};