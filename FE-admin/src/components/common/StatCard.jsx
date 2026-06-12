import React from 'react';
import styled from 'styled-components';

const Card = styled.div`
  background: white;
  padding: 24px;
  border-radius: 20px; /* Bo góc lớn đồng bộ với Modal và Sidebar */
  border: 1px solid #f1f5f9;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    border-color: ${({ $color }) => $color + '40' || '#1e3c7240'};
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
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 700;
  margin: 0;
`;

const IconWrapper = styled.div`
  width: 48px;
  height: 48px;
  /* Tạo nền gradient nhạt dựa trên màu chủ đạo */
  background: ${({ $color }) => ($color ? `${$color}15` : '#1e3c7215')};
  color: ${({ $color }) => $color || '#1e3c72'};
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  transition: all 0.3s ease;

  ${Card}:hover & {
    background: ${({ $color }) => $color || '#1e3c72'};
    color: white;
    transform: rotate(-10deg) scale(1.1);
  }
`;

const Value = styled.div`
  font-size: 2rem;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 8px;
  letter-spacing: -0.02em;
`;

const SubText = styled.div`
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
  
  /* Tự động đổi màu nếu sub chứa ký hiệu tăng/giảm */
  color: ${({ children }) => {
    const text = String(children);
    if (text.includes('+')) return '#10b981'; // Success green
    if (text.includes('-')) return '#ef4444'; // Danger red
    return '#64748b'; // Slate
  }};
`;

export const StatCard = ({ title, value, sub, icon, color }) => {
  return (
    <Card $color={color}>
      <Header>
        <Title>{title}</Title>
        <IconWrapper $color={color}>
          {icon}
        </IconWrapper>
      </Header>
      <Value>{value}</Value>
      {sub && <SubText>{sub}</SubText>}
    </Card>
  );
};