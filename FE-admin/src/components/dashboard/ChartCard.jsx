import React from 'react';
import styled from 'styled-components';

const StyledCard = styled.div`
  background: white;
  border-radius: 10px;
  padding: ${({ $compact }) => $compact ? '8px' : '10px'};
  border: 1px solid #e2e8f0;
  width: 100%;
  min-height: ${({ $compact }) => $compact ? '140px' : '160px'};
  display: flex;
  flex-direction: column;
`;

const CardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: ${({ $compact }) => $compact ? '4px' : '6px'};
  flex-shrink: 0;
`;

const CardTitle = styled.h3`
  margin: 0;
  font-size: ${({ $compact }) => $compact ? '0.7rem' : '0.75rem'};
  font-weight: 600;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 4px;
`;

const ActionWrapper = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
`;

const ChartWrapper = styled.div`
  width: 100%;
  flex: 1;
  min-height: 0;
  position: relative;
  
  & > div {
    width: 100% !important;
    height: 100% !important;
  }
`;

export const ChartCard = ({ title, children, action, compact = false }) => {
  return (
    <StyledCard $compact={compact}>
      <CardHeader $compact={compact}>
        <CardTitle $compact={compact}>{title}</CardTitle>
        {action && <ActionWrapper>{action}</ActionWrapper>}
      </CardHeader>
      <ChartWrapper>
        {children}
      </ChartWrapper>
    </StyledCard>
  );
};