import React from 'react';
import styled from 'styled-components';
import { MdVisibility, MdOutlineReceiptLong } from 'react-icons/md';
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
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 10px;
  background: #f8fafc;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 1.2rem;

  &:hover {
    transform: translateY(-2px);
    background: #eff6ff;
    color: #1e3c72;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }

  &:active {
    transform: translateY(0);
  }
`;

const OrderId = styled.span`
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-weight: 700;
  color: #1e293b;
  font-size: 0.85rem;
  background: #f1f5f9;
  padding: 4px 8px;
  border-radius: 6px;
`;

const ParticipantInfo = styled.div`
  display: flex;
  flex-direction: column;
  
  .name {
    font-weight: 600;
    color: #1e3c72;
    font-size: 0.9rem;
  }
  
  .email {
    font-size: 0.75rem;
    color: #94a3b8;
    margin-top: 2px;
  }
`;

const PriceText = styled.span`
  font-weight: 800;
  color: #1e293b;
  font-variant-numeric: tabular-nums;
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
    day: 'numeric',
    year: 'numeric'
  });
};

/**
 * OrderTable Component
 * Optimized for administrative oversight of high-volume logistics.
 */
export const OrderTable = ({ orders = [], onView }) => {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell>Reference</TableHeaderCell>
          <TableHeaderCell>Customer</TableHeaderCell>
          <TableHeaderCell>Chef / Provider</TableHeaderCell>
          <TableHeaderCell>Total Amount</TableHeaderCell>
          <TableHeaderCell>Fulfillment</TableHeaderCell>
          <TableHeaderCell>Payment</TableHeaderCell>
          <TableHeaderCell>Date Placed</TableHeaderCell>
          <TableHeaderCell align="center">Details</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {orders.length > 0 ? (
          orders.map((order) => (
            <TableRow key={order.uid}>
              <TableCell>
                <OrderId title={order.uid}>
                  {order.uid?.slice(0, 8).toUpperCase()}
                </OrderId>
              </TableCell>
              
              <TableCell>
                <ParticipantInfo>
                  <span className="name">{order.customer_name || 'Guest'}</span>
                  <span className="email">{order.customer_email}</span>
                </ParticipantInfo>
              </TableCell>
              
              <TableCell>
                <ParticipantInfo>
                  <span className="name">{order.chef_name || 'Unassigned'}</span>
                  <span className="email">{order.chef_email}</span>
                </ParticipantInfo>
              </TableCell>
              
              <TableCell>
                <PriceText>{formatCurrency(order.total_price)}</PriceText>
              </TableCell>
              
              <TableCell>
                <StatusBadge status={order.status?.toLowerCase()}>
                  {order.status}
                </StatusBadge>
              </TableCell>
              
              <TableCell>
                <StatusBadge status={order.payment_status?.toLowerCase()}>
                  {order.payment_status}
                </StatusBadge>
              </TableCell>
              
              <TableCell style={{ color: '#64748b', fontSize: '0.85rem' }}>
                {formatDate(order.created_at)}
              </TableCell>
              
              <TableCell>
                <ActionGroup>
                  <ActionButton onClick={() => onView(order)} title="View Full Invoice">
                    <MdVisibility />
                  </ActionButton>
                </ActionGroup>
              </TableCell>
            </TableRow>
          ))
        ) : (
          <TableRow>
            <TableCell colSpan="8" style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
              No orders found matching the criteria.
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
};