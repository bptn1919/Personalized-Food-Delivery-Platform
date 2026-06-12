import React from 'react';
import styled from 'styled-components';
import { 
  MdAttachMoney, 
  MdShoppingCart, 
  MdRestaurant, 
  MdCancel, 
  MdPeople, 
  MdShowChart,
  MdTrendingUp,
  MdAssessment,
} from 'react-icons/md';
import { 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { Loading } from '../common/Loading';
import { KPICard } from './KPICard';
import { ChartCard } from './ChartCard';
import { TopList, TopListItem, TopItemInfo } from './TopList';

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
  margin-bottom: 24px;

  @media (max-width: 1400px) {
    grid-template-columns: repeat(3, 1fr);
  }
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const ChartGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 24px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const DoubleGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
  align-items: stretch;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 20px;
  }
`;

const SectionTitle = styled.h2`
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  margin: 32px 0 16px 0;
  display: flex;
  align-items: center;
  gap: 10px;

  svg {
    color: #1e3c72;
    font-size: 1.5rem;
  }
`;

const formatCurrency = (amount) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', minimumFractionDigits: 0 }).format(amount);

export const OverviewTab = ({ 
  overviewData, 
  revenueChartData, 
  paymentDistributionData, 
  orderStatusDistributionData, 
  topChefsData,
  successOrdersByDistrictData, 
  loading 
}) => {

  if (loading) {
    return <Loading text="Fetching real-time analytics..." />;
  }

  const getRevenueData = () => {
    const rawData = revenueChartData?.data?.data || revenueChartData?.data || revenueChartData || [];
    if (!Array.isArray(rawData)) return [];
    return rawData.slice(-7).map(item => ({
      date: item.date || 'N/A',
      revenue: Number(item.revenue) || 0,
      orders: Number(item.orders) || 0
    }));
  };
  const displayChartData = getRevenueData();

  const overview = overviewData?.data || overviewData || {};

  const getDistrictData = () => {
    const rawData = successOrdersByDistrictData?.data?.data || successOrdersByDistrictData?.data || successOrdersByDistrictData || [];
    if (!Array.isArray(rawData)) return [];
    return rawData;
  };
  const districtData = getDistrictData();

  const getPaymentData = () => {
    const rawData = paymentDistributionData?.data?.data || paymentDistributionData?.data || paymentDistributionData || [];
    if (!Array.isArray(rawData)) return [];
    return rawData;
  };
  const paymentArray = getPaymentData();

  const getStatusData = () => {
    const rawData = orderStatusDistributionData?.data?.data || orderStatusDistributionData?.data || orderStatusDistributionData || [];
    if (!Array.isArray(rawData)) return [];
    return rawData;
  };
  const statusArray = getStatusData();

  const getChefsData = () => {
    const rawData = topChefsData?.data || topChefsData || [];
    if (!Array.isArray(rawData)) return [];
    return rawData;
  };
  const chefsArray = getChefsData();

  const COLORS = {
    revenue: ['#1e3c72', '#3b82f6', '#94a3b8'],
    status: ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#64748b']
  };

  return (
    <>
      <SectionTitle>
        <MdAssessment /> Key Performance Indicators
      </SectionTitle>
      <Grid>
        <KPICard 
          title="Total Revenue" 
          value={overview.total_revenue || 0}
          icon={<MdAttachMoney />}
          color="#1e3c72"
          isMoney
        />
        <KPICard 
          title="Total Orders" 
          value={overview.total_orders || 0}
          icon={<MdShoppingCart />}
          color="#0ea5e9"
        />
        <KPICard 
          title="Active Chefs" 
          value={overview.active_chefs || 0}
          icon={<MdRestaurant />}
          color="#8b5cf6"
        />
        <KPICard 
          title="Cancellation Rate" 
          value={overview.cancellation_rate || 0}
          icon={<MdCancel />}
          color="#ef4444"
          suffix="%"
          isNumber={false}
        />
        <KPICard 
          title="New Users (30d)" 
          value={overview.new_users || 0}
          icon={<MdPeople />}
          color="#10b981"
        />
      </Grid>

      <SectionTitle>
        <MdShowChart /> Revenue Analytics
      </SectionTitle>
      <DoubleGrid>
        <ChartCard title="Revenue Growth Trend">
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={displayChartData}>
              <defs>
                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1e3c72" stopOpacity={0.1}/>
                  <stop offset="95%" stopColor="#1e3c72" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
              <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} tickFormatter={(v) => `${(v/1000000).toFixed(1)}M ₫`} />
              <Tooltip contentStyle={{borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'}} />
              <Area type="monotone" dataKey="revenue" stroke="#1e3c72" strokeWidth={3} fill="url(#colorRevenue)" name="Revenue" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Daily Order Volume">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={displayChartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
              <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
              <Tooltip cursor={{fill: '#f8fafc'}} contentStyle={{borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'}} />
              <Bar dataKey="orders" fill="#1e3c72" radius={[4, 4, 0, 0]} name="Orders" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </DoubleGrid>

      <DoubleGrid>
        <ChartCard title="Payment Method Mix">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={paymentArray}
                innerRadius={60}
                outerRadius={90}
                paddingAngle={5}
                dataKey="percentage"
                nameKey="payment_method"
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              >
                {paymentArray.map((entry, index) => (
                  <Cell key={`payment-${index}`} fill={COLORS.revenue[index % COLORS.revenue.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${value}%`} />
              <Legend verticalAlign="bottom" height={40} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Order Status Distribution">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={statusArray}
                innerRadius={60}
                outerRadius={90}
                paddingAngle={5}
                dataKey="percentage"
                nameKey="status"
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              >
                {statusArray.map((entry, index) => (
                  <Cell key={`status-${index}`} fill={COLORS.status[index % COLORS.status.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${value}%`} />
              <Legend verticalAlign="bottom" height={40} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </DoubleGrid>

      <DoubleGrid>
        <ChartCard title="Top 5 Revenue-Generating Chefs">
          <TopList>
            {chefsArray.slice(0, 5).length > 0 ? (
              chefsArray.slice(0, 5).map((chef, index) => (
                <TopListItem 
                  key={chef.chef_id || index} 
                  rank={index + 1}
                  value={formatCurrency(chef.total_revenue || 0)}
                >
                  <TopItemInfo 
                    name={chef.chef_name || 'Unknown'}
                    meta={<>{chef.total_orders || 0} successful orders • {chef.chef_email || ''}</>}
                  />
                </TopListItem>
              ))
            ) : (
              <EmptyMessage>No chef data found</EmptyMessage>
            )}
          </TopList>
        </ChartCard>

        <ChartCard title="Regional Order Success (By District)">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart 
              data={districtData} 
              layout="vertical"
              margin={{ left: 80, right: 20, top: 10, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
              <XAxis type="number" axisLine={false} tickLine={false} />
              <YAxis 
                type="category" 
                dataKey="district" 
                axisLine={false} 
                tickLine={false} 
                width={70}
                tick={{ fontSize: 12 }}
              />
              <Tooltip />
              <Bar dataKey="success_orders" fill="#0ea5e9" radius={[0, 4, 4, 0]} name="Successful Orders" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </DoubleGrid>
    </>
  );
};

const EmptyMessage = styled.div`
  padding: 40px;
  text-align: center;
  color: #94a3b8;
  font-style: italic;
`;