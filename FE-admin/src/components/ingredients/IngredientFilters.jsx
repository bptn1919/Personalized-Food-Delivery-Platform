import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { FilterPanel, FilterRow, FilterItem } from '../common/FilterPanel';
import { ingredientService } from '../../services/ingredientService';

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
    z-index: 1;
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

const NumberInput = styled.input`
  width: 100%;
  padding: 10px 12px;
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
`;

const AutocompleteDropdown = styled.div`
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  margin-top: 4px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
`;

const AutocompleteItem = styled.div`
  padding: 8px 12px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;

  &:hover {
    background: #f1f5f9;
  }

  .category {
    font-size: 0.7rem;
    color: #64748b;
    background: #f1f5f9;
    padding: 2px 6px;
    border-radius: 12px;
  }
`;

const CATEGORIES = [
  { value: 'all', label: 'All Categories' },
  { value: 'GRAIN', label: 'Grain' },
  { value: 'PROTEIN', label: 'Protein' },
  { value: 'VEGETABLE', label: 'Vegetable' },
  { value: 'FRUIT', label: 'Fruit' },
  { value: 'OILFATBUTTER', label: 'Oil/Fat/Butter' },
  { value: 'SPICE', label: 'Spice' },
  { value: 'MILK', label: 'Milk' }
];

export const IngredientFilters = ({ 
  show, 
  filters, 
  onFilterChange, 
  onReset, 
  onApply, 
  onClose 
}) => {
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const debounceTimer = useRef(null);

  const handleSearchChange = (e) => {
    const value = e.target.value;
    onFilterChange('search', value);
    
    // Clear previous timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
    
    // Hide suggestions if empty
    if (!value.trim() || value.trim().length < 2) {
      setSearchSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    
    // Debounce API call
    debounceTimer.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        const results = await ingredientService.autocompleteIngredients(value, 8);
        if (results && results.length > 0) {
          setSearchSuggestions(results);
          setShowSuggestions(true);
        } else {
          setSearchSuggestions([]);
          setShowSuggestions(false);
        }
      } catch (error) {
        console.error('Autocomplete failed:', error);
        setSearchSuggestions([]);
        setShowSuggestions(false);
      } finally {
        setIsLoading(false);
      }
    }, 300);
  };

  const handleSelectSuggestion = (suggestion) => {
    onFilterChange('search', suggestion.name);
    setSearchSuggestions([]);
    setShowSuggestions(false);
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, []);

  return (
    <FilterPanel 
      show={show} 
      onClose={onClose}
      onApply={onApply}
      onReset={onReset}
      title="Filter Ingredients"
    >
      <FilterRow>
        <FilterItem label="Search">
          <InputGroup>
            <StyledInput 
              type="text" 
              placeholder="Search by name..."
              value={filters.search}
              onChange={handleSearchChange}
              onBlur={() => {
                setTimeout(() => setShowSuggestions(false), 200);
              }}
              onFocus={() => {
                if (filters.search.trim().length > 1 && searchSuggestions.length > 0) {
                  setShowSuggestions(true);
                }
              }}
            />
            {showSuggestions && searchSuggestions.length > 0 && (
              <AutocompleteDropdown>
                {searchSuggestions.map(suggestion => (
                  <AutocompleteItem 
                    key={suggestion.uid} 
                    onClick={() => handleSelectSuggestion(suggestion)}
                  >
                    <span>{suggestion.name}</span>
                    <span className="category">{suggestion.category}</span>
                  </AutocompleteItem>
                ))}
              </AutocompleteDropdown>
            )}
          </InputGroup>
        </FilterItem>

        <FilterItem label="Category">
          <StyledSelect 
            value={filters.categories}
            onChange={(e) => onFilterChange('categories', e.target.value)}
          >
            {CATEGORIES.map(c => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </StyledSelect>
        </FilterItem>
      </FilterRow>

      <FilterRow>
        <FilterItem label="Min Energy (kcal)">
          <InputGroup>
            <NumberInput 
              type="number" 
              placeholder="Min"
              value={filters.min_energy}
              onChange={(e) => onFilterChange('min_energy', e.target.value)}
            />
          </InputGroup>
        </FilterItem>

        <FilterItem label="Max Energy (kcal)">
          <InputGroup>
            <NumberInput 
              type="number" 
              placeholder="Max"
              value={filters.max_energy}
              onChange={(e) => onFilterChange('max_energy', e.target.value)}
            />
          </InputGroup>
        </FilterItem>
      </FilterRow>
    </FilterPanel>
  );
};