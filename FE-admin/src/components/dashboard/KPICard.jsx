import React from 'react';
import styled from 'styled-components';
import { MdTrendingUp, MdTrendingDown } from 'react-icons/md';

// Modern Card Container
const Card = styled.div`
  background: white;
  padding: 24px;
  border-radius: 20px;
  border: 1px solid #f1f5f9;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  justify-content: space-between;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  }
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
`;

const Title = styled.h3`
  color: #64748b;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 700;
  margin: 0;
`;

const IconWrapper = styled.div`
  width: 44px;
  height: 44px;
  /* Dynamic translucent background based on theme color */
  background: ${({ $color }) => ($color ? `${$color}15` : '#1e3c7215')};
  color: ${({ $color }) => ($color || '#1e3c72')};
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
`;

const Value = styled.div`
  font-size: 2rem;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 12px;
  letter-spacing: -0.02em;
`;

const TrendBadge = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 99px;
  width: fit-content;
  
  /* Semantic Colors */
  background: ${({ $positive }) => ($positive ? '#dcfce7' : '#fee2e2')};
  color: ${({ $positive }) => ($positive ? '#166534' : '#991b1b')};

  span {
    color: #64748b;
    font-weight: 400;
    margin-left: 2px;
  }
`;

// Helper formatters
const formatNumber = (num) => new Intl.NumberFormat('en-US').format(num);
const formatCurrency = (amount) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', minimumFractionDigits: 0 }).format(amount);

/**
 * KPICard Component
 * @param {string} title - Label for the metric
 * @param {number|string} value - Main number
 * @param {number} change - Percentage change from previous period
 * @param {ReactNode} icon - Icon from react-icons
 * @param {string} color - Hex color for the theme (e.g., #1e3c72)
 * @param {string} suffix - Text to append to the number (e.g., "kg")
 * @param {boolean} isMoney - If true, formats as VND
 * @param {boolean} isNumber - If true, formats with commas
 */
export const KPICard = ({ 
  title, 
  value, 
  change, 
  icon, 
  color, 
  suffix = '', 
  isMoney = false, 
  isNumber = true 
}) => {
  const displayValue = isMoney 
    ? formatCurrency(value) 
    : isNumber 
      ? formatNumber(value) + suffix 
      : value + suffix;

  return (
    <Card>
      <Header>
        <Title>{title}</Title>
        <IconWrapper $color={color}>{icon}</IconWrapper>
      </Header>
      
      <div>
        <Value>{displayValue}</Value>
        
        {change !== undefined && (
          <TrendBadge $positive={change >= 0}>
            {change >= 0 ? <MdTrendingUp /> : <MdTrendingDown />}
            {Math.abs(change)}%
            <span>vs last period</span>
          </TrendBadge>
        )}
      </div>
    </Card>
  );
};