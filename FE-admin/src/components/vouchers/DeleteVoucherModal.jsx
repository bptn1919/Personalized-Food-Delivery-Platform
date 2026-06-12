import React from 'react';
import styled from 'styled-components';
import { MdWarning, MdLocalOffer } from 'react-icons/md';
import { Modal, ModalFooter } from '../common/Modal';

const MessageWrapper = styled.div`
  display: flex;
  gap: 16px;
  padding: 8px 0;
  align-items: flex-start;
`;

const IconContainer = styled.div`
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 1.5rem;
  background: #fee2e2;
  color: #ef4444;
`;

const TextContent = styled.div`
  line-height: 1.6;
  color: #475569;
  font-size: 0.95rem;

  strong {
    color: #1e293b;
    font-weight: 700;
  }
`;

const VoucherCode = styled.span`
  display: inline-block;
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 8px;
  font-family: monospace;
  font-weight: 700;
  color: #1e3c72;
  font-size: 0.9rem;
  margin-top: 8px;
`;

const WarningBox = styled.div`
  background: #fef3c7;
  border-left: 4px solid #f59e0b;
  padding: 12px;
  margin-top: 16px;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #92400e;

  ul {
    margin: 8px 0 0 20px;
    padding: 0;
  }

  li {
    margin: 4px 0;
  }
`;

export const DeleteVoucherModal = ({ isOpen, onClose, onConfirm, voucher }) => {
  if (!isOpen) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Delete Voucher"
      size="small"
      footer={
        <ModalFooter
          onCancel={onClose}
          onConfirm={onConfirm}
          confirmText="Delete Voucher"
          cancelText="Cancel"
          danger={true}
        />
      }
    >
      <MessageWrapper>
        <IconContainer>
          <MdWarning />
        </IconContainer>
        <TextContent>
          <p>
            Are you sure you want to delete voucher{' '}
            <strong style={{ color: '#dc2626' }}>"{voucher?.code}"</strong>?
          </p>
          <VoucherCode>{voucher?.name}</VoucherCode>
          
          <WarningBox>
            <strong>⚠️ Warning:</strong>
            <ul>
              <li>This voucher will be permanently deleted</li>
              <li>Customers cannot use this code anymore</li>
              <li>This action cannot be undone</li>
            </ul>
          </WarningBox>
        </TextContent>
      </MessageWrapper>
    </Modal>
  );
};