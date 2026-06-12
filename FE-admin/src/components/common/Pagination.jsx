import React from 'react';
import styled from 'styled-components';
import { MdChevronLeft, MdChevronRight } from 'react-icons/md';

const Container = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  margin-top: 10px;
  flex-wrap: wrap;
  gap: 16px;
  border-top: 1px solid #f1f5f9;
`;

const Info = styled.div`
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 500;

  span {
    color: #1e3c72;
    font-weight: 600;
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
`;

const PageBtn = styled.button`
  min-width: 36px;
  height: 36px;
  padding: 0 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px; // Bo góc đồng bộ với hệ thống
  font-size: 0.875rem;
  font-weight: ${({ $active }) => ($active ? '600' : '500')};
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  
  /* Logic màu sắc */
  border: 1px solid ${({ $active }) => ($active ? '#1e3c72' : '#e2e8f0')};
  background: ${({ $active }) => ($active ? '#1e3c72' : 'white')};
  color: ${({ $active }) => ($active ? 'white' : '#64748b')};
  box-shadow: ${({ $active }) => ($active ? '0 4px 12px rgba(30, 60, 114, 0.25)' : 'none')};

  &:hover:not(:disabled) {
    background: ${({ $active }) => ($active ? '#1e3c72' : '#f8fafc')};
    border-color: #1e3c72;
    color: ${({ $active }) => ($active ? 'white' : '#1e3c72')};
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    background: #f1f5f9;
  }

  &.ellipsis {
    cursor: default;
    border-color: transparent;
    background: transparent;
    &:hover { transform: none; }
  }
`;

export const Pagination = ({ currentPage, totalPages, onPageChange, totalItems, pageSize }) => {
  const startIndex = totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endIndex = Math.min(currentPage * pageSize, totalItems);

  // Hàm logic để tính toán dãy số trang hiển thị (ví dụ: 1 ... 4 5 6 ... 10)
  const getPageNumbers = () => {
    const pages = [];
    const showMax = 5; // Số lượng nút trang tối đa muốn hiển thị ở giữa

    if (totalPages <= showMax + 2) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (currentPage > 3) pages.push('...');
      
      let start = Math.max(2, currentPage - 1);
      let end = Math.min(totalPages - 1, currentPage + 1);

      if (currentPage <= 3) end = 4;
      if (currentPage >= totalPages - 2) start = totalPages - 3;

      for (let i = start; i <= end; i++) pages.push(i);

      if (currentPage < totalPages - 2) pages.push('...');
      pages.push(totalPages);
    }
    return pages;
  };

  if (totalPages <= 0) return null;

  return (
    <Container>
      <Info>
        Showing <span>{startIndex}</span> to <span>{endIndex}</span> of <span>{totalItems}</span> results
      </Info>
      
      <ButtonGroup>
        <PageBtn 
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          aria-label="Previous page"
        >
          <MdChevronLeft size={20} />
        </PageBtn>

        {getPageNumbers().map((page, index) => (
          <PageBtn
            key={index}
            $active={currentPage === page}
            className={page === '...' ? 'ellipsis' : ''}
            onClick={() => page !== '...' && onPageChange(page)}
            disabled={page === '...'}
          >
            {page}
          </PageBtn>
        ))}

        <PageBtn 
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          aria-label="Next page"
        >
          <MdChevronRight size={20} />
        </PageBtn>
      </ButtonGroup>
    </Container>
  );
};