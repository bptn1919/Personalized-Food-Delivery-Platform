import React from 'react';
import styled, { keyframes } from 'styled-components';

// Animation xoay tròn
const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

// Animation nhịp thở cho text
const pulse = keyframes`
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.98); }
`;

const Container = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: ${({ $fullPage }) => $fullPage ? '100vh' : '400px'};
  gap: 20px;
  background: ${({ $fullPage }) => 
    $fullPage ? 'rgba(248, 250, 252, 0.8)' : 'transparent'};
  backdrop-filter: ${({ $fullPage }) => $fullPage ? 'blur(8px)' : 'none'};
  width: 100%;
  transition: all 0.3s ease;
`;

const SpinnerWrapper = styled.div`
  position: relative;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;

  &::before {
    content: '';
    position: absolute;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    border: 3px solid transparent;
    /* Tạo vòng xoay gradient */
    border-top: 3px solid #1e3c72;
    border-left: 3px solid #2a5298;
    border-bottom: 3px solid #a5c9fd;
    animation: ${spin} 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
    filter: drop-shadow(0 0 8px rgba(30, 60, 114, 0.4));
  }

  &::after {
    content: '';
    position: absolute;
    width: 12px;
    height: 12px;
    background: #1e3c72;
    border-radius: 50%;
    box-shadow: 0 0 15px rgba(30, 60, 114, 0.6);
  }
`;

const LoadingText = styled.p`
  color: #1e3c72;
  font-weight: 600;
  font-size: 0.95rem;
  letter-spacing: 1px;
  text-transform: uppercase;
  animation: ${pulse} 1.5s ease-in-out infinite;
  
  /* Hiệu ứng gradient cho text */
  background: linear-gradient(to right, #1e3c72, #2a5298);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
`;

export const Loading = ({ fullPage, text = 'Processing...' }) => {
  return (
    <Container $fullPage={fullPage}>
      <SpinnerWrapper />
      <LoadingText>{text}</LoadingText>
    </Container>
  );
};