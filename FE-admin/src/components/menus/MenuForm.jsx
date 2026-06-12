import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Modal } from '../common/Modal';
import { MENU_STATUS } from '../../utils/constants';

// --- Styled Components ---

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 10px 0;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const Label = styled.label`
  font-size: 0.85rem;
  color: #475569; /* Slate 600 */
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 4px;

  span { color: #ef4444; }
`;

const CommonInputStyles = `
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  font-size: 0.95rem;
  color: #1e293b;
  background: #f8fafc;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  &:focus {
    outline: none;
    border-color: #1e3c72;
    background: white;
    box-shadow: 0 0 0 4px rgba(30, 60, 114, 0.1);
  }

  &::placeholder { color: #cbd5e1; }
`;

const Input = styled.input`${CommonInputStyles}`;

const Select = styled.select`
  ${CommonInputStyles}
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394a3b8'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 16px center;
  background-size: 16px;
`;

const TextArea = styled.textarea`
  ${CommonInputStyles}
  min-height: 120px;
  resize: vertical;
`;

const HelperText = styled.small`
  color: #64748b;
  font-size: 0.75rem;
  line-height: 1.4;
`;

const ButtonGroup = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 10px;
  padding-top: 20px;
  border-top: 1px solid #f1f5f9;
`;

const Button = styled.button`
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;

  ${({ $primary }) => $primary ? `
    background: #1e3c72;
    color: white;
    border: none;
    box-shadow: 0 4px 12px rgba(30, 60, 114, 0.2);
    &:hover { background: #2a5298; transform: translateY(-2px); }
  ` : `
    background: white;
    color: #64748b;
    border: 1px solid #e2e8f0;
    &:hover { background: #f8fafc; }
  `}
`;

// --- Component ---

export const MenuForm = ({ isOpen, onClose, onSubmit, initialData = null }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    status: MENU_STATUS.DRAFT,
  });

  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setFormData({
          name: initialData.name || '',
          description: initialData.description || '',
          status: initialData.status || MENU_STATUS.DRAFT,
        });
      } else {
        setFormData({ name: '', description: '', status: MENU_STATUS.DRAFT });
      }
    }
  }, [isOpen, initialData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const isEdit = !!initialData;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? 'Update Menu Collection' : 'Create New Collection'}
      size="large"
    >
      <Form onSubmit={(e) => { e.preventDefault(); onSubmit(formData); }}>
        <FormGroup>
          <Label>Collection Name <span>*</span></Label>
          <Input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            maxLength="100"
            placeholder="e.g., Seasonal Summer Specials"
          />
        </FormGroup>

        <FormGroup>
          <Label>Public Description</Label>
          <TextArea
            name="description"
            value={formData.description}
            onChange={handleChange}
            maxLength="500"
            placeholder="Describe the theme or specific details of this collection..."
          />
        </FormGroup>

        <FormGroup>
          <Label>Publishing Status</Label>
          <Select
            name="status"
            value={formData.status}
            onChange={handleChange}
          >
            <option value={MENU_STATUS.DRAFT}>Draft (Internal Use)</option>
            <option value={MENU_STATUS.ACTIVE}>Live (Visible to Customers)</option>
            <option value={MENU_STATUS.INACTIVE}>Offline (Hidden)</option>
          </Select>
          <HelperText>
            * Note: Collections set to "Live" will be immediately accessible on the storefront.
          </HelperText>
        </FormGroup>

        <ButtonGroup>
          <Button type="button" onClick={onClose}>Cancel</Button>
          <Button type="submit" $primary>
            {isEdit ? 'Save Changes' : 'Publish Collection'}
          </Button>
        </ButtonGroup>
      </Form>
    </Modal>
  );
};