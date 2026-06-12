import React from 'react';
import styled from 'styled-components';
import { MdWarning, MdInfo } from 'react-icons/md';
import { Modal, ModalFooter } from '../common/Modal';

// --- Styled Components ---

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
  
  /* Semantic background and icon colors */
  background: ${({ $danger }) => ($danger ? '#fee2e2' : '#eff6ff')};
  color: ${({ $danger }) => ($danger ? '#ef4444' : '#3b82f6')};
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

/**
 * ConfirmModal Component
 * Standardized for sensitive administrative actions.
 */
export const ConfirmModal = ({ isOpen, onClose, onConfirm, action, userName }) => {
  
  const isDanger = action === 'deactivate';

  const getMessage = () => {
    switch(action) {
      case 'deactivate':
        return (
          <>
            Are you sure you want to <strong>deactivate</strong> the user account for <strong>{userName}</strong>? 
            The user will no longer be able to log in or access the platform.
          </>
        );
      case 'activate':
        return (
          <>
            Are you sure you want to <strong>activate</strong> the user account for <strong>{userName}</strong>? 
            Access permissions will be restored immediately.
          </>
        );
      default:
        return null;
    }
  };

  const getTitle = () => {
    switch(action) {
      case 'deactivate': return 'Deactivate Account';
      case 'activate': return 'Reactivate Account';
      default: return 'Confirm Action';
    }
  };

  const getConfirmText = () => {
    switch(action) {
      case 'deactivate': return 'Deactivate User';
      case 'activate': return 'Activate User';
      default: return 'Confirm';
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={getTitle()}
      size="small"
      footer={
        <ModalFooter
          onCancel={onClose}
          onConfirm={onConfirm}
          confirmText={getConfirmText()}
          cancelText="Cancel"
          danger={isDanger}
        />
      }
    >
      <MessageWrapper>
        <IconContainer $danger={isDanger}>
          {isDanger ? <MdWarning /> : <MdInfo />}
        </IconContainer>
        <TextContent>
          <p>{getMessage()}</p>
        </TextContent>
      </MessageWrapper>
    </Modal>
  );
};