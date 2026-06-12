import React from 'react';
import styled from 'styled-components';
import { MdWarning, MdDelete } from 'react-icons/md';
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

export const DeleteCertificateModal = ({ isOpen, onClose, onConfirm, certificate }) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Delete Certificate"
      size="small"
      footer={
        <ModalFooter
          onCancel={onClose}
          onConfirm={onConfirm}
          confirmText="Delete Certificate"
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
            Are you sure you want to <strong>delete</strong> the certificate{' '}
            <strong>"{certificate?.name}"</strong>?
          </p>
          <p style={{ marginTop: '12px', fontSize: '0.85rem', color: '#64748b' }}>
            This action cannot be undone. The certificate will be permanently removed.
          </p>
        </TextContent>
      </MessageWrapper>
    </Modal>
  );
};