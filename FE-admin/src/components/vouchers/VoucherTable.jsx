import React from 'react';
import styled from 'styled-components';
import { MdEdit, MdDelete } from 'react-icons/md';
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '../common/Table';
import { StatusBadge } from '../common/StatusBadge';

// --- Styled Components ---

const ActionGroup = styled.div`
  display: flex;
  gap: 8px;
  justify-content: center;
  align-items: center;
`;

const ActionButton = styled.button`
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 10px;
  background: #f8fafc;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 1.1rem;

  &:hover {
    transform: translateY(-2px);
    background: ${({ $variant }) => $variant === 'danger' ? '#fef2f2' : '#eff6ff'};
    color: ${({ $variant }) => $variant === 'danger' ? '#ef4444' : '#3b82f6'};
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }
`;

const VoucherCode = styled.code`
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  color: #1e3c72;
  background: #f1f5f9;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.85rem;
  letter-spacing: 0.05em;
`;

const UsageText = styled.div`
  font-size: 0.85rem;
  font-weight: 500;
  color: #475569;
  
  span {
    color: #94a3b8;
    font-weight: 400;
  }
`;

const DateRange = styled.div`
  font-size: 0.8rem;
  color: #64748b;
  white-space: nowrap;
`;

// --- Helpers ---

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('vi-VN', { 
    style: 'currency', 
    currency: 'VND',
    minimumFractionDigits: 0
  }).format(amount || 0);
};

const formatDate = (dateString) => {
  if (!dateString) return '---';
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  });
};

const getVoucherTypeLabel = (type) => {
  const labels = {
    'SHOP_VOUCHER': 'Merchant',
    'PLATFORM_SUBTOTAL': 'Platform',
    'PLATFORM_SHIPPING': 'Shipping'
  };
  return labels[type] || type;
};

const getDiscountDisplay = (voucher) => {
  if (voucher.discount_type === 'PERCENTAGE') {
    return (
      <span style={{ fontWeight: 700, color: '#10b981' }}>
        {voucher.discount_value}% OFF
      </span>
    );
  }
  return (
    <span style={{ fontWeight: 700, color: '#1e293b' }}>
      -{formatCurrency(voucher.discount_value)}
    </span>
  );
};

/**
 * VoucherTable Component
 * Advanced overview for promotional campaigns and redemption tracking.
 */
export const VoucherTable = ({ vouchers, onEdit, onDelete }) => {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell>Promo Code</TableHeaderCell>
          <TableHeaderCell>Campaign Name</TableHeaderCell>
          <TableHeaderCell>Scope</TableHeaderCell>
          <TableHeaderCell>Reward</TableHeaderCell>
          <TableHeaderCell>Min. Spend</TableHeaderCell>
          <TableHeaderCell>Validity Period</TableHeaderCell>
          <TableHeaderCell>Redemptions</TableHeaderCell>
          <TableHeaderCell>Status</TableHeaderCell>
          <TableHeaderCell align="center">Actions</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {vouchers.map((voucher) => (
          <TableRow key={voucher.uid}>
            <TableCell>
              <VoucherCode>{voucher.code}</VoucherCode>
            </TableCell>
            
            <TableCell style={{ fontWeight: 600, color: '#334155' }}>
              {voucher.name}
            </TableCell>
            
            <TableCell>
              <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
                {getVoucherTypeLabel(voucher.voucher_type)}
              </span>
            </TableCell>
            
            <TableCell>{getDiscountDisplay(voucher)}</TableCell>
            
            <TableCell>{formatCurrency(voucher.min_order_amount)}</TableCell>
            
            <TableCell>
              <DateRange>
                {formatDate(voucher.start_date)} — {formatDate(voucher.end_date)}
              </DateRange>
            </TableCell>
            
            <TableCell>
              <UsageText>
                {voucher.usage_count || 0} <span>/ {voucher.usage_limit || '∞'}</span>
              </UsageText>
            </TableCell>
            
            <TableCell>
              <StatusBadge status={voucher.is_active ? 'active' : 'inactive'}>
                {voucher.is_active ? 'Live' : 'Paused'}
              </StatusBadge>
            </TableCell>
            
            <TableCell>
              <ActionGroup>
                <ActionButton onClick={() => onEdit(voucher)} title="Edit Campaign">
                  <MdEdit />
                </ActionButton>
                <ActionButton 
                  $variant="danger" 
                  onClick={() => onDelete(voucher)} 
                  title="Delete Campaign"
                >
                  <MdDelete />
                </ActionButton>
              </ActionGroup>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};