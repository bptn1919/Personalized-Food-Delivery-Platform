import React from 'react';
import styled from 'styled-components';
import { FilterPanel, FilterRow, FilterItem } from '../common/FilterPanel';

// --- Styled Form Components ---

const InputGroup = styled.div`
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;

  svg {
    position: absolute;
    left: 12px;
    color: #94a3b8;
    font-size: 1.1rem;
  }
`;

const StyledInput = styled.input`
  width: 100%;
  padding: 10px 12px 10px 38px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  font-size: 0.9rem;
  color: #1e293b;
  background: #f8fafc;
  transition: all 0.2s ease;

  &:focus {
    outline: none;
    border-color: #1e3c72;
    background: white;
    box-shadow: 0 0 0 4px rgba(30, 60, 114, 0.1);
  }

  &::placeholder {
    color: #cbd5e1;
  }
`;

const StyledSelect = styled.select`
  width: 100%;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  font-size: 0.9rem;
  color: #1e293b;
  background: #f8fafc;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394a3b8'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 16px;

  &:focus {
    outline: none;
    border-color: #1e3c72;
    box-shadow: 0 0 0 4px rgba(30, 60, 114, 0.1);
  }
`;

/**
 * OrderFilters Component
 * Advanced filtering suite for administrative order oversight
 */
export const OrderFilters = ({ 
  show, 
  filters, 
  statusList, 
  paymentMethods,
  paymentStatusList,
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
      title="Advanced Order Search"
    >
      {/* Row 1: Primary Statuses */}
      <FilterRow>
        <FilterItem label="Order Status">
          <StyledSelect 
            value={filters.status}
            onChange={(e) => onFilterChange('status', e.target.value)}
          >
            {statusList.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </StyledSelect>
        </FilterItem>

        <FilterItem label="Payment Method">
          <StyledSelect 
            value={filters.payment_method}
            onChange={(e) => onFilterChange('payment_method', e.target.value)}
          >
            {paymentMethods.map(p => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </StyledSelect>
        </FilterItem>

        <FilterItem label="Payment Status">
          <StyledSelect 
            value={filters.payment_status}
            onChange={(e) => onFilterChange('payment_status', e.target.value)}
          >
            {paymentStatusList.map(p => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </StyledSelect>
        </FilterItem>
      </FilterRow>

      {/* Row 2: Stakeholder Information */}
      <FilterRow>
        <FilterItem label="Customer Email">
          <InputGroup>
            <StyledInput 
              type="email" 
              placeholder="e.g., user@example.com"
              value={filters.customer_email}
              onChange={(e) => onFilterChange('customer_email', e.target.value)}
            />
          </InputGroup>
        </FilterItem>

        <FilterItem label="Chef Email">
          <InputGroup>
            <StyledInput 
              type="email" 
              placeholder="e.g., chef@kitchen.com"
              value={filters.chef_email}
              onChange={(e) => onFilterChange('chef_email', e.target.value)}
            />
          </InputGroup>
        </FilterItem>
      </FilterRow>

      {/* Row 3: Date Range Selection */}
      <FilterRow>
        <FilterItem label="Starting Date">
          <InputGroup>
            <StyledInput 
              type="date" 
              value={filters.from_date}
              onChange={(e) => onFilterChange('from_date', e.target.value)}
            />
          </InputGroup>
        </FilterItem>

        <FilterItem label="Ending Date">
          <InputGroup>
            <StyledInput 
              type="date" 
              value={filters.to_date}
              onChange={(e) => onFilterChange('to_date', e.target.value)}
            />
          </InputGroup>
        </FilterItem>
      </FilterRow>
    </FilterPanel>
  );
};