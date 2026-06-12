import React from 'react';
import styled from 'styled-components';
import { MdSearch } from 'react-icons/md';
import { FilterPanel, FilterRow, FilterItem } from '../common/FilterPanel';
import { DISH_CATEGORIES, DISH_STATUS } from '../../utils/constants';

// --- Styled Components ---

const StyledInputWrapper = styled.div`
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;

  svg {
    position: absolute;
    left: 12px;
    color: #94a3b8;
    font-size: 1.2rem;
  }
`;

const StyledInput = styled.input`
  width: 100%;
  padding: 10px 12px 10px 40px;
  border-radius: 10px;
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
  transition: all 0.2s ease;
  appearance: none; /* Removes default browser arrow */
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394a3b8'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 16px;

  &:focus {
    outline: none;
    border-color: #1e3c72;
    background-color: white;
    box-shadow: 0 0 0 4px rgba(30, 60, 114, 0.1);
  }
`;

/**
 * DishFilters Component
 * Consistent with global dashboard design system
 */
export const DishFilters = ({ 
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
      title="Filter Dish Catalog"
    >
      <FilterRow>
        {/* Category Filter */}
        <FilterItem label="Cuisine Category">
          <StyledSelect 
            value={filters.category}
            onChange={(e) => onFilterChange('category', e.target.value)}
          >
            <option value="all">All Categories</option>
            <option value={DISH_CATEGORIES.FOOD}>Main Courses</option>
            <option value={DISH_CATEGORIES.BEVERAGES}>Beverages</option>
            <option value={DISH_CATEGORIES.DESSERT}>Desserts</option>
          </StyledSelect>
        </FilterItem>

        {/* Status Filter */}
        <FilterItem label="Inventory Status">
          <StyledSelect 
            value={filters.status}
            onChange={(e) => onFilterChange('status', e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value={DISH_STATUS.AVAILABLE}>Active / Available</option>
            <option value={DISH_STATUS.UNAVAILABLE}>Out of Stock / Unavailable</option>
          </StyledSelect>
        </FilterItem>

        {/* Search Filter */}
        <FilterItem label="Quick Search">
          <StyledInputWrapper>
            <StyledInput 
              type="text" 
              placeholder="Search by dish name..."
              value={filters.search || ''}
              onChange={(e) => onFilterChange('search', e.target.value)}
            />
          </StyledInputWrapper>
        </FilterItem>
      </FilterRow>
    </FilterPanel>
  );
};