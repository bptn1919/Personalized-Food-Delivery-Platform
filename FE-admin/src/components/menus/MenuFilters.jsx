import React from 'react';
import styled from 'styled-components';
import { FilterPanel, FilterRow, FilterItem } from '../common/FilterPanel';
import { MENU_STATUS } from '../../utils/constants';

// --- Styled Form Components ---

const InputGroup = styled.div`
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;

  svg {
    position: absolute;
    left: 14px;
    color: #94a3b8;
    font-size: 1.2rem;
  }
`;

const StyledInput = styled.input`
  width: 100%;
  padding: 10px 14px 10px 44px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  font-size: 0.9rem;
  color: #1e293b;
  background: #f8fafc;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  &:focus {
    outline: none;
    border-color: #1e3c72;
    background: white;
    box-shadow: 0 0 0 4px rgba(30, 60, 114, 0.1);
  }

  &::placeholder {
    color: #94a3b8;
  }
`;

const StyledSelect = styled.select`
  width: 100%;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  font-size: 0.9rem;
  color: #1e293b;
  background: #f8fafc;
  cursor: pointer;
  appearance: none; /* Removes native arrow */
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394a3b8'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  background-size: 16px;
  transition: all 0.2s ease;

  &:focus {
    outline: none;
    border-color: #1e3c72;
    background-color: white;
    box-shadow: 0 0 0 4px rgba(30, 60, 114, 0.1);
  }
`;

/**
 * MenuFilters Component
 * Refined for high-performance dashboard layouts
 */
export const MenuFilters = ({ 
  show, 
  filters, 
  onFilterChange, 
  onReset, 
  onApply, 
  onClose 
}) => {
  return (
    <FilterPanel 
      show={show} 
      onClose={onClose}
      onApply={onApply}
      onReset={onReset}
      title="Filter Menu Collections"
    >
      <FilterRow>
        {/* Availability Status Filter */}
        <FilterItem label="Publication Status">
          <StyledSelect 
            value={filters.status}
            onChange={(e) => onFilterChange('status', e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value={MENU_STATUS.ACTIVE}>Live / Active</option>
            <option value={MENU_STATUS.INACTIVE}>Offline / Inactive</option>
            <option value={MENU_STATUS.DRAFT}>Draft Mode</option>
          </StyledSelect>
        </FilterItem>

        {/* Name Search Filter */}
        <FilterItem label="Quick Search">
          <InputGroup>
            <StyledInput 
              type="text" 
              placeholder="Search by collection name..."
              value={filters.search || ''}
              onChange={(e) => onFilterChange('search', e.target.value)}
            />
          </InputGroup>
        </FilterItem>
      </FilterRow>
    </FilterPanel>
  );
};