import React from 'react';
import styled from 'styled-components';
import { MdArrowUpward, MdArrowDownward, MdUnfoldMore } from 'react-icons/md';

const TableContainer = styled.div`
  background: white;
  border-radius: 16px; /* Bo góc đồng bộ */
  border: 1px solid #f1f5f9;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  overflow: hidden; /* Cắt góc bảng cho khớp với border-radius */
  width: 100%;
`;

const ScrollWrapper = styled.div`
  overflow-x: auto;
  
  /* Tùy chỉnh thanh cuộn ngang */
  &::-webkit-scrollbar { height: 6px; }
  &::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }
`;

const StyledTable = styled.table`
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
`;

const Th = styled.th`
  text-align: left;
  padding: 16px;
  background: #f8fafc;
  color: #475569;
  font-weight: 700;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  cursor: ${({ $sortable }) => ($sortable ? 'pointer' : 'default')};
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 10;
  transition: all 0.2s ease;

  &:hover {
    background: ${({ $sortable }) => ($sortable ? '#f1f5f9' : '#f8fafc')};
    color: ${({ $sortable }) => ($sortable ? '#1e3c72' : '#475569')};
  }

  .sort-icon {
    margin-left: 6px;
    font-size: 1rem;
    vertical-align: middle;
    color: #94a3b8;
  }
`;

const Td = styled.td`
  padding: 16px;
  border-bottom: 1px solid #f1f5f9;
  color: #1e293b;
  font-size: 0.9rem;
  vertical-align: middle;
  transition: background 0.2s ease;
`;

const Tr = styled.tr`
  &:last-child ${Td} {
    border-bottom: none;
  }

  &:hover ${Td} {
    background: #fcfdfe; /* Highlight nhẹ khi hover dòng */
  }
`;

// --- Components ---

export const Table = ({ children, ...props }) => {
  return (
    <TableContainer>
      <ScrollWrapper>
        <StyledTable {...props}>{children}</StyledTable>
      </ScrollWrapper>
    </TableContainer>
  );
};

export const TableHead = ({ children }) => <thead>{children}</thead>;
export const TableBody = ({ children }) => <tbody>{children}</tbody>;

export const TableRow = ({ children, ...props }) => <Tr {...props}>{children}</Tr>;

export const TableHeaderCell = ({ children, sortable, onClick, sortConfig, column }) => {
  const getSortIcon = () => {
    if (!sortable) return null;
    if (!sortConfig || sortConfig.key !== column) return <MdUnfoldMore className="sort-icon" />;
    return sortConfig.direction === 'asc' ? 
      <MdArrowUpward className="sort-icon" style={{color: '#1e3c72'}} /> : 
      <MdArrowDownward className="sort-icon" style={{color: '#1e3c72'}} />;
  };

  return (
    <Th $sortable={sortable} onClick={onClick}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        {children} {getSortIcon()}
      </div>
    </Th>
  );
};

export const TableCell = ({ children, ...props }) => {
  return <Td {...props}>{children}</Td>;
};