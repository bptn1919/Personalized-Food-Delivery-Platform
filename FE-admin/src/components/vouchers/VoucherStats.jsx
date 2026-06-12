import React from 'react';
import styled from 'styled-components';
import { 
  MdLocalOffer, MdCheckCircle, MdBlock, MdHistoryToggleOff
} from 'react-icons/md';
import { StatCard } from '../common/StatCard';

// --- Styled Components ---

const StatsGrid = styled.div`
  display: grid;
  /* Fluid layout: cards will wrap naturally based on available width */
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 24px;

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
    gap: 16px;
  }
`;

/**
 * VoucherStats Component
 * High-level overview of promotional campaign distribution and health.
 */
export const VoucherStats = ({ stats }) => {
  // Defensive data handling
  const safeStats = {
    totalVouchers: stats?.totalVouchers || 0,
    activeVouchers: stats?.activeVouchers || 0,
    inactiveVouchers: stats?.inactiveVouchers || 0,
    expiringSoon: stats?.expiringSoon || 0
  };

  const activePercentage = safeStats.totalVouchers > 0 
    ? ((safeStats.activeVouchers / safeStats.totalVouchers) * 100).toFixed(1)
    : '0.0';

  return (
    <StatsGrid>
      {/* Total Inventory */}
      <StatCard
        title="Total Campaigns"
        value={safeStats.totalVouchers}
        sub="Consolidated voucher pool"
        icon={<MdLocalOffer />}
        color="#1e3c72" // Navy
      />

      {/* Live Campaigns */}
      <StatCard
        title="Active Offers"
        value={safeStats.activeVouchers}
        sub={`${activePercentage}% utilization rate`}
        icon={<MdCheckCircle />}
        color="#10b981" // Emerald
      />

      {/* Paused/Disabled */}
      <StatCard
        title="Inactive"
        value={safeStats.inactiveVouchers}
        sub="Manually offline or voided"
        icon={<MdBlock />}
        color="#ef4444" // Rose
      />

      {/* Time-sensitive Alerts */}
      <StatCard
        title="Expiring Soon"
        value={safeStats.expiringSoon}
        sub="Campaigns ending < 7 days"
        icon={<MdHistoryToggleOff />}
        color="#f59e0b" // Amber
      />
    </StatsGrid>
  );
};