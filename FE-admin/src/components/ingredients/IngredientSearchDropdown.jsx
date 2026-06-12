// components/ingredients/IngredientSearchDropdown.jsx
import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { MdSearch, MdInfo } from 'react-icons/md';
import { Button } from '../common/Button';
import { ingredientService } from '../../services/ingredientService';

const SearchContainer = styled.div`
  position: relative;
  margin-bottom: 12px;
`;

const SearchInputWrapper = styled.div`
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
`;

const SearchInput = styled.input`
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 0.9rem;
  padding-right: 40px;

  &:focus {
    outline: none;
    border-color: #1e3c72;
    box-shadow: 0 0 0 3px rgba(30, 60, 114, 0.1);
  }
`;

const ClearButton = styled.button`
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 1rem;
  padding: 4px 8px;

  &:hover {
    color: #ef4444;
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
  max-height: 400px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
`;

const AutocompleteItem = styled.div`
  padding: 12px 16px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f1f5f9;

  &:hover {
    background: #f1f5f9;
  }

  &:last-child {
    border-bottom: none;
  }

  .name {
    font-weight: 500;
    color: #1e293b;
    flex: 1;
  }

  .category {
    font-size: 0.7rem;
    color: #64748b;
    background: #f1f5f9;
    padding: 2px 8px;
    border-radius: 12px;
    margin-right: 8px;
  }
`;

const LoadingIndicator = styled.div`
  text-align: center;
  padding: 12px;
  color: #64748b;
  font-size: 0.85rem;
`;

export const IngredientSearchDropdown = ({ onSelectIngredient, onViewDetail }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceTimer = useRef(null);

  useEffect(() => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    if (!searchQuery.trim() || searchQuery.trim().length < 2) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    debounceTimer.current = setTimeout(async () => {
      setLoading(true);
      try {
        const results = await ingredientService.autocompleteIngredients(searchQuery, 10);
        console.log('✅ Autocomplete results:', results);
        setSuggestions(results || []);
        setShowDropdown(results && results.length > 0);
      } catch (error) {
        console.error('Autocomplete failed:', error);
        setSuggestions([]);
        setShowDropdown(false);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [searchQuery]);

  const handleManualSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const results = await ingredientService.autocompleteIngredients(searchQuery, 15);
      setSuggestions(results || []);
      setShowDropdown(true);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (item) => {
    console.log('✅ Selecting ingredient:', item);
    setSearchQuery('');
    setSuggestions([]);
    setShowDropdown(false);
    onSelectIngredient(item);
  };

  const handleClear = () => {
    setSearchQuery('');
    setSuggestions([]);
    setShowDropdown(false);
  };

  return (
    <SearchContainer>
      <SearchInputWrapper>
        <SearchInput
          type="text"
          placeholder="Search ingredient..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onFocus={() => {
            if (suggestions.length > 0 && searchQuery.trim().length >= 2) {
              setShowDropdown(true);
            }
          }}
          onBlur={() => {
            setTimeout(() => setShowDropdown(false), 200);
          }}
        />
        <Button onClick={handleManualSearch} disabled={loading} style={{ width: '80px' }}>
          {loading ? '...' : 'Search'}
        </Button>
      </SearchInputWrapper>
      
      {searchQuery && (
        <ClearButton onClick={handleClear}>
          ✕
        </ClearButton>
      )}
      
      {showDropdown && searchQuery.trim().length >= 2 && (
        <AutocompleteDropdown>
          {loading ? (
            <LoadingIndicator>Loading...</LoadingIndicator>
          ) : suggestions.length > 0 ? (
            suggestions.map((item) => (
              <AutocompleteItem 
                key={item.uid} 
                onClick={() => handleSelect(item)}
              >
                <span className="name">{item.name}</span>
                <span className="category">{item.category}</span>
                <Button 
                  size="small" 
                  variant="secondary"
                  onClick={(e) => {
                    e.stopPropagation();
                    onViewDetail(item);
                  }}
                  style={{ padding: '2px 6px', minWidth: 'auto' }}
                >
                  <MdInfo size={14} />
                </Button>
              </AutocompleteItem>
            ))
          ) : (
            <div style={{ padding: 12, textAlign: 'center', color: '#94a3b8' }}>
              No ingredients found
            </div>
          )}
        </AutocompleteDropdown>
      )}
    </SearchContainer>
  );
};