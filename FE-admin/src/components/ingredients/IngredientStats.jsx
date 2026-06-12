import React from 'react';
import styled from 'styled-components';
import { 
  MdLocalDining, MdGrain, MdFastfood, MdGrass, MdLunchDining, 
  MdOilBarrel, MdLocalFlorist, MdLiquor 
} from 'react-icons/md';
import { StatCard } from '../common/StatCard';

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;

  @media (max-width: 1200px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const CATEGORY_CONFIG = [
  { key: 'total', title: 'Total Ingredients', icon: MdLocalDining, color: '#1e3c72' },
  { key: 'grain', title: 'Grains', icon: MdGrain, color: '#f59e0b' },
  { key: 'protein', title: 'Proteins', icon: MdFastfood, color: '#ef4444' },
  { key: 'vegetable', title: 'Vegetables', icon: MdGrass, color: '#10b981' },
  { key: 'fruit', title: 'Fruits', icon: MdLunchDining, color: '#ec489a' },
  { key: 'oilFatButter', title: 'Oils & Fats', icon: MdOilBarrel, color: '#f97316' },
  { key: 'spice', title: 'Spices', icon: MdLocalFlorist, color: '#8b5cf6' },
  { key: 'milk', title: 'Milk & Dairy', icon: MdLiquor, color: '#06b6d4' }
];

export const IngredientStats = ({ stats }) => {
  return (
    <StatsGrid>
      {CATEGORY_CONFIG.map((config) => {
        const Icon = config.icon;
        const value = stats[config.key] || 0;
        
        return (
          <StatCard
            key={config.key}
            title={config.title}
            value={value.toLocaleString()}
            icon={<Icon />}
            color={config.color}
          />
        );
      })}
    </StatsGrid>
  );
};