import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { MdRestaurantMenu, MdAdd, MdDelete, MdRestaurant, MdInfo, MdFastfood } from 'react-icons/md';
import { Modal } from '../common/Modal';
import { StatusBadge } from '../common/StatusBadge';
import { Loading } from '../common/Loading';
import { menuService } from '../../services/menuService';
import { formatCurrency } from '../../utils/helpers';

// --- Styled Components ---

const ModalContent = styled.div`
  padding: 10px 0;
  max-height: 75vh;
  overflow-y: auto;
  
  /* Custom Scrollbar for better UI */
  &::-webkit-scrollbar { width: 6px; }
  &::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }
`;

const Section = styled.div`
  margin-bottom: 24px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 16px;
  border: 1px solid #f1f5f9;
`;

const SectionHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
`;

const SectionTitle = styled.h4`
  display: flex;
  align-items: center;
  gap: 10px;
  color: #1e3c72;
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;

  svg { color: #3b82f6; font-size: 1.3rem; }
`;

const InfoGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
`;

const InfoItem = styled.div`
  .label {
    font-size: 0.75rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 700;
    margin-bottom: 6px;
  }
  .value {
    font-size: 1rem;
    font-weight: 600;
    color: #1e293b;
    word-break: break-word;
  }
`;

const DishList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const DishCard = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;

  &:hover {
    border-color: #cbd5e1;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  }
`;

const DishInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
`;

const DishThumb = styled.div`
  width: 52px;
  height: 52px;
  border-radius: 10px;
  overflow: hidden;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;

  img { width: 100%; height: 100%; object-fit: cover; }
  svg { color: #94a3b8; font-size: 1.4rem; }
`;

const DishMeta = styled.div`
  .name { font-weight: 700; color: #334155; font-size: 0.95rem; }
  .price { font-size: 0.85rem; color: #1e3c72; font-weight: 600; margin-top: 2px; }
`;

const RemoveButton = styled.button`
  background: #fff1f2;
  color: #e11d48;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: #e11d48;
    color: white;
    transform: scale(1.05);
  }
`;

const AddAction = styled.button`
  padding: 10px 20px;
  background: #1e3c72;
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(30, 60, 114, 0.15);
  transition: all 0.2s;

  &:hover {
    background: #0f172a;
    transform: translateY(-2px);
  }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 40px 20px;
  color: #94a3b8;
  background: white;
  border-radius: 12px;
  border: 2px dashed #e2e8f0;

  svg { font-size: 2.5rem; margin-bottom: 12px; }
  p { font-weight: 500; font-size: 0.95rem; }
`;

// --- Component ---

export const MenuDetailModal = ({ isOpen, menu, onClose, onAddDish, onRemoveDish }) => {
  const [dishes, setDishes] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && menu?.uid) fetchDishes();
  }, [isOpen, menu]);

  const fetchDishes = async () => {
    if (!menu?.uid) return;
    setLoading(true);
    try {
      const response = await menuService.getDishesInMenu(menu.uid);
      const list = response?.data || response || [];
      setDishes(Array.isArray(list) ? list : []);
    } catch (error) {
      console.error('Error loading menu contents:', error);
      setDishes([]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusVariant = (status) => {
    const variants = { 'ACTIVE': 'active', 'INACTIVE': 'cancelled', 'DRAFT': 'pending' };
    return variants[status] || 'default';
  };

  if (!menu) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Menu Configuration"
      size="large"
    >
      <ModalContent>
        {/* Section 1: Overview */}
        <Section>
          <SectionTitle><MdInfo /> Overview</SectionTitle>
          <InfoGrid>
            <InfoItem>
              <div className="label">Menu Title</div>
              <div className="value">{menu.name}</div>
            </InfoItem>
            <InfoItem>
              <div className="label">Deployment Status</div>
              <div className="value">
                <StatusBadge status={getStatusVariant(menu.status)}>
                  {menu.status || 'Unknown'}
                </StatusBadge>
              </div>
            </InfoItem>
            {menu.description && (
              <InfoItem style={{ gridColumn: '1 / -1' }}>
                <div className="label">Internal Description</div>
                <div className="value">{menu.description}</div>
              </InfoItem>
            )}
          </InfoGrid>
        </Section>

        {/* Section 2: Items */}
        <Section>
          <SectionHeader>
            <SectionTitle><MdRestaurantMenu /> Menu Composition</SectionTitle>
            {onAddDish && (
              <AddAction onClick={() => onAddDish(menu)}>
                <MdAdd size={20} /> Add New Item
              </AddAction>
            )}
          </SectionHeader>
          
          {loading ? (
            <Loading text="Retrieving menu items..." />
          ) : dishes.length === 0 ? (
            <EmptyState>
              <MdRestaurant />
              <p>This menu is currently empty.</p>
            </EmptyState>
          ) : (
            <DishList>
              {dishes.map((dish) => (
                <DishCard key={dish.uid}>
                  <DishInfo>
                    <DishThumb>
                      {dish.public_url ? (
                        <img src={dish.public_url} alt={dish.name} />
                      ) : (
                        <MdFastfood />
                      )}
                    </DishThumb>
                    <DishMeta>
                      <div className="name">{dish.name}</div>
                      <div className="price">{formatCurrency(dish.price)}</div>
                    </DishMeta>
                  </DishInfo>
                  
                  {onRemoveDish && (
                    <RemoveButton 
                      onClick={() => onRemoveDish(dish)}
                      title="Remove from menu"
                    >
                      <MdDelete size={18} />
                    </RemoveButton>
                  )}
                </DishCard>
              ))}
            </DishList>
          )}
        </Section>
      </ModalContent>
    </Modal>
  );
};