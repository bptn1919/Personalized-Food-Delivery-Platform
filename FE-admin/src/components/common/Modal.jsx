import React, { useEffect } from 'react';
import styled, { keyframes } from 'styled-components';
import { MdClose } from 'react-icons/md';
import { Button } from './Button';

// Animations
const fadeIn = keyframes`
  from { opacity: 0; }
  to { opacity: 1; }
`;

const slideUp = keyframes`
  from { opacity: 0; transform: translateY(20px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
`;

const Overlay = styled.div`
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.65); // Màu Slate đậm cho chiều sâu
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
  animation: ${fadeIn} 0.3s ease-out;
`;

const ModalContainer = styled.div`
  background: white;
  width: 100%;
  max-width: ${({ $size }) => {
    if ($size === 'small') return '440px';
    if ($size === 'large') return '960px';
    return '640px';
  }};
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  border-radius: 20px; // Bo góc lớn hiện đại
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  animation: ${slideUp} 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
`;

const Header = styled.div`
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-bottom: 1px solid #f1f5f9;
  z-index: 10;

  h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
    color: #1e293b;
    letter-spacing: -0.5px;
  }
`;

const CloseBtn = styled.button`
  background: #f8fafc;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  cursor: pointer;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;

  &:hover {
    background: #f1f5f9;
    color: #ef4444;
    transform: rotate(90deg);
  }
`;

const Content = styled.div`
  padding: 24px;
  color: #475569;
  overflow-y: auto;
  font-size: 0.95rem;
  line-height: 1.6;

  /* Tùy chỉnh thanh cuộn cho hiện đại */
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: #e2e8f0;
    border-radius: 10px;
  }
`;

const Footer = styled.div`
  padding: 16px 24px;
  background: #f8fafc; // Nền footer hơi tối hơn để phân tách
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
`;

export const Modal = ({ isOpen, onClose, title, children, footer, size }) => {
  // Chặn scroll body khi modal mở
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => { document.body.style.overflow = 'unset'; };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <Overlay onClick={onClose}>
      <ModalContainer $size={size} onClick={(e) => e.stopPropagation()}>
        <Header>
          <h2>{title}</h2>
          <CloseBtn onClick={onClose}>
            <MdClose size={20} />
          </CloseBtn>
        </Header>
        <Content>{children}</Content>
        {footer && <Footer>{footer}</Footer>}
      </ModalContainer>
    </Overlay>
  );
};

export const ModalFooter = ({ onCancel, onConfirm, confirmText = 'Confirm', cancelText = 'Cancel', danger, loading }) => {
  return (
    <>
      <Button variant="outline" onClick={onCancel} disabled={loading}>
        {cancelText}
      </Button>
      <Button 
        variant={danger ? 'danger' : 'primary'} 
        onClick={onConfirm}
        disabled={loading}
      >
        {loading ? 'Processing...' : confirmText}
      </Button>
    </>
  );
};