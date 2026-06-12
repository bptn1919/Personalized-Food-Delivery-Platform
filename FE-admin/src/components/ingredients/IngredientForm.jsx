import React, { useState, useEffect } from 'react';
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
  transition: all 0.2s ease;

  &:focus {
    outline: none;
    border-color: #1e3c72;
    background: white;
    box-shadow: 0 0 0 3px rgba(30, 60, 114, 0.1);
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
    border-color: #1e3c72;
    box-shadow: 0 0 0 3px rgba(30, 60, 114, 0.1);
  }
`;

const SectionTitle = styled.h4`
  font-size: 0.9rem;
  font-weight: 700;
  color: #1e3c72;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e2e8f0;
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
  { name: 'weight', label: 'Weight', unit: 'g', placeholder: '100', defaultValue: 100 },
  { name: 'energy', label: 'Energy', unit: 'kcal', placeholder: '0' },
  { name: 'protein', label: 'Protein', unit: 'g', placeholder: '0' },
  { name: 'lipid', label: 'Fat', unit: 'g', placeholder: '0' },
  { name: 'carbohydrate', label: 'Carbohydrate', unit: 'g', placeholder: '0' },
  { name: 'fiber', label: 'Fiber', unit: 'g', placeholder: '0' },
  { name: 'natri', label: 'Sodium', unit: 'mg', placeholder: '0' },
  { name: 'kali', label: 'Potassium', unit: 'mg', placeholder: '0' },
  { name: 'cholesterol', label: 'Cholesterol', unit: 'mg', placeholder: '0' },
  { name: 'retinol', label: 'Vitamin A', unit: 'µg', placeholder: '0' },
  { name: 'caroten', label: 'Beta-carotene', unit: 'µg', placeholder: '0' },
  { name: 'vitamin_b_1', label: 'Vitamin B1', unit: 'mg', placeholder: '0' },
  { name: 'vitamin_b_2', label: 'Vitamin B2', unit: 'mg', placeholder: '0' },
  { name: 'vitamin_pp', label: 'Niacin', unit: 'mg', placeholder: '0' },
  { name: 'vitamin_c', label: 'Vitamin C', unit: 'mg', placeholder: '0' },
  { name: 'calcium', label: 'Calcium', unit: 'mg', placeholder: '0' },
  { name: 'phosphorus', label: 'Phosphorus', unit: 'mg', placeholder: '0' },
  { name: 'fe', label: 'Iron', unit: 'mg', placeholder: '0' },
  { name: 'mg', label: 'Magnesium', unit: 'mg', placeholder: '0' },
  { name: 'zn', label: 'Zinc', unit: 'mg', placeholder: '0' }
];

export const IngredientForm = ({ isOpen, onClose, onSubmit, initialData, isAdmin }) => {
  const [formData, setFormData] = useState({
    name: '',
    category: 'GRAIN',
    weight: 100,
    energy: 0,
    protein: 0,
    lipid: 0,
    carbohydrate: 0,
    fiber: 0,
    natri: 0,
    kali: 0,
    cholesterol: 0,
    retinol: 0,
    caroten: 0,
    vitamin_b_1: 0,
    vitamin_b_2: 0,
    vitamin_pp: 0,
    vitamin_c: 0,
    calcium: 0,
    phosphorus: 0,
    fe: 0,
    mg: 0,
    zn: 0,
    source: 'USDA'
  });

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || '',
        category: initialData.category || 'GRAIN',
        weight: initialData.weight || 100,
        energy: initialData.energy || 0,
        protein: initialData.protein || 0,
        lipid: initialData.lipid || 0,
        carbohydrate: initialData.carbohydrate || 0,
        fiber: initialData.fiber || 0,
        natri: initialData.natri || 0,
        kali: initialData.kali || 0,
        cholesterol: initialData.cholesterol || 0,
        retinol: initialData.retinol || 0,
        caroten: initialData.caroten || 0,
        vitamin_b_1: initialData.vitamin_b_1 || 0,
        vitamin_b_2: initialData.vitamin_b_2 || 0,
        vitamin_pp: initialData.vitamin_pp || 0,
        vitamin_c: initialData.vitamin_c || 0,
        calcium: initialData.calcium || 0,
        phosphorus: initialData.phosphorus || 0,
        fe: initialData.fe || 0,
        mg: initialData.mg || 0,
        zn: initialData.zn || 0,
        source: initialData.source || 'USDA'
      });
    } else {
      setFormData({
        name: '',
        category: 'GRAIN',
        weight: 100,
        energy: 0,
        protein: 0,
        lipid: 0,
        carbohydrate: 0,
        fiber: 0,
        natri: 0,
        kali: 0,
        cholesterol: 0,
        retinol: 0,
        caroten: 0,
        vitamin_b_1: 0,
        vitamin_b_2: 0,
        vitamin_pp: 0,
        vitamin_c: 0,
        calcium: 0,
        phosphorus: 0,
        fe: 0,
        mg: 0,
        zn: 0,
        source: 'USDA'
      });
    }
  }, [initialData, isOpen]);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = () => {
    onSubmit(formData);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initialData ? 'Edit Ingredient' : 'Create New Ingredient'}
      size="large"
      footer={
        <ModalFooter
          onCancel={onClose}
          onConfirm={handleSubmit}
          confirmText={initialData ? 'Update' : 'Create'}
          cancelText="Cancel"
        />
      }
    >
      <FormContainer>
        <FormRow>
          <FormGroup>
            <Label>Name *</Label>
            <Input 
              type="text" 
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
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

        <SectionTitle>Basic Nutrition (per 100g)</SectionTitle>
        <FormRow>
          {NUTRITION_FIELDS.slice(0, 6).map(field => (
            <FormGroup key={field.name}>
              <Label>{field.label} ({field.unit})</Label>
              <Input 
                type="number" 
                step="0.01"
                value={formData[field.name]}
                onChange={(e) => handleChange(field.name, parseFloat(e.target.value) || 0)}
                placeholder={field.placeholder}
              />
            </FormGroup>
          ))}
        </FormRow>

        <SectionTitle>Vitamins & Minerals</SectionTitle>
        <FormRow>
          {NUTRITION_FIELDS.slice(6).map(field => (
            <FormGroup key={field.name}>
              <Label>{field.label} ({field.unit})</Label>
              <Input 
                type="number" 
                step="0.01"
                value={formData[field.name]}
                onChange={(e) => handleChange(field.name, parseFloat(e.target.value) || 0)}
                placeholder={field.placeholder}
              />
            </FormGroup>
          ))}
        </FormRow>
      </FormContainer>
    </Modal>
  );
};