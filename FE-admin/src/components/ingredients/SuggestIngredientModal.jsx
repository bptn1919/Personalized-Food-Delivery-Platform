import React, { useState } from 'react';
import styled from 'styled-components';
import { Modal, ModalFooter } from '../common/Modal';

const FormContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const FormRow = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
`;

const Label = styled.label`
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const Input = styled.input`
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  font-size: 0.9rem;
  color: #1e293b;
  background: #f8fafc;

  &:focus {
    outline: none;
    border-color: #10b981;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
  }
`;

const Select = styled.select`
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  font-size: 0.9rem;
  color: #1e293b;
  background: #f8fafc;
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: #10b981;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
  }
`;

const Textarea = styled.textarea`
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  font-size: 0.9rem;
  color: #1e293b;
  background: #f8fafc;
  resize: vertical;
  min-height: 80px;

  &:focus {
    outline: none;
    border-color: #10b981;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
  }
`;

const SectionTitle = styled.h4`
  font-size: 0.9rem;
  font-weight: 700;
  color: #10b981;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e2e8f0;
`;

const WarningBox = styled.div`
  background: #fef3c7;
  border-left: 4px solid #f59e0b;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;

  p {
    margin: 0;
    font-size: 0.85rem;
    color: #92400e;
  }
`;

const CATEGORIES = [
  { value: 'GRAIN', label: 'Grain' },
  { value: 'PROTEIN', label: 'Protein' },
  { value: 'VEGETABLE', label: 'Vegetable' },
  { value: 'FRUIT', label: 'Fruit' },
  { value: 'OILFATBUTTER', label: 'Oil/Fat/Butter' },
  { value: 'SPICE', label: 'Spice' },
  { value: 'MILK', label: 'Milk' }
];

const NUTRITION_FIELDS = [
  { name: 'energy', label: 'Energy', unit: 'kcal' },
  { name: 'protein', label: 'Protein', unit: 'g' },
  { name: 'lipid', label: 'Fat', unit: 'g' },
  { name: 'carbohydrate', label: 'Carbohydrate', unit: 'g' },
  { name: 'fiber', label: 'Fiber', unit: 'g' },
  { name: 'natri', label: 'Sodium', unit: 'mg' },
  { name: 'kali', label: 'Potassium', unit: 'mg' }
];

export const SuggestIngredientModal = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    custom_name: '',
    category: 'GRAIN',
    description: '',
    weight: 100,
    energy: 0,
    protein: 0,
    lipid: 0,
    carbohydrate: 0,
    fiber: 0,
    natri: 0,
    kali: 0
  });

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = () => {
    // Gọi API suggest ingredient
    onSuccess(formData);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Suggest New Ingredient"
      size="large"
      footer={
        <ModalFooter
          onCancel={onClose}
          onConfirm={handleSubmit}
          confirmText="Submit Suggestion"
          cancelText="Cancel"
        />
      }
    >
      <FormContainer>
        <WarningBox>
          <p>⚠️ Please provide accurate nutritional information. Your suggestion will be reviewed by admin before being added to the system.</p>
        </WarningBox>

        <FormRow>
          <FormGroup>
            <Label>Ingredient Name *</Label>
            <Input 
              type="text" 
              value={formData.custom_name}
              onChange={(e) => handleChange('custom_name', e.target.value)}
              placeholder="Enter ingredient name"
              required
            />
          </FormGroup>
          <FormGroup>
            <Label>Category *</Label>
            <Select 
              value={formData.category}
              onChange={(e) => handleChange('category', e.target.value)}
            >
              {CATEGORIES.map(c => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </Select>
          </FormGroup>
        </FormRow>

        <FormGroup>
          <Label>Description (Optional)</Label>
          <Textarea 
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            placeholder="Describe the ingredient, its common uses, etc..."
          />
        </FormGroup>

        <SectionTitle>Nutrition Information (per 100g)</SectionTitle>
        <FormRow>
          <FormGroup>
            <Label>Weight (g)</Label>
            <Input 
              type="number" 
              value={formData.weight}
              onChange={(e) => handleChange('weight', parseFloat(e.target.value) || 100)}
              placeholder="100"
            />
          </FormGroup>
          {NUTRITION_FIELDS.map(field => (
            <FormGroup key={field.name}>
              <Label>{field.label} ({field.unit})</Label>
              <Input 
                type="number" 
                step="0.01"
                value={formData[field.name]}
                onChange={(e) => handleChange(field.name, parseFloat(e.target.value) || 0)}
                placeholder="0"
              />
            </FormGroup>
          ))}
        </FormRow>
      </FormContainer>
    </Modal>
  );
};