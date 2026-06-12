import React from 'react';
import styled from 'styled-components';
import { MdEdit, MdDelete, MdVisibility, MdFastfood } from 'react-icons/md';
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '../common/Table';
import { StatusBadge } from '../common/StatusBadge';

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
    background: ${({ $variant }) => {
      if ($variant === 'danger') return '#fef2f2';
      if ($variant === 'success') return '#f0fdf4';
      return '#eff6ff';
    }};
    color: ${({ $variant }) => {
      if ($variant === 'danger') return '#ef4444';
      if ($variant === 'success') return '#22c55e';
      return '#3b82f6';
    }};
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }

  &:active {
    transform: translateY(0);
  }
`;

const DishImageWrapper = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 12px;
  overflow: hidden;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e2e8f0;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  svg {
    color: #94a3b8;
    font-size: 1.5rem;
  }
`;

const DishName = styled.div`
  font-weight: 700;
  color: #1e3c72;
  font-size: 0.95rem;
`;

const DescriptionText = styled.div`
  max-width: 240px;
  font-size: 0.85rem;
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
`;

// Standardized Currency Formatter
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('vi-VN', { 
    style: 'currency', 
    currency: 'VND',
    minimumFractionDigits: 0
  }).format(amount || 0);
};

export const DishTable = ({ dishes, onView, onEdit, onDelete }) => {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell>Dish</TableHeaderCell>
          <TableHeaderCell>Name</TableHeaderCell>
          <TableHeaderCell>Category</TableHeaderCell>
          <TableHeaderCell>Description</TableHeaderCell>
          <TableHeaderCell>Price</TableHeaderCell>
          <TableHeaderCell>Status</TableHeaderCell>
          <TableHeaderCell align="center">Actions</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {dishes.map((dish) => (
          <TableRow key={dish.uid}>
            <TableCell>
              <DishImageWrapper>
                {dish.public_url ? (
                  <img src={dish.public_url} alt={dish.name} />
                ) : (
                  <MdFastfood />
                )}
              </DishImageWrapper>
            </TableCell>
            
            <TableCell>
              <DishName title={dish.name}>{dish.name}</DishName>
            </TableCell>
            
            <TableCell style={{ textTransform: 'capitalize', fontWeight: '500' }}>
              {dish.category?.toLowerCase() || 'Uncategorized'}
            </TableCell>
            
            <TableCell>
              <DescriptionText title={dish.description}>
                {dish.description || 'No description provided.'}
              </DescriptionText>
            </TableCell>
            
            <TableCell style={{ fontWeight: '700', color: '#1e293b' }}>
              {formatCurrency(dish.price)}
            </TableCell>
            
            <TableCell>
              <StatusBadge status={dish.status === 'AVAILABLE' ? 'active' : 'cancelled'}>
                {dish.status === 'AVAILABLE' ? 'In Stock' : 'Out of Stock'}
              </StatusBadge>
            </TableCell>
            
            <TableCell>
              <ActionGroup>
                <ActionButton 
                  onClick={() => onView(dish)} 
                  title="View Details"
                >
                  <MdVisibility />
                </ActionButton>
                
                <ActionButton 
                  $variant="success" 
                  onClick={() => onEdit(dish)} 
                  title="Edit Item"
                >
                  <MdEdit />
                </ActionButton>
                
                <ActionButton 
                  $variant="danger" 
                  onClick={() => onDelete(dish)} 
                  title="Delete Item"
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