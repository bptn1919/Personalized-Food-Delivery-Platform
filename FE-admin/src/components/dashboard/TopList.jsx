import React from 'react';
import styled from 'styled-components';

const List = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const Item = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: white;
  border-radius: 12px;
  border: 1px solid #f1f5f9;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  
  /* Left accent bar for top 3 ranks */
  border-left: 4px solid ${({ $rank }) => {
    if ($rank === 1) return '#f59e0b'; // Gold
    if ($rank === 2) return '#94a3b8'; // Silver
    if ($rank === 3) return '#b45309'; // Bronze
    return 'transparent';
  }};

  &:hover {
    transform: translateX(4px);
    background: #f8fafc;
    border-color: #e2e8f0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  }
`;

const RankCircle = styled.div`
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 0.85rem;

  /* Rank-based styling */
  background: ${({ $rank }) => {
    if ($rank === 1) return 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)';
    if ($rank === 2) return 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)';
    if ($rank === 3) return 'linear-gradient(135deg, #ffedd5 0%, #fed7aa 100%)';
    return '#f8fafc';
  }};
  
  color: ${({ $rank }) => {
    if ($rank === 1) return '#92400e';
    if ($rank === 2) return '#475569';
    if ($rank === 3) return '#9a3412';
    return '#64748b';
  }};

  border: 1px solid ${({ $rank }) => {
    if ($rank === 1) return '#fde68a';
    if ($rank === 2) return '#e2e8f0';
    if ($rank === 3) return '#fed7aa';
    return '#f1f5f9';
  }};
`;

const Content = styled.div`
  flex: 1;
  min-width: 0; /* Important for text truncation in children */
`;

const Name = styled.div`
  font-weight: 700;
  color: #1e293b;
  font-size: 0.95rem;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const Meta = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: #64748b;
  
  span.separator {
    width: 3px;
    height: 3px;
    background: #cbd5e1;
    border-radius: 50%;
  }
`;

const ValueBadge = styled.div`
  font-size: 0.95rem;
  font-weight: 800;
  color: #1e3c72;
  text-align: right;
  font-variant-numeric: tabular-nums; /* Keeps numbers aligned */
`;

export const TopList = ({ children }) => <List>{children}</List>;

/**
 * TopListItem
 * @param {number} rank - Positioning (1-3 gets special styling)
 * @param {string|ReactNode} value - The metric value (e.g., $1,200)
 */
export const TopListItem = ({ rank, children, value }) => (
  <Item $rank={rank}>
    <RankCircle $rank={rank}>{rank}</RankCircle>
    <Content>{children}</Content>
    {value && <ValueBadge>{value}</ValueBadge>}
  </Item>
);

/**
 * TopItemInfo
 * @param {string} name - Primary text (Chef name, Dish name)
 * @param {ReactNode} meta - Secondary text/stats
 */
export const TopItemInfo = ({ name, meta }) => (
  <>
    <Name title={name}>{name}</Name>
    <Meta>{meta}</Meta>
  </>
);