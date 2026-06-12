import React from 'react';
import styled from 'styled-components';
import { MdPeople, MdCheckCircle, MdPersonAdd, MdBlock } from 'react-icons/md';
import { StatCard } from '../common/StatCard';

// --- Styled Components ---

const StatsGrid = styled.div`
  display: grid;
  /* Auto-fit ensures cards fill space efficiently */
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 24px;

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
    gap: 16px;
  }
`;

/**
 * UserStats Component
 * High-level overview of user acquisition and account health.
 */
export const UserStats = ({ stats }) => {
  // Safe calculation for active percentage
  const activePercent = stats.totalUsers > 0 
    ? ((stats.activeUsers / stats.totalUsers) * 100).toFixed(1) 
    : '0.0';

  return (
    <StatsGrid>
      {/* Total Accounts */}
      <StatCard
        title="Total Accounts"
        value={stats.totalUsers}
        sub="Consolidated user base"
        icon={<MdPeople />}
        color="#1e3c72" // Navy
      />

      {/* Active Accounts */}
      <StatCard
        title="Active Accounts"
        value={stats.activeUsers}
        sub={`${activePercent}% of total base`}
        icon={<MdCheckCircle />}
        color="#10b981" // Emerald
      />

      {/* Acquisition */}
      <StatCard
        title="New Registrations"
        value={stats.newThisWeek}
        sub="Acquired in last 7 days"
        icon={<MdPersonAdd />}
        color="#f59e0b" // Amber
      />

      {/* Risk/Safety */}
      <StatCard
        title="Restricted / Banned"
        value={`${stats.bannedRate}%`}
        sub={`${stats.bannedUsers} restricted accounts`}
        icon={<MdBlock />}
        color="#ef4444" // Rose
      />
    </StatsGrid>
  );
};