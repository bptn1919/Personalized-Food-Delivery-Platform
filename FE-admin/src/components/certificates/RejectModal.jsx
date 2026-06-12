import React, { useState } from 'react';
import styled from 'styled-components';
import { MdErrorOutline, MdSend } from 'react-icons/md';
import { Modal } from '../common/Modal';

const FormContainer = styled.div`
  padding: 8px 0;
`;

const AlertBox = styled.div`
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background: #fff1f2;
  border: 1px solid #ffe4e6;
  border-radius: 12px;
  margin-bottom: 20px;
  color: #991b1b;
  font-size: 0.85rem;
  line-height: 1.4;

  svg {
    font-size: 1.2rem;
    flex-shrink: 0;
  }
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 24px;
`;

const Label = styled.label`
  font-size: 0.9rem;
  color: #1e293b;
  font-weight: 700;

  span {
    color: #64748b;
    font-weight: 400;
  }
`;

const TextArea = styled.textarea`
  padding: 14px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  font-size: 0.95rem;
  min-height: 120px;
  resize: vertical;
  background: #f8fafc;
  transition: all 0.2s ease;

  &:focus {
    outline: none;
    border-color: #ef4444;
    background: white;
    box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.1);
  }

  &::placeholder {
    color: #94a3b8;
  }
`;

const ActionWrapper = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
`;

const Button = styled.button`
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;

  ${({ $isPrimary }) => $isPrimary ? `
    background: #ef4444;
    color: white;
    border: none;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);

    &:hover:not(:disabled) {
      background: #dc2626;
      transform: translateY(-2px);
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      box-shadow: none;
    }
  ` : `
    background: white;
    color: #64748b;
    border: 1px solid #e2e8f0;

    &:hover {
      background: #f8fafc;
      color: #1e293b;
    }
  `}
`;

export const RejectModal = ({ isOpen, onClose, onConfirm, certificateName }) => {
  const [reason, setReason] = useState('');

  const handleConfirm = () => {
    if (!reason.trim()) return;
    onConfirm(reason);
    setReason('');
  };

  const isInvalid = !reason.trim();

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Reject Approval"
      size="small"
    >
      <FormContainer>
        <AlertBox>
          <MdErrorOutline />
          <div>
            You are rejecting the certificate: <strong>{certificateName}</strong>. 
            This reason will be sent directly to the chef for them to review and edit.
          </div>
        </AlertBox>

        <FormGroup>
          <Label>Rejection Reason <span>(Required)</span></Label>
          <TextArea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Enter detailed reason (e.g., Image is blurry, Certificate is expired...)"
          />
        </FormGroup>

        <ActionWrapper>
          <Button type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button 
            $isPrimary 
            onClick={handleConfirm}
            disabled={isInvalid}
          >
            <MdSend /> Confirm Rejection
          </Button>
        </ActionWrapper>
      </FormContainer>
    </Modal>
  );
};