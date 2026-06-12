// components/dishLocations/LocationFormModal.jsx
import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
`;

const Label = styled.label`
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
`;

const Input = styled.input`
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;

  &:focus {
    outline: none;
    border-color: #1e3c72;
  }
`;

const Select = styled.select`
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  background: white;
  cursor: pointer;
`;

const ActionButtons = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
`;

const HelpText = styled.p`
  font-size: 0.7rem;
  color: #64748b;
  margin-top: 4px;
  margin-bottom: 0;
`;

const TYPE_OPTIONS = [
  { value: 'REGION', label: 'Region (Largest)', order: 1 },
  { value: 'SUBREGION', label: 'Subregion', order: 2 },
  { value: 'COUNTRY', label: 'Country (Smallest)', order: 3 },
];

export const LocationFormModal = ({ isOpen, onClose, onSubmit, initialData = null, existingLocations = [] }) => {
  const [formData, setFormData] = useState({
    name: '',
    type: 'REGION',
    parent_id: null
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || '',
        type: initialData.type || 'REGION',
        parent_id: initialData.parent_id || null
      });
    } else {
      setFormData({
        name: '',
        type: 'REGION',
        parent_id: null
      });
    }
  }, [initialData, isOpen]);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      alert('Please enter location name');
      return;
    }
    
    setLoading(true);
    try {
      await onSubmit(formData);
      onClose();
    } catch (error) {
      console.error('Submit failed:', error);
      alert('Submit failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Lọc parent locations (chỉ có thể chọn parent có type nhỏ hơn)
  const typeOrder = { REGION: 1, SUBREGION: 2, COUNTRY: 3 };
  const currentOrder = typeOrder[formData.type];
  
  const availableParents = existingLocations.filter(loc => {
    const locOrder = typeOrder[loc.type];
    // Chỉ hiển thị locations có type nhỏ hơn current
    if (locOrder >= currentOrder) return false;
    // Không hiển thị chính nó khi edit
    if (initialData && loc.id === initialData.id) return false;
    return true;
  });

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initialData ? 'Edit Location' : 'Create New Location'}
      size="small"
    >
      <FormGroup>
        <Label>Location Name *</Label>
        <Input
          type="text"
          value={formData.name}
          onChange={(e) => handleChange('name', e.target.value)}
          placeholder="e.g., Southeast Asia, Vietnam, Ho Chi Minh City"
        />
      </FormGroup>

      <FormGroup>
        <Label>Type *</Label>
        <Select
          value={formData.type}
          onChange={(e) => handleChange('type', e.target.value)}
        >
          {TYPE_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </Select>
        <HelpText>
          Hierarchy: Region (largest) → Subregion → Country (smallest)
        </HelpText>
      </FormGroup>

      {availableParents.length > 0 && (
        <FormGroup>
          <Label>Parent Location</Label>
          <Select
            value={formData.parent_id || ''}
            onChange={(e) => handleChange('parent_id', e.target.value ? parseInt(e.target.value) : null)}
          >
            <option value="">None (Root level)</option>
            {availableParents.map(loc => (
              <option key={loc.id} value={loc.id}>
                {loc.name} ({TYPE_OPTIONS.find(t => t.value === loc.type)?.label})
              </option>
            ))}
          </Select>
          <HelpText>
            Select a parent location to create hierarchy (e.g., Vietnam under Southeast Asia)
          </HelpText>
        </FormGroup>
      )}

      <ActionButtons>
        <Button onClick={onClose}>Cancel</Button>
        <Button $primary onClick={handleSubmit} disabled={loading}>
          {loading ? 'Saving...' : (initialData ? 'Update' : 'Create')}
        </Button>
      </ActionButtons>
    </Modal>
  );
};