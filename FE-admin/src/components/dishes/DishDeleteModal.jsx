import React from 'react';
import styled from 'styled-components';
import { MdWarning, MdInfo, MdVisibilityOff } from 'react-icons/md';
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
  
  background: ${({ $isReferenced }) => $isReferenced ? '#fef3c7' : '#fee2e2'};
  color: ${({ $isReferenced }) => $isReferenced ? '#d97706' : '#ef4444'};
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

const WarningBox = styled.div`
  background: #fef3c7;
  border-left: 4px solid #f59e0b;
  padding: 12px;
  margin-top: 12px;
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

/**
 * DeleteDishModal Component
 * Handles dish deletion with reference checking
 */
export const DeleteDishModal = ({ isOpen, onClose, onConfirm, onHide, dish, isReferenced }) => {
  
  const getMessage = () => {
    if (isReferenced) {
      return (
        <>
          Cannot delete <strong style={{ color: '#d97706' }}>"{dish?.name}"</strong> because it is referenced in existing orders.
        </>
      );
    }
    
    return (
      <>
        Are you sure you want to <strong style={{ color: '#dc2626' }}>delete</strong> the dish <strong>"{dish?.name}"</strong>?
        The dish will be removed from the menu and cannot be ordered anymore.
      </>
    );
  };

  const getTitle = () => {
    if (isReferenced) {
      return "Cannot Delete Dish";
    }
    return "Delete Dish";
  };

  const getConfirmText = () => {
    if (isReferenced) {
      return "Hide Dish";
    }
    return "Delete Dish";
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
          onConfirm={isReferenced ? onHide : onConfirm}
          confirmText={getConfirmText()}
          cancelText="Cancel"
          danger={!isReferenced}
        />
      }
    >
      <MessageWrapper>
        <IconContainer $isReferenced={isReferenced}>
          {isReferenced ? <MdVisibilityOff /> : <MdWarning />}
        </IconContainer>
        <TextContent>
          <p>{getMessage()}</p>
          {isReferenced && (
            <WarningBox>
              <strong>💡 Suggestion:</strong>
              <ul>
                <li>Hide this dish to remove it from the menu</li>
                <li>Existing orders will not be affected</li>
                <li>You can restore it later if needed</li>
              </ul>
            </WarningBox>
          )}
        </TextContent>
      </MessageWrapper>
    </Modal>
  );
};