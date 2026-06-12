import React from 'react';
import styled from 'styled-components';
import { FilterPanel, FilterRow, FilterItem } from '../common/FilterPanel';
import { VOUCHER_TYPES, DISCOUNT_TYPES } from '../../utils/constants';

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
 * VoucherFilters Component
 * Advanced campaign filtering for platform and shop promotions.
 */
export const VoucherFilters = ({ 
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
      title="Filter Campaign Vouchers"
    >
      {/* Row 1: Primary Classification */}
      <FilterRow>
        <FilterItem label="Campaign Scope">
          <StyledSelect 
            value={filters.voucher_type}
            onChange={(e) => onFilterChange('voucher_type', e.target.value)}
          >
            <option value="all">All Scopes</option>
            <option value={VOUCHER_TYPES.SHOP_VOUCHER}>Merchant (Shop) Voucher</option>
            <option value={VOUCHER_TYPES.PLATFORM_SUBTOTAL}>Platform (Subtotal)</option>
            <option value={VOUCHER_TYPES.PLATFORM_SHIPPING}>Platform (Shipping)</option>
          </StyledSelect>
        </FilterItem>

        <FilterItem label="Reward Type">
          <StyledSelect 
            value={filters.discount_type}
            onChange={(e) => onFilterChange('discount_type', e.target.value)}
          >
            <option value="all">All Reward Types</option>
            <option value={DISCOUNT_TYPES.PERCENTAGE}>Percentage (%)</option>
            <option value={DISCOUNT_TYPES.FIXED_AMOUNT}>Fixed Amount ($)</option>
          </StyledSelect>
        </FilterItem>

        <FilterItem label="Campaign Status">
          <StyledSelect 
            value={filters.is_active}
            onChange={(e) => onFilterChange('is_active', e.target.value)}
          >
            <option value="all">All Lifecycle</option>
            <option value="true">Active Campaigns</option>
            <option value="false">Inactive / Expired</option>
          </StyledSelect>
        </FilterItem>
      </FilterRow>

      {/* Row 2: Identity Tracking */}
      <FilterRow>
        <FilterItem label="Voucher Code">
          <InputGroup>
            <StyledInput 
              type="text" 
              placeholder="e.g., SUMMER50"
              value={filters.code}
              onChange={(e) => onFilterChange('code', e.target.value)}
            />
          </InputGroup>
        </FilterItem>

        <FilterItem label="Campaign Name">
          <InputGroup>
            <StyledInput 
              type="text" 
              placeholder="Search internal name..."
              value={filters.name}
              onChange={(e) => onFilterChange('name', e.target.value)}
            />
          </InputGroup>
        </FilterItem>
      </FilterRow>

      {/* Row 3: Temporal Range */}
      <FilterRow>
        <FilterItem label="Validity Start">
          <InputGroup>
            <StyledInput 
              type="date" 
              value={filters.from_date}
              onChange={(e) => onFilterChange('from_date', e.target.value)}
            />
          </InputGroup>
        </FilterItem>

        <FilterItem label="Validity End">
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