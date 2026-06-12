// components/dishLocations/DeleteDishLocationModal.jsx
import React from 'react';
import styled from 'styled-components';
import { MdWarning, MdLocationOn } from 'react-icons/md';
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

export const DeleteDishLocationModal = ({ isOpen, onClose, onConfirm, location }) => {
  if (!location) return null;

  const hasChildren = location.children && location.children.length > 0;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Delete Location"
      size="small"
      footer={
        <ModalFooter
          onCancel={onClose}
          onConfirm={onConfirm}
          confirmText="Delete Location"
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
            Are you sure you want to delete the location{' '}
            <strong style={{ color: '#dc2626' }}>"{location.name}"</strong>?
          </p>
          
          {hasChildren && (
            <WarningBox>
              <strong>⚠️ Warning:</strong>
              <ul>
                <li>This location has {location.children.length} child location(s)</li>
                <li>Please delete or reassign child locations first</li>
              </ul>
            </WarningBox>
          )}
          
          <p style={{ marginTop: 12, fontSize: '0.85rem', color: '#64748b' }}>
            Dishes using this location will not be affected, but new dishes cannot select this location.
          </p>
        </TextContent>
      </MessageWrapper>
    </Modal>
  );
};