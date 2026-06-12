import React from 'react';
import styled from 'styled-components';
import { 
  MdPending, MdCancel, MdOutlineAssignment,
  MdCheckCircle
} from 'react-icons/md';
import { StatCard } from '../common/StatCard';

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px; /* Increased gap for better "breathing" room and shadow separation */
  margin-bottom: 24px;

  /* Tablet */
  @media (max-width: 1200px) {
    grid-template-columns: repeat(2, 1fr);
  }

  /* Mobile */
  @media (max-width: 600px) {
    grid-template-columns: 1fr;
    gap: 16px;
  }
`;

/**
 * Component displaying an overview of certificate statistics
 * @param {Object} stats - Object containing counts: total, pending, active, expired, revoked
 */
export const CertificateStats = ({ stats }) => {
  // Safe percentage calculation (prevents division by zero)
  const calculatePercent = (value) => {
    if (!stats.total || stats.total === 0) return '0.0';
    return ((value / stats.total) * 100).toFixed(1);
  };

  const totalLabel = `Total of ${stats.total} certificates`;
  const pendingPercent = `Accounts for ${calculatePercent(stats.pending)}% of system`;
  const activePercent = `Verified: ${calculatePercent(stats.active)}%`;
  const issueSummary = `${stats.expired} expired • ${stats.revoked} revoked`;

  return (
    <StatsGrid>
      {/* Card: Total */}
      <StatCard
        title="Total Certificates"
        value={stats.total}
        sub={totalLabel}
        icon={<MdOutlineAssignment />}
        color="#1e3c72" // Navy Blue
      />

      {/* Card: Pending Review */}
      <StatCard
        title="Pending Review"
        value={stats.pending}
        sub={pendingPercent}
        icon={<MdPending />}
        color="#f59e0b" // Amber
      />

      {/* Card: Active */}
      <StatCard
        title="Active"
        value={stats.active}
        sub={activePercent}
        icon={<MdCheckCircle />}
        color="#10b981" // Emerald
      />

    </StatsGrid>
  );
};