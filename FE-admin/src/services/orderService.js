import api from './api';

export const orderService = {
  // Get orders list
  getOrders: async (params = {}) => {
    try {
      const response = await api.get('/api/admin/orders', { params });

      let ordersData = response.data;

      if (ordersData.data && ordersData.data.content) {
        return ordersData.data;
      }

      if (ordersData.content) {
        return ordersData;
      }

      return { content: [], total_rows: 0, total_pages: 0 };
    } catch (error) {
      throw error;
    }
  },

  // Get order detail by UID
  getOrderDetail: async (orderUid) => {
    try {
      console.log('📤 [getOrderDetail] Fetching order detail for UID:', orderUid);
      console.log('🔗 [getOrderDetail] Endpoint:', `/api/admin/orders/${orderUid}`);
      
      const response = await api.get(`/api/admin/orders/${orderUid}`);
      
      console.log('📥 [getOrderDetail] Response status:', response.status);
      console.log('📥 [getOrderDetail] Response data:', response.data);
      
      return response.data;
    } catch (error) {
      console.error('❌ [getOrderDetail] Error:', error);
      console.error('❌ [getOrderDetail] Error response:', error.response?.data);
      throw error;
    }
  },

  // Get order statistics
  getOrderStats: async () => {
    try {
      // Nếu có API riêng cho stats, gọi ở đây
      // Nếu không, tính từ dữ liệu orders
      const response = await api.get('/api/admin/orders', { 
        params: { page: 1, page_size: 1000 } 
      });
      
      let ordersData = response.data;
      let orders = [];
      
      if (ordersData.data && ordersData.data.content) {
        orders = ordersData.data.content;
      } else if (ordersData.content) {
        orders = ordersData.content;
      } else {
        orders = [];
      }
      
      // Tính toán stats từ orders
      const stats = {
        totalOrders: orders.length,
        draftOrders: orders.filter(o => o.status === 'DRAFT').length,
        pendingOrders: orders.filter(o => o.status === 'PENDING').length,
        confirmedSystemOrders: orders.filter(o => o.status === 'CONFIRMED_SYSTEM').length,
        confirmedShopOrders: orders.filter(o => o.status === 'CONFIRMED_SHOP').length,
        processingOrders: orders.filter(o => o.status === 'PROCESSING').length,
        deliveringOrders: orders.filter(o => o.status === 'DELIVERING').length,
        completedOrders: orders.filter(o => o.status === 'COMPLETED').length,
        cancelledOrders: orders.filter(o => o.status === 'CANCELLED').length
      };
      
      return stats;
    } catch (error) {
      console.error('❌ [getOrderStats] Error:', error);
      // Return default stats if error
      return {
        totalOrders: 0,
        draftOrders: 0,
        pendingOrders: 0,
        confirmedSystemOrders: 0,
        confirmedShopOrders: 0,
        processingOrders: 0,
        deliveringOrders: 0,
        completedOrders: 0,
        cancelledOrders: 0
      };
    }
  },
};