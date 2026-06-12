import React from 'react';
import styled from 'styled-components';
import { MdEdit, MdDelete, MdRestaurantMenu } from 'react-icons/md';
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

const MenuName = styled.div`
  font-weight: 700;
  color: #1e3c72;
  font-size: 0.95rem;
`;

const DescriptionText = styled.div`
  max-width: 320px;
  font-size: 0.85rem;
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
`;

// --- Helpers ---

const getStatusVariant = (status) => {
  switch(status) {
    case 'ACTIVE': return 'active';
    case 'INACTIVE': return 'cancelled';
    case 'DRAFT': return 'pending';
    default: return 'default';
  }
};

/**
 * MenuTable Component
 * Displays a list of menu collections with administrative controls.
 */
export const MenuTable = ({ menus, onEdit, onDelete, onViewDishes }) => {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell>Collection Name</TableHeaderCell>
          <TableHeaderCell>Description</TableHeaderCell>
          <TableHeaderCell>Status</TableHeaderCell>
          <TableHeaderCell align="center">Actions</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {menus.map((menu) => (
          <TableRow key={menu.uid}>
            <TableCell>
              <MenuName title={menu.name}>{menu.name}</MenuName>
            </TableCell>
            
            <TableCell>
              <DescriptionText title={menu.description}>
                {menu.description || 'No description provided.'}
              </DescriptionText>
            </TableCell>
            
            <TableCell>
              <StatusBadge status={getStatusVariant(menu.status)}>
                {menu.status?.toLowerCase() || 'unknown'}
              </StatusBadge>
            </TableCell>
            
            <TableCell>
              <ActionGroup>
                {onViewDishes && (
                  <ActionButton 
                    onClick={() => onViewDishes(menu)} 
                    title="Manage Dishes"
                    $variant="success"
                  >
                    <MdRestaurantMenu />
                  </ActionButton>
                )}
                
                <ActionButton 
                  onClick={() => onEdit(menu)} 
                  title="Edit Settings"
                >
                  <MdEdit />
                </ActionButton>
                
                <ActionButton 
                  $variant="danger" 
                  onClick={() => onDelete(menu)} 
                  title="Delete Collection"
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