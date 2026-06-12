// components/ingredients/SuggestionModal.jsx
import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { MdCheck, MdClose } from 'react-icons/md';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { ingredientService } from '../../services/ingredientService';

const SuggestionCard = styled.div`
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
`;

const SuggestionName = styled.div`
  font-weight: 600;
  margin-bottom: 8px;
`;

const SuggestionMeta = styled.div`
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 12px;
`;

const Select = styled.select`
  width: 100%;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  margin-bottom: 12px;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 12px;
  justify-content: flex-end;
`;

export const SuggestionModal = ({ isOpen, onClose, type, onApprove, onReject }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedIngredientUids, setSelectedIngredientUids] = useState({});
  const [approvalModes, setApprovalModes] = useState({});
  const [ingredients, setIngredients] = useState([]);

  useEffect(() => {
    if (isOpen) {
      fetchSuggestions();
      fetchIngredients();
    }
  }, [isOpen, type]);

const fetchSuggestions = async () => {
  console.log('🔍 [SuggestionModal] Fetching suggestions - type:', type);
  setLoading(true);
  try {
    const response = await ingredientService.getAllSuggestions({ status: 'PENDING' });
    console.log('📦 [SuggestionModal] Full response:', response);
    
    // ✅ Lấy đúng content từ response.data.data.content
    let allSuggestions = [];
    if (response?.data?.data?.content) {
      allSuggestions = response.data.data.content;
    } else if (response?.data?.content) {
      allSuggestions = response.data.content;
    } else if (response?.content) {
      allSuggestions = response.content;
    }
    
    console.log('📦 [SuggestionModal] All suggestions count:', allSuggestions.length);
    
    if (type === 'ingredient') {
      allSuggestions = allSuggestions.filter(s => !s.ingredient_uid);
      console.log('📦 [SuggestionModal] Filtered ingredient suggestions:', allSuggestions.length);
    } else {
      allSuggestions = allSuggestions.filter(s => s.ingredient_uid);
      console.log('📦 [SuggestionModal] Filtered alias suggestions:', allSuggestions.length);
    }
    
    console.log('📦 [SuggestionModal] Final suggestions to display:', allSuggestions);
    setSuggestions(allSuggestions);
  } catch (error) {
    console.error('❌ [SuggestionModal] Fetch suggestions failed:', error);
  } finally {
    setLoading(false);
  }
};

  const fetchIngredients = async () => {
    try {
      const response = await ingredientService.getAllIngredients({ page_size: 1000 });
      console.log('📦 [SuggestionModal] Ingredients response:', response);
      
      let ingredientsList = [];
      
      // Vì ingredientService.getAllIngredients đã trả về response.data.data hoặc response.data
      if (response?.content) {
        ingredientsList = response.content;
      } else if (response?.data?.content) {
        ingredientsList = response.data.content;
      } else if (Array.isArray(response)) {
        ingredientsList = response;
      } else if (Array.isArray(response?.data)) {
        ingredientsList = response.data;
      }
      
      console.log('📦 [SuggestionModal] Final ingredients count:', ingredientsList.length);
      setIngredients(ingredientsList);
    } catch (error) {
      console.error('Fetch ingredients failed:', error);
    }
  };

  const handleApprove = async (suggestion) => {
    const approvalMode = approvalModes[suggestion.uid] || 'new';
    
    try {
      if (approvalMode === 'alias') {
        const selectedUid = selectedIngredientUids[suggestion.uid];
        if (!selectedUid) {
          alert('Vui lòng chọn ingredient để alias');
          return;
        }
        await ingredientService.approveAliasSuggestion(suggestion.uid, selectedUid, 'Approved as alias');
      } else {
        await ingredientService.approveNewSuggestion(suggestion.uid, 'Approved as new ingredient');
      }
      fetchSuggestions();
      onApprove();
    } catch (error) {
      console.error('Approve failed:', error);
      alert(`Approve failed: ${error.message}`);
    }
  };

  const [rejectReason, setRejectReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState(null);

  const openRejectModal = (suggestion) => {
    setSelectedSuggestion(suggestion);
    setRejectReason('');
    setShowRejectModal(true);
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      alert('Vui lòng nhập lý do từ chối');
      return;
    }
    try {
      await ingredientService.rejectSuggestion(selectedSuggestion.uid, rejectReason);
      setShowRejectModal(false);
      fetchSuggestions();
      onReject();
    } catch (error) {
      console.error('Reject failed:', error);
      alert(`Reject failed: ${error.message}`);
    }
  };

  return (
    <>
    <Modal isOpen={isOpen} onClose={onClose} title={`Pending ${type === 'ingredient' ? 'Ingredient' : 'Alias'} Suggestions`} size="large">
      {loading ? (
        <div style={{ textAlign: 'center', padding: 40 }}>Loading...</div>
      ) : suggestions.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>No pending suggestions</div>
      ) : (
        suggestions.map(suggestion => (
          <SuggestionCard key={suggestion.uid}>
            <SuggestionName>{suggestion.name}</SuggestionName>
            <SuggestionMeta>
              Category: {suggestion.category} | By Chef ID: {suggestion.created_by_id}
            </SuggestionMeta>
            
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <input 
                  type="radio" 
                  name={`mode-${suggestion.uid}`}
                  checked={approvalModes[suggestion.uid] !== 'alias'}
                  onChange={() => setApprovalModes(prev => ({ ...prev, [suggestion.uid]: 'new' }))}
                />
                Tạo ingredient mới
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <input 
                  type="radio" 
                  name={`mode-${suggestion.uid}`}
                  checked={approvalModes[suggestion.uid] === 'alias'}
                  onChange={() => setApprovalModes(prev => ({ ...prev, [suggestion.uid]: 'alias' }))}
                />
                Là alias của ingredient có sẵn
              </label>
              
              {approvalModes[suggestion.uid] === 'alias' && (
                <Select 
                  value={selectedIngredientUids[suggestion.uid] || ''}
                  onChange={(e) => setSelectedIngredientUids(prev => ({ ...prev, [suggestion.uid]: e.target.value }))}
                >
                  <option value="">Chọn ingredient để alias...</option>
                  {ingredients.map(ing => (
                    <option key={ing.uid} value={ing.uid}>{ing.name}</option>
                  ))}
                </Select>
              )}
            </div>
            
            <ButtonGroup>
              <Button size="small" variant="danger" onClick={() => openRejectModal(suggestion)}>
                <MdClose /> Reject
              </Button>
              <Button size="small" $primary onClick={() => handleApprove(suggestion)}>
                <MdCheck /> Approve
              </Button>
            </ButtonGroup>
          </SuggestionCard>
        ))
      )}
    </Modal>
    
    {showRejectModal && (
      <Modal isOpen={showRejectModal} onClose={() => setShowRejectModal(false)} title="Từ chối Suggestion" size="small">
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
            Lý do từ chối:
          </label>
          <Select 
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            style={{ width: '100%' }}
          >
            <option value="">Chọn lý do...</option>
            <option value="Không hợp lệ">Không hợp lệ</option>
            <option value="Trùng lặp với ingredient hiện có">Trùng lặp với ingredient hiện có</option>
            <option value="Thiếu thông tin dinh dưỡng">Thiếu thông tin dinh dưỡng</option>
            <option value="Sai định dạng">Sai định dạng</option>
          </Select>
        </div>
        <ButtonGroup>
          <Button variant="secondary" onClick={() => setShowRejectModal(false)}>Hủy</Button>
          <Button variant="danger" onClick={handleReject}>Xác nhận từ chối</Button>
        </ButtonGroup>
      </Modal>
    )}
    </>
  );
};