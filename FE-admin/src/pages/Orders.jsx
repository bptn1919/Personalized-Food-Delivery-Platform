import React, { useState, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import { 
  MdShoppingBag, MdFilterList, MdDateRange, MdRefresh 
} from 'react-icons/md';
import { useLocation } from 'react-router-dom';
import { Loading } from '../components/common/Loading';
import { IconBtn } from '../components/common/Button';
import { Pagination } from '../components/common/Pagination';
import { OrderStats } from '../components/orders/OrderStats';
import { OrderFilters } from '../components/orders/OrderFilters';
import { OrderTable } from '../components/orders/OrderTable';
import { OrderDetailModal } from '../components/orders/OrderDetailModal';
import { orderService } from '../services/orderService';

// --- Constants & Enums ---

const STATUS_LIST = [
  { value: 'all', label: 'All Statuses' },
  { value: 'DRAFT', label: 'Draft' },
  { value: 'PENDING', label: 'Pending' },
  { value: 'CONFIRMED_SYSTEM', label: 'Auto-Confirmed' },
  { value: 'CONFIRMED_SHOP', label: 'Store-Confirmed' },
  { value: 'PROCESSING', label: 'In Kitchen' },
  { value: 'DELIVERING', label: 'With Courier' },
  { value: 'COMPLETED', label: 'Delivered' },
  { value: 'CANCELLED', label: 'Voided' }
];

const PAYMENT_METHODS = [
  { value: 'all', label: 'All Methods' },
  { value: 'COD', label: 'Cash on Delivery' },
  { value: 'PAYOS', label: 'PayOS Online' }
];

const PAYMENT_STATUS_LIST = [
  { value: 'all', label: 'All Payment Status' },
  { value: 'PENDING', label: 'Awaiting Payment' },
  { value: 'SUCCESS', label: 'Payment Verified' },
  { value: 'FAILED', label: 'Payment Failed' }
];

// --- Styled Components ---

const Container = styled.div`
  padding: 24px;
  animation: fadeIn 0.3s ease-in-out;
`;

const Header = styled.div`
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 32px; flex-wrap: wrap; gap: 16px;
`;

const TitleSection = styled.div`display: flex; align-items: center; gap: 16px;`;

const TitleIcon = styled.div`
  width: 54px; height: 54px; background: #1e3c72;
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  color: white; font-size: 28px;
  box-shadow: 0 4px 12px rgba(30, 60, 114, 0.2);
`;

const Title = styled.h1`
  font-size: 1.75rem; font-weight: 700; color: #1e293b; margin: 0;
`;

const DateDisplay = styled.div`
  display: flex; align-items: center; gap: 8px; margin-top: 6px;
  color: #64748b; font-size: 0.875rem; font-weight: 500;
  svg { color: #3b82f6; }
`;

const ActionBar = styled.div`display: flex; align-items: center; gap: 12px;`;

const TableContainer = styled.div`
  background: white; 
  padding: 24px; 
  border-radius: 16px;
  border: 1px solid #f1f5f9; 
  margin-top: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
`;

const TableHeader = styled.div`
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;
`;

const TableTitle = styled.h3`
  font-size: 1.1rem; font-weight: 700; color: #1e3c72; margin: 0;
`;

// --- Component Logic ---

const Orders = () => {
  const location = useLocation();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showOrderDetail, setShowOrderDetail] = useState(false);
  
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRows, setTotalRows] = useState(0);
  
  const [appliedFilters, setAppliedFilters] = useState({
    status: 'all', payment_method: 'all', payment_status: 'all',
    customer_email: '', chef_email: '', from_date: '', to_date: ''
  });

  const [tempFilters, setTempFilters] = useState({ ...appliedFilters });

  const [orderStats, setOrderStats] = useState({
    totalOrders: 0, draftOrders: 0, pendingOrders: 0, confirmedSystemOrders: 0,
    confirmedShopOrders: 0, processingOrders: 0, deliveringOrders: 0,
    completedOrders: 0, cancelledOrders: 0
  });
  
  const pageSize = 10;

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page: currentPage, page_size: pageSize };

      Object.entries(appliedFilters).forEach(([key, value]) => {
        if (value && value !== 'all') params[key] = value;
      });

      // Parallel data fetching for better performance
      const [orderRes, statsRes] = await Promise.all([
        orderService.getOrders(params),
        orderService.getOrderStats()
      ]);

      if (orderRes) {
        setOrders(orderRes.content || []);
        setTotalRows(orderRes.total_rows || 0);
        setTotalPages(orderRes.total_pages || 1);
      }
      if (statsRes) setOrderStats(statsRes);

    } catch (error) {
      console.error('❌ Sync Error:', error);
    } finally {
      setLoading(false);
    }
  }, [currentPage, appliedFilters]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  // Handle cross-navigation from User profile
  useEffect(() => {
    if (location.state?.customer_email) {
      const externalSearch = {
        status: 'all', payment_method: 'all', payment_status: 'all',
        customer_email: location.state.customer_email, chef_email: '',
        from_date: '', to_date: ''
      };
      setTempFilters(externalSearch);
      setAppliedFilters(externalSearch);
      setCurrentPage(1);
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const handleViewOrder = async (order) => {
    try {
      const detail = await orderService.getOrderDetail(order.uid);
      setSelectedOrder(detail);
      setShowOrderDetail(true);
    } catch (error) {
      console.error('Fetch Error:', error);
    }
  };

  const getCurrentDate = () => {
    return new Date().toLocaleDateString('en-US', { 
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' 
    });
  };

  if (loading && orders.length === 0) {
    return <Loading fullPage text="Retrieving order manifest..." />;
  }

  return (
    <Container>
      <Header>
        <TitleSection>
          <TitleIcon><MdShoppingBag /></TitleIcon>
          <div>
            <Title>Orders Management</Title>
          </div>
        </TitleSection>
        
        <ActionBar>
          <IconBtn $active={showFilters} onClick={() => setShowFilters(!showFilters)} title="Filters">
            <MdFilterList />
          </IconBtn>
        </ActionBar>
      </Header>

      <OrderStats stats={orderStats} />

      <OrderFilters 
        show={showFilters}
        filters={tempFilters}
        statusList={STATUS_LIST}
        paymentMethods={PAYMENT_METHODS}
        paymentStatusList={PAYMENT_STATUS_LIST}
        onFilterChange={(k, v) => setTempFilters(p => ({...p, [k]: v}))}
        onReset={() => {
          const reset = { status: 'all', payment_method: 'all', payment_status: 'all', customer_email: '', chef_email: '', from_date: '', to_date: '' };
          setTempFilters(reset);
          setAppliedFilters(reset);
          setCurrentPage(1);
          setShowFilters(false);
        }}
        onApply={() => {
          setAppliedFilters(tempFilters);
          setCurrentPage(1);
          setShowFilters(false);
        }}
        onClose={() => setShowFilters(false)}
      />

      <TableContainer>

        <OrderTable 
          orders={orders}
          onView={handleViewOrder}
        />

        {totalPages > 1 && (
          <Pagination 
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
            totalItems={totalRows}
            pageSize={pageSize}
          />
        )}
      </TableContainer>

      <OrderDetailModal 
        isOpen={showOrderDetail}
        order={selectedOrder}
        onClose={() => setShowOrderDetail(false)}
      />
    </Container>
  );
};

export default Orders;