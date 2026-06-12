import React from 'react';
import styled, { css } from 'styled-components';

const variants = {
  primary: css`
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
  `,
  secondary: css`
    background: #eef2ff;
    color: #4338ca;
  `,
  success: css`
    background: #22c55e;
    color: white;
  `,
  danger: css`
    background: #ef4444;
    color: white;
  `,
  outline: css`
    background: transparent;
    border: 1px solid #c7d2fe;
    color: #4338ca;
  `,
};

const sizes = {
  small: css`
    padding: 6px 12px;
    font-size: 0.85rem;
  `,
  medium: css`
    padding: 8px 16px;
    font-size: 0.95rem;
  `,
  large: css`
    padding: 12px 22px;
    font-size: 1.05rem;
  `,
};

const StyledButton = styled.button`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 10px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  width: ${({ $fullWidth }) => ($fullWidth ? '100%' : 'auto')};

  ${({ $variant }) => variants[$variant || 'primary']}
  ${({ $size }) => sizes[$size || 'medium']}

  box-shadow: 0 2px 6px rgba(0,0,0,0.08);

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 14px rgba(0,0,0,0.12);
    filter: brightness(1.05);
  }

  &:active {
    transform: scale(0.97);
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
  }

  &:disabled {
    background: #e5e7eb;
    color: #9ca3af;
    cursor: not-allowed;
    box-shadow: none;
  }

  svg {
    font-size: 1.1rem;
  }
`;

const IconButton = styled.button`
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  background: #f3f4f6;
  color: #4f46e5;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #e0e7ff;
    transform: scale(1.05);
    box-shadow: 0 4px 10px rgba(79,70,229,0.25);
  }

  &:active {
    transform: scale(0.92);
  }

  &:disabled {
    background: #e5e7eb;
    color: #9ca3af;
    cursor: not-allowed;
  }

  svg {
    font-size: 1.2rem;
  }
`;

export const Button = ({
  children,
  variant = 'primary',
  size = 'medium',
  fullWidth,
  ...props
}) => {
  return (
    <StyledButton
      $variant={variant}
      $size={size}
      $fullWidth={fullWidth}
      {...props}
    >
      {children}
    </StyledButton>
  );
};

export const IconBtn = ({ children, ...props }) => {
  return <IconButton {...props}>{children}</IconButton>;
};