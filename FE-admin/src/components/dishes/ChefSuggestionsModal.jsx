// components/dishes/ChefSuggestionsModal.jsx
import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { ingredientService } from '../../services/ingredientService';
import { MdCheckCircle, MdPending, MdCancel, MdInfo } from 'react-icons/md';

const SuggestionsList = styled.div`
  max-height: 500px;
  overflow-y: auto;
`;

const SuggestionCard = styled.div`
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  background: white;
  transition: all 0.2s;

  &:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
`;

const SuggestionHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
`;

const SuggestionName = styled.h4`
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: #1e293b;
`;

const StatusBadge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 600;
  background: ${({ $status }) => {
    if ($status === 'PENDING') return '#fef3c7';
    if ($status === 'APPROVED') return '#dcfce7';
    if ($status === 'REJECTED') return '#fee2e2';
    return '#f1f5f9';
  }};
  color: ${({ $status }) => {
    if ($status === 'PENDING') return '#92400e';
    if ($status === 'APPROVED') return '#166534';
    if ($status === 'REJECTED') return '#991b1b';
    return '#64748b';
  }};
`;

const SuggestionMeta = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  font-size: 0.75rem;
  color: #64748b;
  margin: 8px 0;
`;

const ResolutionNote = styled.div`
  margin-top: 8px;
  padding: 8px;
  background: #f8fafc;
  border-radius: 8px;
  font-size: 0.75rem;
  color: #475569;
`;

const VerifiedInfo = styled.div`
  margin-top: 8px;
  font-size: 0.7rem;
  color: #94a3b8;
`;

const FilterBar = styled.div`
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
`;

const FilterButton = styled.button`
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  border: 1px solid #e2e8f0;
  background: ${({ $active }) => $active ? '#1e3c72' : 'white'};
  color: ${({ $active }) => $active ? 'white' : '#64748b'};
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: ${({ $active }) => $active ? '#2a5298' : '#f1f5f9'};
  }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 40px;
  color: #94a3b8;
`;

const LoadingState = styled.div`
  text-align: center;
  padding: 40px;
  color: #64748b;
`;

const PaginationContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
`;

const PageInfo = styled.span`
  font-size: 0.85rem;
  color: #64748b;
`;

export const ChefSuggestionsModal = ({ isOpen, onClose }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRows, setTotalRows] = useState(0);
  const pageSize = 10;

  const fetchSuggestions = async () => {
    setLoading(true);
    try {
      const params = { page: currentPage, page_size: pageSize };
      if (filter !== 'all') params.status = filter.toUpperCase();
      
      const response = await ingredientService.getMySuggestions(params);
      console.log('My suggestions response:', response);
      
      // Lấy đúng content từ cấu trúc response
      let content = [];
      let total = 0;
      let pages = 1;
      
      if (response?.data?.content) {
        content = response.data.content;
        total = response.data.total_rows || 0;
        pages = response.data.total_pages || 1;
      } else if (response?.content) {
        content = response.content;
        total = response.total_rows || 0;
        pages = response.total_pages || 1;
      }
      
      setSuggestions(content);
      setTotalRows(total);
      setTotalPages(pages);
    } catch (error) {
      console.error('Fetch suggestions failed:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchSuggestions();
    }
  }, [isOpen, currentPage, filter]);

  const getStatusIcon = (status) => {
    if (status === 'PENDING') return <MdPending size={14} />;
    if (status === 'APPROVED') return <MdCheckCircle size={14} />;
    return <MdCancel size={14} />;
  };

  const getStatusText = (status) => {
    if (status === 'PENDING') return 'Pending Review';
    if (status === 'APPROVED') return 'Approved';
    return 'Rejected';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="My Ingredient Suggestions" size="large">
      <FilterBar>
        <FilterButton $active={filter === 'all'} onClick={() => { setFilter('all'); setCurrentPage(1); }}>
          All ({totalRows})
        </FilterButton>
        <FilterButton $active={filter === 'pending'} onClick={() => { setFilter('pending'); setCurrentPage(1); }}>
          Pending
        </FilterButton>
        <FilterButton $active={filter === 'approved'} onClick={() => { setFilter('approved'); setCurrentPage(1); }}>
          Approved
        </FilterButton>
        <FilterButton $active={filter === 'rejected'} onClick={() => { setFilter('rejected'); setCurrentPage(1); }}>
          Rejected
        </FilterButton>
      </FilterBar>

      {loading ? (
        <LoadingState>Loading your suggestions...</LoadingState>
      ) : suggestions.length === 0 ? (
        <EmptyState>
          <MdInfo size={32} />
          <p>You haven't submitted any ingredient suggestions yet.</p>
          <p style={{ fontSize: '0.8rem', marginTop: 8 }}>Go to a dish and click "Suggest New Ingredient" to get started.</p>
        </EmptyState>
      ) : (
        <>
          <SuggestionsList>
            {suggestions.map((suggestion) => (
              <SuggestionCard key={suggestion.uid}>
                <SuggestionHeader>
                  <SuggestionName>{suggestion.name}</SuggestionName>
                  <StatusBadge $status={suggestion.status}>
                    {getStatusIcon(suggestion.status)}
                    {getStatusText(suggestion.status)}
                  </StatusBadge>
                </SuggestionHeader>
                
                <SuggestionMeta>
                  <div>📂 Category: {suggestion.category}</div>
                </SuggestionMeta>
                
                {suggestion.verified_at && (
                  <VerifiedInfo>
                    ✓ Reviewed on {formatDate(suggestion.verified_at)} by Admin #{suggestion.verified_by_id}
                  </VerifiedInfo>
                )}
                
                {suggestion.resolution_note && (
                  <ResolutionNote>
                    <strong>📝 Note:</strong> {suggestion.resolution_note}
                  </ResolutionNote>
                )}
              </SuggestionCard>
            ))}
          </SuggestionsList>
          
          {totalPages > 1 && (
            <PaginationContainer>
              <Button 
                variant="secondary" 
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                Previous
              </Button>
              <PageInfo>
                Page {currentPage} of {totalPages}
              </PageInfo>
              <Button 
                variant="secondary" 
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Next
              </Button>
            </PaginationContainer>
          )}
        </>
      )}
    </Modal>
  );
};