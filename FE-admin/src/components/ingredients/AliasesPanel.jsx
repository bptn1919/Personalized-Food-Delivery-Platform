// components/ingredients/AliasesPanel.jsx
import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { MdLink, MdPendingActions, MdRefresh } from 'react-icons/md';
import { Button } from '../common/Button';
import { ingredientService } from '../../services/ingredientService';

const PanelHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 12px;
`;

const CreateForm = styled.div`
  background: #f8fafc;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 16px;
`;

const FormGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
`;

const Select = styled.select`
  padding: 8px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
`;

const Input = styled.input`
  padding: 8px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
`;

const FormActions = styled.div`
  display: flex;
  gap: 12px;
  justify-content: flex-end;
`;

const TableContainer = styled.div`
  background: white;
  border-radius: 16px;
  border: 1px solid #f1f5f9;
  overflow: hidden;
  width: 100%;
  margin-top: 16px;
`;

const StyledTable = styled.table`
  width: 100%;
  border-collapse: collapse;
`;

const Th = styled.th`
  padding: 12px;
  text-align: left;
  background: #f8fafc;
  border-bottom: 2px solid #e2e8f0;
  font-weight: 600;
  color: #475569;
`;

const Td = styled.td`
  padding: 12px;
  border-bottom: 1px solid #f1f5f9;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 40px;
  color: #94a3b8;
`;

export const AliasesPanel = ({ onShowSuggestions }) => {
  const [aliases, setAliases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAlias, setNewAlias] = useState({ ingredient_uid: '', alias: '' });
  const [ingredients, setIngredients] = useState([]);

  const fetchAliases = async () => {
    setLoading(true);
    try {
      const response = await ingredientService.listAliases();
      let aliasesList = [];
      if (Array.isArray(response)) {
        aliasesList = response;
      } else if (response?.data && Array.isArray(response.data)) {
        aliasesList = response.data;
      } else if (response?.content && Array.isArray(response.content)) {
        aliasesList = response.content;
      }
      setAliases(aliasesList);
    } catch (error) {
      console.error('Fetch aliases failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchIngredients = async () => {
    try {
      const response = await ingredientService.getAllIngredients({ page_size: 1000 });
      let ingredientsList = [];
      if (response?.content && Array.isArray(response.content)) {
        ingredientsList = response.content;
      } else if (response?.data?.content && Array.isArray(response.data.content)) {
        ingredientsList = response.data.content;
      }
      setIngredients(ingredientsList);
    } catch (error) {
      console.error('Fetch ingredients failed:', error);
    }
  };

  const handleCreateAlias = async () => {
    if (!newAlias.ingredient_uid || !newAlias.alias) {
      alert('Please select ingredient and enter alias');
      return;
    }
    try {
      await ingredientService.createAlias(newAlias.ingredient_uid, newAlias.alias);
      setShowCreateForm(false);
      setNewAlias({ ingredient_uid: '', alias: '' });
      fetchAliases();
    } catch (error) {
      alert(`Create alias failed: ${error.message}`);
    }
  };

  useEffect(() => {
    fetchAliases();
    fetchIngredients();
  }, []);

  if (loading) return <div style={{ textAlign: 'center', padding: 40 }}>Loading aliases...</div>;

  return (
    <div>
      <PanelHeader>
        <ButtonGroup>
          <Button onClick={() => setShowCreateForm(true)}>
            <MdLink /> Create Alias
          </Button>
        </ButtonGroup>
==
      </PanelHeader>

      {showCreateForm && (
        <CreateForm>
          <h4>Create New Alias</h4>
          <FormGrid>
            <Select 
              value={newAlias.ingredient_uid}
              onChange={(e) => setNewAlias({ ...newAlias, ingredient_uid: e.target.value })}
            >
              <option value="">Select Ingredient</option>
              {ingredients.map(ing => (
                <option key={ing.uid} value={ing.uid}>{ing.name}</option>
              ))}
            </Select>
            <Input 
              type="text"
              placeholder="Alias name (e.g., cheese -> phô mai)"
              value={newAlias.alias}
              onChange={(e) => setNewAlias({ ...newAlias, alias: e.target.value })}
            />
          </FormGrid>
          <FormActions>
            <Button onClick={() => setShowCreateForm(false)}>Cancel</Button>
            <Button $primary onClick={handleCreateAlias}>Create</Button>
          </FormActions>
        </CreateForm>
      )}

      <TableContainer>
        <StyledTable>
          <thead>
            <tr>
              <Th>Original Ingredient</Th>
              <Th>Alias</Th>
            </tr>
          </thead>
          <tbody>
            {aliases.length > 0 ? (
              aliases.map(alias => (
                <tr key={alias.uid}>
                  <Td>{alias.ingredient_name || alias.ingredient?.name}</Td>
                  <Td><code>{alias.alias}</code></Td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={2}>
                  <EmptyState>No aliases found</EmptyState>
                </td>
              </tr>
            )}
          </tbody>
        </StyledTable>
      </TableContainer>
    </div>
  );
};