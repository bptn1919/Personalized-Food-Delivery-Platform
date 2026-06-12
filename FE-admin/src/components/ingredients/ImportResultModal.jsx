import React from 'react';
import styled from 'styled-components';
import { MdError, MdClose, MdCheckCircle } from 'react-icons/md';

const ModalOverlay = styled.div`
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.4); display: flex; align-items: center; justify-content: center;
  z-index: 2000;
`;

const ModalContent = styled.div`
  background: white; border-radius: 12px; width: 100%; max-width: 450px;
  padding: 24px; position: relative; box-shadow: 0 10px 25px rgba(0,0,0,0.1);
`;

const CloseBtn = styled.button`
  position: absolute; top: 16px; right: 16px;
  background: none; border: none; font-size: 20px; color: #94a3b8; cursor: pointer;
`;

const IconWrapper = styled.div`
  display: flex; justify-content: center; margin-bottom: 16px;
  color: ${({ $success }) => $success ? '#10b981' : '#ef4444'};
  font-size: 48px;
`;

const Title = styled.h3`
  text-align: center; margin: 0 0 8px; color: #1e293b;
`;

const ErrorList = styled.div`
  margin-top: 16px; max-height: 200px; overflow-y: auto;
  background: #fff1f2; border-radius: 8px; padding: 12px;
`;

const ErrorItem = styled.div`
  font-size: 0.85rem; color: #991b1b; margin-bottom: 8px; line-height: 1.4;
  &:last-child { margin-bottom: 0; }
  strong { margin-right: 4px; }
`;

export const ImportResultModal = ({ isOpen, onClose, result, titleSuccess = 'Success', titleError = 'Failed' }) => {
  if (!isOpen || !result) return null;

  const data = result.data || result;
  const { total_rows = 0, created_count = 0, failed_count = 0, errors = [] } = data;
  const isSuccess = failed_count === 0 && (total_rows > 0 || created_count > 0);

  return (
    <ModalOverlay onClick={onClose}>
      <ModalContent onClick={e => e.stopPropagation()}>
        <CloseBtn onClick={onClose}><MdClose /></CloseBtn>
        
        <IconWrapper $success={isSuccess}>
          {isSuccess ? <MdCheckCircle /> : <MdError />}
        </IconWrapper>

        <Title>
          {isSuccess ? titleSuccess : titleError}
        </Title>
        
        <p style={{ textAlign: 'center', color: '#64748b', fontSize: '0.9rem', margin: '0 0 16px' }}>
          {isSuccess 
            ? (total_rows > 1 ? `Successfully processed ${created_count} items.` : 'Operation completed successfully.')
            : (total_rows > 1 ? `Failed to process ${failed_count} items out of ${total_rows}.` : 'The operation could not be completed.')}
        </p>

        {failed_count > 0 && (
          <ErrorList>
            {errors.map((err, idx) => (
              <ErrorItem key={idx}>
                {err.row && <strong>Row {err.row}:</strong>} {err.message}
              </ErrorItem>
            ))}
          </ErrorList>
        )}
      </ModalContent>
    </ModalOverlay>
  );
};
