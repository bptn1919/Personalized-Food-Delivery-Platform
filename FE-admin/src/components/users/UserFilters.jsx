import React from 'react';
import styled from 'styled-components';
import { MdSearch, MdPersonOutline, MdDateRange } from 'react-icons/md';
import { FilterPanel, FilterRow, FilterItem } from '../common/FilterPanel';

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
    font-size: 1.1rem;
  }
`;

const StyledInput = styled.input`
  width: 100%;
  padding: 10px 14px 10px 42px;
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
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394a3b8'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  background-size: 16px;

  &:focus {
    outline: none;
    border-color: #1e3c72;
    box-shadow: 0 0 0 4px rgba(30, 60, 114, 0.1);
  }
`;

/**
 * UserFilters Component
 * Standardized filtering for Customer and Chef accounts.
 */
export const UserFilters = ({ show, filters, onFilterChange, onReset, onApply, onClose }) => {
  return (
    <FilterPanel 
      show={show} 
      onClose={onClose}
      onApply={onApply}
      onReset={onReset}
      title="Filter User Accounts"
    >
      <FilterRow>
        {/* Identity Search */}
        <FilterItem label="User Identity">
          <InputGroup>
            <StyledInput 
              type="text" 
              placeholder="Name, email, or username..."
              value={filters.search || ''}
              onChange={(e) => onFilterChange('search', e.target.value)}
            />
          </InputGroup>
        </FilterItem>

        {/* Role Filtering */}
        <FilterItem label="Account Role">
          <StyledSelect 
            value={filters.user_type || 'all'}
            onChange={(e) => onFilterChange('user_type', e.target.value === 'all' ? null : e.target.value)}
          >
            <option value="all">All Roles</option>
            <option value="CUSTOMER">Customer / Diner</option>
            <option value="CHEF">Chef / Provider</option>
          </StyledSelect>
        </FilterItem>

        {/* Activity Status */}
        <FilterItem label="Account Status">
          <StyledSelect 
            value={filters.is_active === undefined ? 'all' : filters.is_active.toString()}
            onChange={(e) => {
              const value = e.target.value;
              onFilterChange('is_active', value === 'all' ? undefined : value === 'true');
            }}
          >
            <option value="all">All Statuses</option>
            <option value="true">Active Only</option>
            <option value="false">Inactive Only</option>
          </StyledSelect>
        </FilterItem>
      </FilterRow>

      <FilterRow>
        {/* Registration Date Range */}
        <FilterItem label="Joined From">
          <InputGroup>
            <StyledInput 
              type="date" 
              value={filters.dateFrom || ''}
              onChange={(e) => onFilterChange('dateFrom', e.target.value)}
            />
          </InputGroup>
        </FilterItem>

        <FilterItem label="Joined To">
          <InputGroup>
            <StyledInput 
              type="date" 
              value={filters.dateTo || ''}
              onChange={(e) => onFilterChange('dateTo', e.target.value)}
            />
          </InputGroup>
        </FilterItem>
      </FilterRow>
    </FilterPanel>
  );
};