import React from 'react';
import styled from 'styled-components';
import { Modal } from '../common/Modal';

const DetailGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const DetailSection = styled.div`
  margin-bottom: 20px;
`;

const SectionTitle = styled.h4`
  font-size: 0.9rem;
  font-weight: 700;
  color: #1e3c72;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e2e8f0;
`;

const DetailRow = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;

  &:last-child {
    border-bottom: none;
  }
`;

const DetailLabel = styled.span`
  font-weight: 600;
  color: #64748b;
  font-size: 0.85rem;
`;

const DetailValue = styled.span`
  color: #1e293b;
  font-weight: 500;
  font-size: 0.9rem;
`;

const CategoryBadge = styled.span`
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  background: ${({ $category }) => {
    switch($category) {
      case 'GRAIN': return '#fef3c7';
      case 'PROTEIN': return '#fee2e2';
      case 'VEGETABLE': return '#dcfce7';
      case 'FRUIT': return '#fce7f3';
      case 'OILFATBUTTER': return '#ffedd5';
      case 'SPICE': return '#ede9fe';
      case 'MILK': return '#cffafe';
      default: return '#f1f5f9';
    }
  }};
  color: ${({ $category }) => {
    switch($category) {
      case 'GRAIN': return '#92400e';
      case 'PROTEIN': return '#991b1b';
      case 'VEGETABLE': return '#166534';
      case 'FRUIT': return '#9d174d';
      case 'OILFATBUTTER': return '#9a3412';
      case 'SPICE': return '#5b21b6';
      case 'MILK': return '#155e75';
      default: return '#475569';
    }
  }};
`;

const BASIC_NUTRITION = [
  { key: 'weight', label: 'Weight', unit: 'g' },
  { key: 'energy', label: 'Energy', unit: 'kcal' },
  { key: 'protein', label: 'Protein', unit: 'g' },
  { key: 'lipid', label: 'Fat', unit: 'g' },
  { key: 'carbohydrate', label: 'Carbohydrate', unit: 'g' },
  { key: 'fiber', label: 'Fiber', unit: 'g' }
];

const MINERALS = [
  { key: 'natri', label: 'Sodium', unit: 'mg' },
  { key: 'kali', label: 'Potassium', unit: 'mg' },
  { key: 'calcium', label: 'Calcium', unit: 'mg' },
  { key: 'phosphorus', label: 'Phosphorus', unit: 'mg' },
  { key: 'fe', label: 'Iron', unit: 'mg' },
  { key: 'mg', label: 'Magnesium', unit: 'mg' },
  { key: 'zn', label: 'Zinc', unit: 'mg' }
];

const VITAMINS = [
  { key: 'retinol', label: 'Vitamin A', unit: 'µg' },
  { key: 'caroten', label: 'Beta-carotene', unit: 'µg' },
  { key: 'vitamin_b_1', label: 'Vitamin B1', unit: 'mg' },
  { key: 'vitamin_b_2', label: 'Vitamin B2', unit: 'mg' },
  { key: 'vitamin_pp', label: 'Niacin', unit: 'mg' },
  { key: 'vitamin_c', label: 'Vitamin C', unit: 'mg' },
  { key: 'cholesterol', label: 'Cholesterol', unit: 'mg' }
];

export const IngredientDetailModal = ({ isOpen, ingredient, onClose }) => {
  if (!ingredient) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={ingredient.name}
      size="large"
    >
      <DetailGrid>
        <div>
          <DetailSection>
            <SectionTitle>Basic Information</SectionTitle>
            <DetailRow>
              <DetailLabel>Category</DetailLabel>
              <DetailValue>
                <CategoryBadge $category={ingredient.category}>
                  {ingredient.category}
                </CategoryBadge>
              </DetailValue>
            </DetailRow>
            <DetailRow>
              <DetailLabel>Source</DetailLabel>
              <DetailValue>{ingredient.source || 'USDA'}</DetailValue>
            </DetailRow>
          </DetailSection>

          <DetailSection>
            <SectionTitle>Basic Nutrition</SectionTitle>
            {BASIC_NUTRITION.map(item => (
              <DetailRow key={item.key}>
                <DetailLabel>{item.label} ({item.unit})</DetailLabel>
                <DetailValue>{ingredient[item.key] || 0}</DetailValue>
              </DetailRow>
            ))}
          </DetailSection>
        </div>

        <div>
          <DetailSection>
            <SectionTitle>Minerals</SectionTitle>
            {MINERALS.map(item => (
              <DetailRow key={item.key}>
                <DetailLabel>{item.label} ({item.unit})</DetailLabel>
                <DetailValue>{ingredient[item.key] || 0}</DetailValue>
              </DetailRow>
            ))}
          </DetailSection>

          <DetailSection>
            <SectionTitle>Vitamins</SectionTitle>
            {VITAMINS.map(item => (
              <DetailRow key={item.key}>
                <DetailLabel>{item.label} ({item.unit})</DetailLabel>
                <DetailValue>{ingredient[item.key] || 0}</DetailValue>
              </DetailRow>
            ))}
          </DetailSection>
        </div>
      </DetailGrid>
    </Modal>
  );
};