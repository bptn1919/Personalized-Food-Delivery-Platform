import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { MdSearch, MdAdd, MdRestaurant, MdFastfood } from 'react-icons/md';
import { Modal } from '../common/Modal';
import { Loading } from '../common/Loading';
import { dishService } from '../../services/dishService';
import { formatCurrency } from '../../utils/helpers';
import { DISH_STATUS } from '../../utils/constants';

// --- Styled Components ---

const Content = styled.div`
  padding: 10px 0;
  max-height: 75vh;
  overflow-y: auto;
`;

const SearchBox = styled.div`
  margin-bottom: 20px;
  position: relative;
  
  input {
    width: 100%;
    padding: 12px 16px 12px 44px;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    font-size: 0.95rem;
    background: #f8fafc;
    transition: all 0.2s;
    
    &:focus {
      outline: none;
      border-color: #1e3c72;
      background: white;
      box-shadow: 0 0 0 4px rgba(30, 60, 114, 0.1);
    }
  }
  
  svg {
    position: absolute;
    left: 16px;
    top: 50%;
    transform: translateY(-50%);
    color: #94a3b8;
    font-size: 1.2rem;
  }
`;

const FilterContainer = styled.div`
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
`;

const SelectField = styled.select`
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 0.9rem;
  background: white;
  cursor: pointer;
  
  &:focus {
    outline: none;
    border-color: #1e3c72;
  }
`;

const ListWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 420px;
  overflow-y: auto;
  padding-right: 4px;

  /* Custom Scrollbar */
  &::-webkit-scrollbar { width: 5px; }
  &::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }
`;

const DishCard = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  border-radius: 12px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;

  &:hover {
    background: white;
    border-color: #3b82f6;
    transform: translateX(4px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  }
`;

const DishMeta = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
`;

const Thumb = styled.div`
  width: 52px;
  height: 52px;
  border-radius: 10px;
  overflow: hidden;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #f1f5f9;

  img { width: 100%; height: 100%; object-fit: cover; }
  svg { color: #94a3b8; font-size: 1.5rem; }
`;

const TextDetails = styled.div`
  .name {
    font-weight: 700;
    color: #1e293b;
    font-size: 0.95rem;
  }
  .price {
    font-size: 0.85rem;
    color: #1e3c72;
    font-weight: 600;
    margin-top: 2px;
  }
`;

const AddAction = styled.button`
  padding: 8px 16px;
  background: #1e3c72;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all 0.2s;

  &:hover:not(:disabled) { background: #0f172a; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
`;

const EmptyContainer = styled.div`
  text-align: center;
  padding: 60px 20px;
  color: #94a3b8;
  background: #f8fafc;
  border-radius: 16px;
  border: 2px dashed #e2e8f0;

  svg { font-size: 3rem; margin-bottom: 12px; }
  p { font-weight: 500; }
`;

// --- Component ---

export const AddDishToMenuModal = ({ isOpen, menu, onClose, onAdd, onSuccess }) => {
  const [dishes, setDishes] = useState([]);
  const [filteredDishes, setFilteredDishes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    if (isOpen) fetchDishes();
  }, [isOpen]);

  const fetchDishes = async () => {
    setLoading(true);
    try {
      const response = await dishService.getMyDishes();
      const list = response?.data?.content || response?.content || response || [];
      const availableDishes = list.filter(d => d.status === DISH_STATUS.AVAILABLE);
      setDishes(availableDishes);
      setFilteredDishes(availableDishes);
    } catch (error) {
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let filtered = [...dishes];
    if (searchTerm) {
      filtered = filtered.filter(d => d.name.toLowerCase().includes(searchTerm.toLowerCase()));
    }
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(d => d.category === categoryFilter);
    }
    setFilteredDishes(filtered);
  }, [searchTerm, categoryFilter, dishes]);

  const handleAddDish = async (dish) => {
    if (!menu?.uid || adding) return;
    setAdding(true);
    try {
      await onAdd(menu.uid, dish.uid);
      onClose();
      if (onSuccess) onSuccess();
    } catch (error) {
      alert('Failed to add dish to menu');
    } finally {
      setAdding(false);
    }
  };

  const CATEGORIES = [
    { value: 'all', label: 'All Categories' },
    { value: 'FOOD', label: 'Main Courses' },
    { value: 'BEVERAGES', label: 'Beverages' },
    { value: 'DESSERT', label: 'Desserts' }
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Add Selection to "${menu?.name || 'Menu'}"`}
      size="large"
    >
      <Content>
        <SearchBox>
          <MdSearch />
          <input
            type="text"
            placeholder="Search catalog by product name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </SearchBox>

        <FilterContainer>
          <SelectField 
            value={categoryFilter} 
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            {CATEGORIES.map(cat => (
              <option key={cat.value} value={cat.value}>{cat.label}</option>
            ))}
          </SelectField>
        </FilterContainer>

        {loading ? (
          <Loading text="Syncing catalog data..." />
        ) : filteredDishes.length === 0 ? (
          <EmptyContainer>
            <MdRestaurant />
            <p>No eligible items found in the catalog.</p>
          </EmptyContainer>
        ) : (
          <ListWrapper>
            {filteredDishes.map((dish) => (
              <DishCard key={dish.uid} onClick={() => handleAddDish(dish)}>
                <DishMeta>
                  <Thumb>
                    {dish.public_url ? (
                      <img src={dish.public_url} alt={dish.name} />
                    ) : (
                      <MdFastfood />
                    )}
                  </Thumb>
                  <TextDetails>
                    <div className="name">{dish.name}</div>
                    <div className="price">{formatCurrency(dish.price)}</div>
                  </TextDetails>
                </DishMeta>
                <AddAction disabled={adding}>
                  <MdAdd size={18} /> {adding ? 'Adding...' : 'Select'}
                </AddAction>
              </DishCard>
            ))}
          </ListWrapper>
        )}
      </Content>
    </Modal>
  );
};