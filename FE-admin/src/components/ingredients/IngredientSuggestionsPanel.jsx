import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { MdCheck, MdClose, MdLink, MdWarning } from 'react-icons/md';
import { Button } from '../common/Button';
import { Modal, ModalFooter } from '../common/Modal';
import { ingredientService } from '../../services/ingredientService';

const SuggestionsContainer = styled.div`
  margin-top: 24px;
`;

const SuggestionCard = styled.div`
  background: white;
  border: 1px solid ${({ $status }) => 
    $status === 'PENDING' ? '#fef3c7' : 
    $status === 'APPROVED' ? '#dcfce7' : '#fee2e2'
  };
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  transition: all 0.2s;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  }
`;

const SuggestionHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
`;

const SuggestionName = styled.h4`
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #1e293b;
`;

const StatusBadge = styled.span`
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 600;
  background: ${({ $status }) => 
    $status === 'PENDING' ? '#fef3c7' : 
    $status === 'APPROVED' ? '#dcfce7' : '#fee2e2'
  };
  color: ${({ $status }) => 
    $status === 'PENDING' ? '#92400e' : 
    $status === 'APPROVED' ? '#166534' : '#991b1b'
  };
`;

const SuggestionInfo = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
  font-size: 0.85rem;
  color: #475569;
`;

const InfoRow = styled.div`
  display: flex;
  gap: 8px;
  align-items: baseline;
`;

const InfoLabel = styled.span`
  font-weight: 600;
  color: #64748b;
  min-width: 100px;
`;

const InfoValue = styled.span`
  color: #1e293b;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 60px;
  color: #94a3b8;
`;

const TabsContainer = styled.div`
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 1px solid #e2e8f0;
`;

const Tab = styled.button`
  padding: 10px 20px;
  background: none;
  border: none;
  font-size: 0.9rem;
  font-weight: 600;
  color: ${({ $active }) => $active ? '#1e3c72' : '#64748b'};
  border-bottom: 3px solid ${({ $active }) => $active ? '#1e3c72' : 'transparent'};
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    color: #1e3c72;
  }
`;

// Component cho Admin
export const AdminSuggestionsPanel = () => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSuggestion, setSelectedSuggestion] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [actionType, setActionType] = useState('');
  const [resolutionNote, setResolutionNote] = useState('');
  const [selectedIngredientUid, setSelectedIngredientUid] = useState('');
  const [searchIngredients, setSearchIngredients] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchSuggestions = async () => {
    setLoading(true);
    try {
      const response = await ingredientService.getAllSuggestions({ page: 1, page_size: 100 });
      setSuggestions(response?.content || []);
    } catch (error) {
      console.error('Fetch suggestions failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchIngredientsApi = async (query) => {
    if (!query) return;
    try {
      const results = await ingredientService.autocompleteIngredients(query, 10);
      setSearchIngredients(results || []);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  useEffect(() => {
    fetchSuggestions();
  }, []);

  const handleApproveNew = async () => {
    try {
      await ingredientService.approveNewSuggestion(selectedSuggestion.uid, resolutionNote);
      fetchSuggestions();
      setShowModal(false);
      alert('Suggestion approved and added to ingredients!');
    } catch (error) {
      alert(`Approve failed: ${error.message}`);
    }
  };

  const handleApproveAlias = async () => {
    try {
      await ingredientService.approveAliasSuggestion(selectedSuggestion.uid, selectedIngredientUid, resolutionNote);
      fetchSuggestions();
      setShowModal(false);
      alert('Alias created successfully!');
    } catch (error) {
      alert(`Approve alias failed: ${error.message}`);
    }
  };

  const handleReject = async () => {
    try {
      await ingredientService.rejectSuggestion(selectedSuggestion.uid, resolutionNote);
      fetchSuggestions();
      setShowModal(false);
      alert('Suggestion rejected');
    } catch (error) {
      alert(`Reject failed: ${error.message}`);
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 40 }}>Loading suggestions...</div>;
  }

  return (
    <SuggestionsContainer>
      <TabsContainer>
        <Tab $active>Pending</Tab>
      </TabsContainer>

      {suggestions.filter(s => s.status === 'PENDING').length === 0 ? (
        <EmptyState>No pending suggestions</EmptyState>
      ) : (
        suggestions.filter(s => s.status === 'PENDING').map(suggestion => (
          <SuggestionCard key={suggestion.uid} $status={suggestion.status}>
            <SuggestionHeader>
              <SuggestionName>{suggestion.name}</SuggestionName>
              <StatusBadge $status={suggestion.status}>{suggestion.status}</StatusBadge>
            </SuggestionHeader>
            
            <SuggestionInfo>
              <InfoRow>
                <InfoLabel>Category:</InfoLabel>
                <InfoValue>{suggestion.category}</InfoValue>
              </InfoRow>
              <InfoRow>
                <InfoLabel>Submitted by:</InfoLabel>
                <InfoValue>Chef ID {suggestion.created_by_id}</InfoValue>
              </InfoRow>
              <InfoRow>
                <InfoLabel>Energy:</InfoLabel>
                <InfoValue>{suggestion.energy} kcal/100g</InfoValue>
              </InfoRow>
              <InfoRow>
                <InfoLabel>Protein:</InfoLabel>
                <InfoValue>{suggestion.protein}g</InfoValue>
              </InfoRow>
              <InfoRow>
                <InfoLabel>Fat:</InfoLabel>
                <InfoValue>{suggestion.lipid}g</InfoValue>
              </InfoRow>
              <InfoRow>
                <InfoLabel>Carbs:</InfoLabel>
                <InfoValue>{suggestion.carbohydrate}g</InfoValue>
              </InfoRow>
            </SuggestionInfo>

            <ActionButtons>
              <Button 
                size="small" 
                onClick={() => {
                  setSelectedSuggestion(suggestion);
                  setActionType('approve_new');
                  setShowModal(true);
                }}
              >
                <MdCheck /> Approve New
              </Button>
              <Button 
                size="small" 
                variant="secondary"
                onClick={() => {
                  setSelectedSuggestion(suggestion);
                  setActionType('approve_alias');
                  setShowModal(true);
                }}
              >
                <MdLink /> Approve Alias
              </Button>
              <Button 
                size="small" 
                variant="danger"
                onClick={() => {
                  setSelectedSuggestion(suggestion);
                  setActionType('reject');
                  setShowModal(true);
                }}
              >
                <MdClose /> Reject
              </Button>
            </ActionButtons>
          </SuggestionCard>
        ))
      )}

      {/* Modal xử lý suggestion */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Process Suggestion" size="small">
        {actionType === 'approve_alias' && (
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 8, fontWeight: 600 }}>Select Ingredient to Alias:</label>
            <input 
              type="text" 
              placeholder="Search ingredient..."
              style={{ width: '100%', padding: 8, borderRadius: 8, border: '1px solid #e2e8f0' }}
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                searchIngredientsApi(e.target.value);
              }}
            />
            {searchIngredients.length > 0 && (
              <div style={{ marginTop: 8, border: '1px solid #e2e8f0', borderRadius: 8, maxHeight: 150, overflow: 'auto' }}>
                {searchIngredients.map(ing => (
                  <div 
                    key={ing.uid}
                    style={{ padding: 8, cursor: 'pointer', borderBottom: '1px solid #f1f5f9' }}
                    onClick={() => {
                      setSelectedIngredientUid(ing.uid);
                      setSearchTerm(ing.name);
                      setSearchIngredients([]);
                    }}
                  >
                    {ing.name} - {ing.energy} kcal/100g
                  </div>
                ))}
              </div>
            )}
            {selectedIngredientUid && <div style={{ marginTop: 8, color: '#10b981' }}>✓ Selected</div>}
          </div>
        )}
        
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 8, fontWeight: 600 }}>Resolution Note:</label>
          <textarea 
            value={resolutionNote}
            onChange={(e) => setResolutionNote(e.target.value)}
            placeholder="Add a note..."
            style={{ width: '100%', padding: 8, borderRadius: 8, border: '1px solid #e2e8f0', minHeight: 80 }}
          />
        </div>
        
        <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
          <Button onClick={() => setShowModal(false)}>Cancel</Button>
          <Button 
            $primary 
            onClick={
              actionType === 'approve_new' ? handleApproveNew :
              actionType === 'approve_alias' ? handleApproveAlias : handleReject
            }
          >
            Confirm
          </Button>
        </div>
      </Modal>
    </SuggestionsContainer>
  );
};

// Component cho Chef
export const ChefSuggestionsPanel = () => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchMySuggestions = async () => {
    setLoading(true);
    try {
      const response = await ingredientService.getMySuggestions({ page: 1, page_size: 100 });
      setSuggestions(response?.content || []);
    } catch (error) {
      console.error('Fetch my suggestions failed:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMySuggestions();
  }, []);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 40 }}>Loading your suggestions...</div>;
  }

  return (
    <SuggestionsContainer>
      {suggestions.length === 0 ? (
        <EmptyState>You haven't submitted any suggestions yet</EmptyState>
      ) : (
        suggestions.map(suggestion => (
          <SuggestionCard key={suggestion.uid} $status={suggestion.status}>
            <SuggestionHeader>
              <SuggestionName>{suggestion.name}</SuggestionName>
              <StatusBadge $status={suggestion.status}>{suggestion.status}</StatusBadge>
            </SuggestionHeader>
            
            <SuggestionInfo>
              <InfoRow>
                <InfoLabel>Category:</InfoLabel>
                <InfoValue>{suggestion.category}</InfoValue>
              </InfoRow>
              <InfoRow>
                <InfoLabel>Submitted:</InfoLabel>
                <InfoValue>{new Date(suggestion.created_at).toLocaleDateString()}</InfoValue>
              </InfoRow>
              <InfoRow>
                <InfoLabel>Energy:</InfoLabel>
                <InfoValue>{suggestion.energy} kcal/100g</InfoValue>
              </InfoRow>
              <InfoRow>
                <InfoLabel>Protein:</InfoLabel>
                <InfoValue>{suggestion.protein}g</InfoValue>
              </InfoRow>
            </SuggestionInfo>

            {suggestion.status === 'REJECTED' && suggestion.rejection_reason && (
              <div style={{ marginTop: 12, padding: 12, background: '#fee2e2', borderRadius: 8, fontSize: '0.85rem' }}>
                <strong>Rejection reason:</strong> {suggestion.rejection_reason}
              </div>
            )}

            {suggestion.status === 'APPROVED' && suggestion.resolution_note && (
              <div style={{ marginTop: 12, padding: 12, background: '#dcfce7', borderRadius: 8, fontSize: '0.85rem' }}>
                <strong>Resolution note:</strong> {suggestion.resolution_note}
              </div>
            )}
          </SuggestionCard>
        ))
      )}
    </SuggestionsContainer>
  );
};