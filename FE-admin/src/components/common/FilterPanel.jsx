import React from 'react';
import styled from 'styled-components';
import { Button } from './Button';
import { MdClose, MdTune } from 'react-icons/md';

const Panel = styled.form`
  background: #ffffff;
  padding: 20px;
  margin-bottom: 20px;
  border-radius: 16px;
  border: 1px solid #f1f5f9;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.06);
  animation: slideDown 0.25s ease;

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-8px) scale(0.98);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
`;

const TitleWrap = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;

  h3 {
    color: #0f172a;
    margin: 0;
    font-size: 1.05rem;
    font-weight: 600;
  }

  svg {
    font-size: 1.2rem;
    color: #6366f1;
  }
`;

const CloseBtn = styled.button`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #f1f5f9;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;

  &:hover {
    background: #e0e7ff;
    color: #4f46e5;
    transform: rotate(90deg);
  }
`;

const Row = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
  margin-bottom: 18px;
`;

const Item = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;

  label {
    font-size: 0.8rem;
    color: #475569;
    font-weight: 500;
  }

  input, select {
    padding: 9px 10px;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    font-size: 0.9rem;
    color: #0f172a;
    background: #f8fafc;
    transition: all 0.2s ease;

    &:focus {
      outline: none;
      border-color: #6366f1;
      background: white;
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
    }
  }
`;

const Actions = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  border-top: 1px solid #f1f5f9;
  padding-top: 16px;
`;

export const FilterPanel = ({
  title = 'Filters',
  children,
  onApply,
  onReset,
  onClose,
  show
}) => {
  if (!show) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (onApply) onApply();
  };

  return (
    <Panel onSubmit={handleSubmit}>
      <Header>
        <TitleWrap>
          <MdTune />
          <h3>{title}</h3>
        </TitleWrap>

        {onClose && (
          <CloseBtn type="button" onClick={onClose}>
            <MdClose />
          </CloseBtn>
        )}
      </Header>

      {children}

      <Actions>
        <Button type="button" variant="outline" size="small" onClick={onReset}>
          Reset
        </Button>
        <Button type="submit" size="small">
          Apply
        </Button>
      </Actions>
    </Panel>
  );
};

export const FilterRow = ({ children }) => <Row>{children}</Row>;

export const FilterItem = ({ label, children }) => (
  <Item>
    <label>{label}</label>
    {children}
  </Item>
);