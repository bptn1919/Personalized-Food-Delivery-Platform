import React, { useState, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import { 
  MdAssessment, MdDateRange, MdFilterList, MdRefresh 
} from 'react-icons/md';
import { Loading } from '../components/common/Loading';
import { IconBtn } from '../components/common/Button';
import { FilterPanel, FilterRow, FilterItem } from '../components/common/FilterPanel';
import { OverviewTab } from '../components/dashboard/OverviewTab';
import { dashboardService } from '../services/dashboardService';

// --- Styled Components ---

const Container = styled.div`
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  flex-wrap: wrap;
  gap: 16px;
`;

const TitleSection = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`;

const TitleIcon = styled.div`
  width: 54px;
  height: 54px;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 28px;
  box-shadow: 0 4px 12px rgba(30, 60, 114, 0.2);
`;

const Title = styled.h1`
  font-size: 1.75rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
`;

const DateDisplay = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 500;

  svg { color: #3b82f6; }
`;

const ActionBar = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

// --- Main Component ---

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  
  // Data States
  const [dashboardData, setDashboardData] = useState({
    overview: null,
    revenueChart: null,
    paymentDist: null,
    statusDist: null,
    topChefs: null,
    districtStats: null
  });

  const [dateRange, setDateRange] = useState({ fromDate: '', toDate: '' });

  // Centralized Fetch Logic
  const fetchAllData = useCallback(async () => {
    setLoading(true);
    try {
      const safeFetch = async (promise, fallback = null) => {
        try {
          return await promise;
        } catch (e) {
          console.warn("Dashboard API fetch failed, using fallback:", e);
          return fallback;
        }
      };

      const [
        overview, 
        revenue, 
        payment, 
        status, 
        chefs, 
        districts
      ] = await Promise.all([
        safeFetch(dashboardService.getOverview(), {}),
        safeFetch(dashboardService.getLast30DaysRevenue(), []),
        safeFetch(dashboardService.getPaymentMethodDistribution(), []),
        safeFetch(dashboardService.getOrderStatusDistribution(), []),
        safeFetch(dashboardService.getTopChefs(5), []),
        safeFetch(dashboardService.getLast30DaysSuccessOrdersByDistrict(), [])
      ]);

      setDashboardData({
        overview,
        revenueChart: revenue,
        paymentDist: payment,
        statusDist: status,
        topChefs: chefs,
        districtStats: districts
      });
    } catch (error) {
      console.error('Critical Dashboard Error:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  const handleApplyDateRange = async () => {
    if (!dateRange.fromDate || !dateRange.toDate) return;
    
    setLoading(true);
    try {
      const safeFetch = async (promise, fallback = null) => {
        try {
          return await promise;
        } catch (e) {
          console.warn("Date range fetch failed, using fallback:", e);
          return fallback;
        }
      };

      const [revenue, districts] = await Promise.all([
        safeFetch(dashboardService.getCustomRangeRevenue(dateRange.fromDate, dateRange.toDate), []),
        safeFetch(dashboardService.getSuccessOrdersByDistrict(dateRange.fromDate, dateRange.toDate), [])
      ]);
      
      setDashboardData(prev => ({
        ...prev,
        revenueChart: revenue,
        districtStats: districts
      }));
      setShowFilters(false);
    } catch (error) {
      console.error('Filtering Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCurrentDate = () => {
    return new Date().toLocaleDateString('en-US', { 
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' 
    });
  };

  if (loading && !dashboardData.overview) {
    return <Loading fullPage text="Syncing real-time analytics..." />;
  }

  return (
    <Container>
      <Header>
        <TitleSection>
          <TitleIcon><MdAssessment /></TitleIcon>
          <div>
            <Title>Dashboard Management</Title>
            <DateDisplay>
              <MdDateRange />
              <span>{getCurrentDate()}</span>
            </DateDisplay>
          </div>
        </TitleSection>
        
        <ActionBar>
          <IconBtn onClick={() => setShowFilters(!showFilters)} $active={showFilters}>
            <MdFilterList />
          </IconBtn>
        </ActionBar>
      </Header>

      <FilterPanel 
        show={showFilters} 
        onApply={handleApplyDateRange} 
        onReset={() => {
          setDateRange({ fromDate: '', toDate: '' });
          fetchAllData();
        }}
        onClose={() => setShowFilters(false)}
        title="Custom Date Range"
      >
        <FilterRow>
          <FilterItem label="Start Date">
            <input 
              type="date" 
              value={dateRange.fromDate}
              onChange={(e) => setDateRange({...dateRange, fromDate: e.target.value})}
              max={dateRange.toDate || new Date().toISOString().split('T')[0]}
            />
          </FilterItem>
          <FilterItem label="End Date">
            <input 
              type="date" 
              value={dateRange.toDate}
              onChange={(e) => setDateRange({...dateRange, toDate: e.target.value})}
              min={dateRange.fromDate}
              max={new Date().toISOString().split('T')[0]}
            />
          </FilterItem>
        </FilterRow>
      </FilterPanel>

      <OverviewTab 
        overviewData={dashboardData.overview}
        revenueChartData={dashboardData.revenueChart}
        paymentDistributionData={dashboardData.paymentDist}
        orderStatusDistributionData={dashboardData.statusDist}
        topChefsData={dashboardData.topChefs}
        successOrdersByDistrictData={dashboardData.districtStats}
        loading={loading}
      />
    </Container>
  );
};

export default Dashboard;