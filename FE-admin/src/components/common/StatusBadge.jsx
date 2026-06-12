import React from 'react';
import styled from 'styled-components';

// Cấu hình bảng màu hiện đại
const STATUS_COLORS = {
  completed: { bg: '#dcfce7', text: '#166534', dot: '#22c55e' },
  active: { bg: '#dcfce7', text: '#166534', dot: '#22c55e' },
  pending: { bg: '#fef9c3', text: '#854d0e', dot: '#eab308' },
  cancelled: { bg: '#fee2e2', text: '#991b1b', dot: '#ef4444' },
  banned: { bg: '#fee2e2', text: '#991b1b', dot: '#ef4444' },
  confirmed: { bg: '#dbeafe', text: '#1e40af', dot: '#3b82f6' },
  preparing: { bg: '#e0e7ff', text: '#3730a3', dot: '#6366f1' },
  shipping: { bg: '#f3e8ff', text: '#6b21a8', dot: '#a855f7' },
  refunded: { bg: '#f1f5f9', text: '#475569', dot: '#94a3b8' },
  cod: { bg: '#ecfeff', text: '#0891b2', dot: '#06b6d4' },
  banking: { bg: '#f8fafc', text: '#475569', dot: '#cbd5e1' },
  default: { bg: '#f1f5f9', text: '#475569', dot: '#94a3b8' }
};

const BadgeContainer = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 99px;
  text-transform: capitalize;
  white-space: nowrap;
  
  /* Áp dụng màu động */
  background-color: ${({ $colors }) => $colors.bg};
  color: ${({ $colors }) => $colors.text};
  border: 1px solid ${({ $colors }) => $colors.dot}20; // Border siêu nhạt
`;

const StatusDot = styled.span`
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: ${({ $color }) => $color};
  display: inline-block;
`;

export const StatusBadge = ({ status, type, children }) => {
  // Ưu tiên check type payment trước, nếu không lấy theo status chung
  const statusKey = type === 'payment' ? (status || 'default') : (status || 'default');
  const colors = STATUS_COLORS[statusKey] || STATUS_COLORS.default;

  return (
    <BadgeContainer $colors={colors}>
      <StatusDot $color={colors.dot} />
      {children || status}
    </BadgeContainer>
  );
};