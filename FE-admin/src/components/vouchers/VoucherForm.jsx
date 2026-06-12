import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Modal } from '../common/Modal';
import { VOUCHER_TYPES, DISCOUNT_TYPES } from '../../utils/constants';

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
  color: #475569;
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

  &:disabled {
    background: #f1f5f9;
    color: #94a3b8;
    cursor: not-allowed;
  }
`;

const Input = styled.input`${CommonInputStyles}`;
const Select = styled.select`${CommonInputStyles} cursor: pointer;`;
const TextArea = styled.textarea`${CommonInputStyles} min-height: 100px; resize: vertical;`;

const FormRow = styled.div`
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  
  @media (min-width: 640px) {
    grid-template-columns: 1fr 1fr;
  }
`;

const CheckboxWrapper = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  cursor: pointer;

  input {
    width: 20px;
    height: 20px;
    cursor: pointer;
    accent-color: #1e3c72;
  }

  label {
    cursor: pointer;
    font-weight: 600;
    color: #1e293b;
    margin: 0;
  }
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

export const VoucherForm = ({ isOpen, onClose, onSubmit, initialData = null }) => {
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    description: '',
    voucher_type: VOUCHER_TYPES.PLATFORM_SUBTOTAL,
    discount_type: DISCOUNT_TYPES.PERCENTAGE,
    discount_value: '',
    max_discount_amount: '',
    min_order_amount: '0',
    start_date: '',
    end_date: '',
    usage_limit: '',
    usage_limit_per_user: 1,
    is_active: true
  });

  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setFormData({
          ...initialData,
          description: initialData.description || '',
          max_discount_amount: initialData.max_discount_amount ?? '',
          usage_limit: initialData.usage_limit ?? '',
          start_date: initialData.start_date ? new Date(initialData.start_date).toISOString().slice(0, 16) : '',
          end_date: initialData.end_date ? new Date(initialData.end_date).toISOString().slice(0, 16) : '',
          is_active: initialData.is_active ?? true
        });
      } else {
        setFormData({
          code: '', name: '', description: '', voucher_type: VOUCHER_TYPES.PLATFORM_SUBTOTAL,
          discount_type: DISCOUNT_TYPES.PERCENTAGE, discount_value: '', max_discount_amount: '',
          min_order_amount: '0', start_date: '', end_date: '', usage_limit: '', usage_limit_per_user: 1, is_active: true
        });
      }
    }
  }, [isOpen, initialData]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const isEdit = !!initialData;
  const isPercentage = formData.discount_type === DISCOUNT_TYPES.PERCENTAGE;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={isEdit ? 'Update Voucher Campaign' : 'Configure New Voucher'} size="large">
      <Form onSubmit={(e) => { e.preventDefault(); onSubmit(formData); }}>
        <FormRow>
          <FormGroup>
            <Label>Promo Code <span>*</span></Label>
            <Input name="code" value={formData.code} onChange={handleChange} required maxLength="50" placeholder="e.g. SUMMERDEAL2026" />
          </FormGroup>
          <FormGroup>
            <Label>Campaign Name <span>*</span></Label>
            <Input name="name" value={formData.name} onChange={handleChange} required maxLength="100" placeholder="e.g. Summer Solstice Sale" />
          </FormGroup>
        </FormRow>

        <FormGroup>
          <Label>Public Description</Label>
          <TextArea name="description" value={formData.description} onChange={handleChange} placeholder="Describe the voucher benefits to customers..." />
        </FormGroup>

        <FormRow>
          <FormGroup>
            <Label>Voucher Scope <span>*</span></Label>
            <Select name="voucher_type" value={formData.voucher_type} onChange={handleChange} required>
              <option value={VOUCHER_TYPES.PLATFORM_SUBTOTAL}>Platform (Subtotal)</option>
              <option value={VOUCHER_TYPES.PLATFORM_SHIPPING}>Platform (Shipping)</option>
            </Select>
          </FormGroup>
          <FormGroup>
            <Label>Reward Model <span>*</span></Label>
            <Select name="discount_type" value={formData.discount_type} onChange={handleChange} required>
              <option value={DISCOUNT_TYPES.PERCENTAGE}>Percentage (%)</option>
              <option value={DISCOUNT_TYPES.FIXED_AMOUNT}>Fixed Amount (VND)</option>
            </Select>
          </FormGroup>
        </FormRow>

        <FormRow>
          <FormGroup>
            <Label>Reward Value <span>*</span></Label>
            <Input
              type="number"
              name="discount_value"
              value={formData.discount_value}
              onChange={handleChange}
              required
              min="0"
              max={isPercentage ? "100" : undefined}
              step={isPercentage ? "0.1" : "1"}
              placeholder={isPercentage ? "10%" : "5.00"}
            />
            <HelperText>{isPercentage ? "Rate between 0 and 100%" : "Flat currency deduction"}</HelperText>
          </FormGroup>
          <FormGroup>
            <Label>Maximum Cap (VND)</Label>
            <Input
              type="number"
              name="max_discount_amount"
              value={formData.max_discount_amount}
              onChange={handleChange}
              disabled={!isPercentage}
              placeholder={isPercentage ? "Cap the discount" : "Not applicable"}
            />
            <HelperText>Limits the total savings for percentage models</HelperText>
          </FormGroup>
        </FormRow>

        <FormRow>
          <FormGroup>
            <Label>Minimum Basket Value <span>*</span></Label>
            <Input type="number" name="min_order_amount" value={formData.min_order_amount} onChange={handleChange} required min="0" placeholder="0.00" />
            <HelperText>Customer must spend this much to qualify</HelperText>
          </FormGroup>
          <FormGroup>
            <Label>Global Usage Limit</Label>
            <Input type="number" name="usage_limit" value={formData.usage_limit} onChange={handleChange} min="1" placeholder="Unlimited" />
            <HelperText>Total number of redemptions allowed platform-wide</HelperText>
          </FormGroup>
        </FormRow>

        <FormRow>
          <FormGroup>
            <Label>Start Date <span>*</span></Label>
            <Input type="datetime-local" name="start_date" value={formData.start_date} onChange={handleChange} required />
          </FormGroup>
          <FormGroup>
            <Label>End Date <span>*</span></Label>
            <Input type="datetime-local" name="end_date" value={formData.end_date} onChange={handleChange} required min={formData.start_date} />
          </FormGroup>
        </FormRow>

        <FormRow>
          <FormGroup>
            <Label>User Usage Limit</Label>
            <Input type="number" name="usage_limit_per_user" value={formData.usage_limit_per_user} onChange={handleChange} min="1" placeholder="1" />
            <HelperText>Max redemptions per individual account</HelperText>
          </FormGroup>
          <CheckboxWrapper>
            <input type="checkbox" name="is_active" id="is_active" checked={formData.is_active} onChange={handleChange} />
            <label htmlFor="is_active">Live Campaign</label>
          </CheckboxWrapper>
        </FormRow>

        <ButtonGroup>
          <Button type="button" onClick={onClose}>Discard</Button>
          <Button type="submit" $primary>{isEdit ? 'Save Changes' : 'Activate Campaign'}</Button>
        </ButtonGroup>
      </Form>
    </Modal>
  );
};