import React from 'react';
import styled from 'styled-components';
import { 
  MdShoppingBag, MdPending, MdCheckCircle, 
  MdCancel, MdLocalShipping, MdAccessTime,
  MdOutlineSystemUpdate, MdOutlineStore, MdDrafts
} from 'react-icons/md';
import { StatCard } from '../common/StatCard';

const StatsGrid = styled.div`
  display: grid;
  /* Uses minmax to ensure cards don't get too squished */
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 24px;

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
    gap: 16px;
  }
`;

const ClickableWrapper = styled.div`
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  border-radius: 20px; /* Matches StatCard rounding */
  
  &:hover {
    transform: translateY(-4px);
  }
  
  /* Active indicator: A glowing ring and a slight scale up */
  ${({ $active, $color }) => $active && `
    transform: scale(1.02);
    box-shadow: 0 0 0 3px ${$color}40, 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    z-index: 2;
  `}
`;

const ActiveRibbon = styled.div`
  position: absolute;
  top: 12px;
  right: 12px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${({ $color }) => $color};
  box-shadow: 0 0 10px ${({ $color }) => $color};
  display: ${({ $active }) => ($active ? 'block' : 'none')};
`;

export const OrderStats = ({ stats, activeStat, onStatClick }) => {
  // Modern Semantic Palette
  const statItems = [
    { key: 'total', title: 'Total Orders', value: stats.totalOrders, sub: 'Consolidated volume', icon: MdShoppingBag, color: '#1e3c72' },
    { key: 'draft', title: 'Draft', value: stats.draftOrders, sub: 'Incomplete checkouts', icon: MdDrafts, color: '#64748b' },
    { key: 'pending', title: 'Pending', value: stats.pendingOrders, sub: 'Awaiting confirmation', icon: MdPending, color: '#f59e0b' },
    { key: 'confirmedSystem', title: 'Confirmed (Auto)', value: stats.confirmedSystemOrders, sub: 'System validated', icon: MdOutlineSystemUpdate, color: '#10b981' },
    { key: 'confirmedShop', title: 'Confirmed (Manual)', value: stats.confirmedShopOrders, sub: 'Store validated', icon: MdOutlineStore, color: '#059669' },
    { key: 'processing', title: 'Processing', value: stats.processingOrders, sub: 'Kitchen prep in progress', icon: MdAccessTime, color: '#3b82f6' },
    { key: 'delivering', title: 'Delivering', value: stats.deliveringOrders, sub: 'Out with courier', icon: MdLocalShipping, color: '#8b5cf6' },
    { key: 'completed', title: 'Completed', value: stats.completedOrders, sub: 'Successful fulfillment', icon: MdCheckCircle, color: '#1e293b' },
    { key: 'cancelled', title: 'Cancelled', value: stats.cancelledOrders, sub: 'Voided transactions', icon: MdCancel, color: '#ef4444' }
  ];

  return (
    <StatsGrid>
      {statItems.map(item => (
        <ClickableWrapper 
          key={item.key}
          $active={activeStat === item.key}
          $color={item.color}
          onClick={() => onStatClick(item.key)}
        >
          <ActiveRibbon $active={activeStat === item.key} $color={item.color} />
          <StatCard
            title={item.title}
            value={item.value}
            sub={item.sub}
            icon={<item.icon />}
            color={item.color}
          />
        </ClickableWrapper>
      ))}
    </StatsGrid>
  );
};