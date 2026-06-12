import React from 'react';
import styled from 'styled-components';
import { MdVisibility, MdEdit, MdDelete, MdFavorite, MdFavoriteBorder, MdWarning, MdRestore } from 'react-icons/md';
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '../common/Table';

const CategoryBadge = styled.span`
  display: inline-block;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
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

const ActionButton = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  margin: 0 2px;
  border-radius: 8px;
  color: #64748b;
  transition: all 0.2s;

  &:hover {
    background: #f1f5f9;
    color: ${({ $danger }) => $danger ? '#ef4444' : '#1e3c72'};
  }
`;

const EnergyBar = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

const EnergyValue = styled.span`
  font-weight: 600;
  color: #1e3c72;
`;

const EnergyMeter = styled.div`
  width: 60px;
  height: 4px;
  background: #e2e8f0;
  border-radius: 2px;
  overflow: hidden;
`;

const EnergyFill = styled.div`
  width: ${({ $percent }) => Math.min($percent, 100)}%;
  height: 100%;
  background: ${({ $percent }) => 
    $percent > 70 ? '#ef4444' : $percent > 40 ? '#f59e0b' : '#10b981'
  };
  border-radius: 2px;
`;

export const IngredientTable = ({ 
  ingredients, 
  favourites = [], 
  allergies = [],
  onView, 
  onEdit, 
  onDelete,
  onRestore,
  onToggleFavourite,
  onToggleAllergy,
  isAdmin 
}) => {
  const isFavourite = (uid) => favourites.some(f => f.ingredient_uid === uid);
  const isAllergic = (uid) => allergies.some(a => a.ingredient_uid === uid);

  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell>Name</TableHeaderCell>
          <TableHeaderCell>Category</TableHeaderCell>
          <TableHeaderCell>Energy (kcal/100g)</TableHeaderCell>
          <TableHeaderCell>Protein (g)</TableHeaderCell>
          <TableHeaderCell>Fat (g)</TableHeaderCell>
          <TableHeaderCell>Carbs (g)</TableHeaderCell>
          <TableHeaderCell>Actions</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {ingredients.map((item) => (
          <TableRow key={item.uid}>
            <TableCell>
              {item.name}
              {isAllergic(item.uid) && (
                <span style={{ marginLeft: 8, color: '#ef4444' }} title="Allergy">
                  <MdWarning size={14} />
                </span>
              )}
            </TableCell>
            <TableCell>
              <CategoryBadge $category={item.category}>
                {item.category}
              </CategoryBadge>
            </TableCell>
            <TableCell>
              <EnergyBar>
                <EnergyValue>{item.energy || 0}</EnergyValue>
                <EnergyMeter>
                  <EnergyFill $percent={(item.energy || 0) / 10} />
                </EnergyMeter>
              </EnergyBar>
            </TableCell>
            <TableCell>{item.protein || 0}g</TableCell>
            <TableCell>{item.lipid || 0}g</TableCell>
            <TableCell>{item.carbohydrate || 0}g</TableCell>
            <TableCell>
              <ActionButton onClick={() => onView(item)} title="View Details">
                <MdVisibility size={18} />
              </ActionButton>
              
              {!isAdmin && onToggleFavourite && (
                <ActionButton 
                  onClick={() => onToggleFavourite(item)} 
                  title={isFavourite(item.uid) ? 'Remove from Favourites' : 'Add to Favourites'}
                  style={{ color: isFavourite(item.uid) ? '#ef4444' : '#64748b' }}
                >
                  {isFavourite(item.uid) ? <MdFavorite size={18} /> : <MdFavoriteBorder size={18} />}
                </ActionButton>
              )}
              
              {!isAdmin && onToggleAllergy && (
                <ActionButton 
                  onClick={() => onToggleAllergy(item)} 
                  title={isAllergic(item.uid) ? 'Remove from Allergies' : 'Add to Allergies'}
                  $danger={isAllergic(item.uid)}
                >
                  <MdWarning size={18} />
                </ActionButton>
              )}
              
              {isAdmin && (
                <>
                  <ActionButton onClick={() => onEdit(item)} title="Edit">
                    <MdEdit size={18} />
                  </ActionButton>
                  {item.deleted_at ? (
                    <ActionButton 
                      onClick={() => onRestore?.(item)} 
                      title="Restore"
                      style={{ color: '#10b981' }}
                    >
                      <MdRestore size={18} />
                    </ActionButton>
                  ) : (
                    <ActionButton onClick={() => onDelete(item)} title="Delete" $danger>
                      <MdDelete size={18} />
                    </ActionButton>
                  )}
                </>
              )}
            </TableCell>
          </TableRow>
        ))}
        
        {ingredients.length === 0 && (
          <TableRow>
            <TableCell colSpan={7} style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
              No ingredients found
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
};