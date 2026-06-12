import React from 'react';
import styled from 'styled-components';

const StyledCard = styled.div`
  background: #ffffff;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #f1f5f9;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.25s ease;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.08);
  }
`;

const CardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f1f5f9;
`;

const CardTitle = styled.h3`
  font-size: 1.05rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
`;

const CardContent = styled.div`
  color: #334155;
  font-size: 0.95rem;
  line-height: 1.5;
`;

export const Card = ({ children, ...props }) => {
  return <StyledCard {...props}>{children}</StyledCard>;
};

export const Header = ({ children }) => {
  return <CardHeader>{children}</CardHeader>;
};

export const Title = ({ children }) => {
  return <CardTitle>{children}</CardTitle>;
};

export const Content = ({ children }) => {
  return <CardContent>{children}</CardContent>;
};