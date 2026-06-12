import React, { useState, useRef } from 'react';
import styled from 'styled-components';
import { MdAdd, MdTrendingUp, MdCheckCircle, MdErrorOutline, MdArrowBack } from 'react-icons/md';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { IngredientDetailModal } from '../ingredients/IngredientDetailModal';
import { IngredientSearchDropdown } from '../ingredients/IngredientSearchDropdown';
import { ingredientService } from '../../services/ingredientService';

const WeightInput = styled.input`
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;

  &:focus {
    outline: none;
    border-color: #1e3c72;
  }
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
`;

const Label = styled.label`
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
`;

const NutritionPreview = styled.div`
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
  margin: 12px 0;
  font-size: 0.85rem;
`;

const NutritionGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
`;

const NutritionRow = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.8rem;
`;

const ConfidenceBadge = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  background: ${({ $confidence }) => {
    if ($confidence >= 0.8) return '#dcfce7';
    if ($confidence >= 0.5) return '#fef3c7';
    return '#fee2e2';
  }};
  color: ${({ $confidence }) => {
    if ($confidence >= 0.8) return '#166534';
    if ($confidence >= 0.5) return '#92400e';
    return '#991b1b';
  }};
  margin-bottom: 12px;
`;

const WarningItem = styled.div`
  padding: 10px;
  margin-bottom: 8px;
  border-radius: 8px;
  background: ${({ $severity }) => {
    if ($severity >= 2) return '#fee2e2';
    if ($severity >= 1) return '#fef3c7';
    return '#f1f5f9';
  }};
  border-left: 4px solid ${({ $severity }) => {
    if ($severity >= 2) return '#ef4444';
    if ($severity >= 1) return '#f59e0b';
    return '#64748b';
  }};
  font-size: 0.8rem;
`;

const ActionButtons = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
`;

const SuggestButton = styled.button`
  width: 100%;
  margin-top: 16px;
  padding: 10px;
  background: #f1f5f9;
  border: 1px dashed #e2e8f0;
  border-radius: 10px;
  color: #1e3c72;
  font-size: 0.85rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;

  &:hover {
    background: #e2e8f0;
    border-color: #1e3c72;
  }
`;

const SuggestForm = styled.div`
  margin-top: 16px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
`;

const FormRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
`;

const Select = styled.select`
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.85rem;
  background: white;
`;

const CATEGORIES = [
  { value: 'GRAIN', label: 'Grain' },
  { value: 'PROTEIN', label: 'Protein' },
  { value: 'VEGETABLE', label: 'Vegetable' },
  { value: 'FRUIT', label: 'Fruit' },
  { value: 'OILFATBUTTER', label: 'Oil/Fat/Butter' },
  { value: 'SPICE', label: 'Spice' },
  { value: 'MILK', label: 'Milk' }
];

const formatNumber = (num) => {
  if (num === null || num === undefined) return '0';
  return Number(num).toFixed(1);
};

export const AddIngredientModal = ({ isOpen, onClose, onAdd, dishUid }) => {
  const [selectedIngredient, setSelectedIngredient] = useState(null);
  const [weight, setWeight] = useState(100);
  const [previewData, setPreviewData] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showSuggestForm, setShowSuggestForm] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [fullIngredientDetail, setFullIngredientDetail] = useState(null);
  const [suggestFormData, setSuggestFormData] = useState({
    custom_name: '',
    category: 'GRAIN',
    weight: 100,
    energy: 0,
    protein: 0,
    lipid: 0,
    carbohydrate: 0,
    fiber: 0,
    natri: 0,
    kali: 0,
    vitamin_b_2: 0,
    vitamin_pp: 0,
    vitamin_c: 0,
    calcium: 0,
    phosphorus: 0,
    fe: 0,
    mg: 0,
    zn: 0
  });
  const [suggestPreview, setSuggestPreview] = useState(null);
  const [suggestLoading, setSuggestLoading] = useState(false);
  const isSubmittingRef = useRef(false);

  const handleSelectIngredient = (item) => {
    console.log('Selected ingredient:', item);
    setSelectedIngredient(item);
    setPreviewData(null);
    setShowPreview(false);
  };

const handleViewDetail = async (item) => {
  setLoading(true);
  try {
    const response = await ingredientService.getIngredientDetail(item.uid);
    console.log('Detail response:', response);
    
    // ✅ Lấy đúng data từ response
    const detailData = response?.data || response;
    setFullIngredientDetail(detailData);
    setShowDetailModal(true);
  } catch (error) {
    console.error('Failed to fetch ingredient detail:', error);
    alert('Failed to load ingredient details');
  } finally {
    setLoading(false);
  }
};

  const handlePreview = async () => {
    if (loading || !selectedIngredient) return;
    if (!dishUid) {
      alert('Please save the dish first before adding ingredients');
      return;
    }
    setLoading(true);
    try {
      const data = await ingredientService.previewIngredientForDish(dishUid, {
        ingredient_uid: selectedIngredient.uid,
        weight: weight
      });
      console.log('Preview data:', data);
      setPreviewData(data);
      setShowPreview(true);
    } catch (error) {
      console.error('Preview failed:', error);
      alert('Preview failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAdd = async () => {
    if (loading || !selectedIngredient || isSubmittingRef.current) return;
    isSubmittingRef.current = true;
    setLoading(true);
    try {
      await ingredientService.addIngredientToDish(dishUid, {
        ingredient_uid: selectedIngredient.uid,
        weight: weight
      });
      onAdd({
        ...selectedIngredient,
        ingredient_uid: selectedIngredient.uid,
        weight: weight,
        nutrition: previewData?.nutrition
      });
      handleClose();
    } catch (error) {
      console.error('Add failed:', error);
      alert('Add failed: ' + error.message);
    } finally {
      setLoading(false);
      isSubmittingRef.current = false;
    }
  };

  const handleClose = () => {
    setSelectedIngredient(null);
    setWeight(100);
    setPreviewData(null);
    setShowPreview(false);
    setShowSuggestForm(false);
    setSuggestFormData({
      custom_name: '',
      category: 'GRAIN',
      weight: 100,
      energy: 0,
      protein: 0,
      lipid: 0,
      carbohydrate: 0,
      fiber: 0,
      natri: 0,
      kali: 0,
      vitamin_b_2: 0,
      vitamin_pp: 0,
      vitamin_c: 0,
      calcium: 0,
      phosphorus: 0,
      fe: 0,
      mg: 0,
      zn: 0
    });
    setSuggestPreview(null);
    onClose();
    setShowDetailModal(false);
    setFullIngredientDetail(null);
  };

  const handleSuggestFormChange = (field, value) => {
    setSuggestFormData(prev => ({ ...prev, [field]: value }));
  };

  const handlePreviewSuggestion = async () => {
    if (suggestLoading || !suggestFormData.custom_name.trim()) {
      alert('Please enter ingredient name');
      return;
    }
    setSuggestLoading(true);
    try {
      const data = await ingredientService.previewSuggestIngredient(dishUid, {
        custom_name: suggestFormData.custom_name,
        category: suggestFormData.category,
        weight: suggestFormData.weight,
        energy: Number(suggestFormData.energy),
        protein: Number(suggestFormData.protein),
        lipid: Number(suggestFormData.lipid),
        carbohydrate: Number(suggestFormData.carbohydrate),
        fiber: Number(suggestFormData.fiber),
        natri: Number(suggestFormData.natri),
        kali: Number(suggestFormData.kali),
        vitamin_b_2: Number(suggestFormData.vitamin_b_2),
        vitamin_pp: Number(suggestFormData.vitamin_pp),
        vitamin_c: Number(suggestFormData.vitamin_c),
        calcium: Number(suggestFormData.calcium),
        phosphorus: Number(suggestFormData.phosphorus),
        fe: Number(suggestFormData.fe),
        mg: Number(suggestFormData.mg),
        zn: Number(suggestFormData.zn)
      });
      setSuggestPreview(data);
    } catch (error) {
      console.error('Preview suggestion failed:', error);
      alert('Preview failed: ' + error.message);
    } finally {
      setSuggestLoading(false);
      isSubmittingRef.current = false;
    }
  };

  const handleSelectCandidate = (candidate) => {
    setSelectedIngredient({
      uid: candidate.uid,
      name: candidate.name,
      category: candidate.category
    });
    setShowSuggestForm(false);
  };

  const handleSubmitSuggestion = async () => {
    if (suggestLoading || !suggestFormData.custom_name.trim() || isSubmittingRef.current) {
      alert('Please enter ingredient name');
      return;
    }
    isSubmittingRef.current = true;
    setSuggestLoading(true);
    try {
      await ingredientService.suggestIngredientForDish(dishUid, {
        custom_name: suggestFormData.custom_name,
        category: suggestFormData.category,
        weight: suggestFormData.weight,
        energy: Number(suggestFormData.energy),
        protein: Number(suggestFormData.protein),
        lipid: Number(suggestFormData.lipid),
        carbohydrate: Number(suggestFormData.carbohydrate),
        fiber: Number(suggestFormData.fiber),
        natri: Number(suggestFormData.natri),
        kali: Number(suggestFormData.kali),
        vitamin_b_2: Number(suggestFormData.vitamin_b_2),
        vitamin_pp: Number(suggestFormData.vitamin_pp),
        vitamin_c: Number(suggestFormData.vitamin_c),
        calcium: Number(suggestFormData.calcium),
        phosphorus: Number(suggestFormData.phosphorus),
        fe: Number(suggestFormData.fe),
        mg: Number(suggestFormData.mg),
        zn: Number(suggestFormData.zn)
      });
      alert('Suggestion submitted successfully! Admin will review it.');
      setShowSuggestForm(false);
      handleClose();
    } catch (error) {
      console.error('Submit suggestion failed:', error);
      alert('Submit failed: ' + error.message);
    } finally {
      setSuggestLoading(false);
    }
  };

  const renderWarnings = (warnings) => {
    if (!warnings || warnings.length === 0) return null;
    return (
      <div style={{ marginTop: 12 }}>
        <strong style={{ fontSize: '0.8rem', display: 'block', marginBottom: 8 }}>⚠️ Warnings:</strong>
        {warnings.map((warning, idx) => (
          <WarningItem key={idx} $severity={warning.severity || 1}>
            <strong>{warning.field || 'General'}:</strong> {warning.message}
          </WarningItem>
        ))}
      </div>
    );
  };

  const renderConfidence = (confidence) => {
    if (confidence === undefined) return null;
    let label = '';
    let icon = null;
    if (confidence >= 0.8) {
      label = 'High confidence';
      icon = <MdCheckCircle size={14} />;
    } else if (confidence >= 0.5) {
      label = 'Medium confidence';
      icon = <MdTrendingUp size={14} />;
    } else {
      label = 'Low confidence - please verify';
      icon = <MdErrorOutline size={14} />;
    }
    return (
      <ConfidenceBadge $confidence={confidence}>
        {icon} {label} ({Math.round(confidence * 100)}%)
      </ConfidenceBadge>
    );
  };

  const renderNutrition = (nutrition) => {
    if (!nutrition) return null;
    const items = [
      { label: 'Energy', value: nutrition.energy, unit: 'kcal' },
      { label: 'Protein', value: nutrition.protein, unit: 'g' },
      { label: 'Fat', value: nutrition.lipid, unit: 'g' },
      { label: 'Carbs', value: nutrition.carbohydrate, unit: 'g' },
      { label: 'Fiber', value: nutrition.fiber, unit: 'g' },
      { label: 'Sodium', value: nutrition.natri, unit: 'mg' },
      { label: 'Potassium', value: nutrition.kali, unit: 'mg' },
      { label: 'Calcium', value: nutrition.calcium, unit: 'mg' },
      { label: 'Iron', value: nutrition.fe, unit: 'mg' },
      { label: 'Magnesium', value: nutrition.mg, unit: 'mg' },
      { label: 'Zinc', value: nutrition.zn, unit: 'mg' }
    ];
    return (
      <NutritionGrid>
        {items.map(item => (
          <NutritionRow key={item.label}>
            <span>{item.label}:</span>
            <strong>{formatNumber(item.value)} {item.unit}</strong>
          </NutritionRow>
        ))}
      </NutritionGrid>
    );
  };

  return (
    <>
      <Modal isOpen={isOpen} onClose={handleClose} title="Add Ingredient to Dish" size="large">
        {!selectedIngredient ? (
          <>
            <IngredientSearchDropdown 
              onSelectIngredient={handleSelectIngredient}
              onViewDetail={handleViewDetail}
            />
            <SuggestButton onClick={() => setShowSuggestForm(true)}>
              <MdAdd /> Can't find the ingredient? Suggest a new one
            </SuggestButton>

            {showSuggestForm && (
              <SuggestForm>
                <h4 style={{ margin: '0 0 12px 0', fontSize: '0.9rem' }}>Suggest New Ingredient</h4>
                
                <FormGroup>
                  <Label>Ingredient Name *</Label>
                  <input type="text" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.custom_name} onChange={(e) => handleSuggestFormChange('custom_name', e.target.value)} placeholder="e.g., Truffle Oil" />
                </FormGroup>

                <FormRow>
                  <FormGroup>
                    <Label>Category *</Label>
                    <Select value={suggestFormData.category} onChange={(e) => handleSuggestFormChange('category', e.target.value)}>
                      {CATEGORIES.map(c => (<option key={c.value} value={c.value}>{c.label}</option>))}
                    </Select>
                  </FormGroup>
                  <FormGroup>
                    <Label>Weight (g)</Label>
                    <input type="number" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.weight} onChange={(e) => handleSuggestFormChange('weight', Number(e.target.value))} placeholder="100" />
                  </FormGroup>
                </FormRow>

                <FormRow>
                  <FormGroup>
                    <Label>Energy (kcal)</Label>
                    <input type="number" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.energy} onChange={(e) => handleSuggestFormChange('energy', Number(e.target.value))} />
                  </FormGroup>
                  <FormGroup>
                    <Label>Protein (g)</Label>
                    <input type="number" step="0.1" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.protein} onChange={(e) => handleSuggestFormChange('protein', Number(e.target.value))} />
                  </FormGroup>
                </FormRow>

                <FormRow>
                  <FormGroup>
                    <Label>Fat (g)</Label>
                    <input type="number" step="0.1" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.lipid} onChange={(e) => handleSuggestFormChange('lipid', Number(e.target.value))} />
                  </FormGroup>
                  <FormGroup>
                    <Label>Carbohydrates (g)</Label>
                    <input type="number" step="0.1" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.carbohydrate} onChange={(e) => handleSuggestFormChange('carbohydrate', Number(e.target.value))} />
                                      </FormGroup>
                </FormRow>

                <FormRow>
                  <FormGroup>
                    <Label>Fiber (g)</Label>
                    <input type="number" step="0.1" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.fiber} onChange={(e) => handleSuggestFormChange('fiber', Number(e.target.value))} />
                  </FormGroup>
                  <FormGroup>
                    <Label>Sodium (mg)</Label>
                    <input type="number" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.natri} onChange={(e) => handleSuggestFormChange('natri', Number(e.target.value))} />
                  </FormGroup>
                </FormRow>

                <FormRow>
                  <FormGroup>
                    <Label>Potassium (mg)</Label>
                    <input type="number" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.kali} onChange={(e) => handleSuggestFormChange('kali', Number(e.target.value))} />
                  </FormGroup>
                  <FormGroup>
                    <Label>Calcium (mg)</Label>
                    <input type="number" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.calcium} onChange={(e) => handleSuggestFormChange('calcium', Number(e.target.value))} />
                  </FormGroup>
                </FormRow>

                <FormRow>
                  <FormGroup>
                    <Label>Phosphorus (mg)</Label>
                    <input type="number" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.phosphorus} onChange={(e) => handleSuggestFormChange('phosphorus', Number(e.target.value))} />
                  </FormGroup>
                  <FormGroup>
                    <Label>Vitamin B2 (mg)</Label>
                    <input type="number" step="0.01" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.vitamin_b_2} onChange={(e) => handleSuggestFormChange('vitamin_b_2', Number(e.target.value))} />
                  </FormGroup>
                </FormRow>

                <FormRow>
                  <FormGroup>
                    <Label>Vitamin PP (mg)</Label>
                    <input type="number" step="0.01" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.vitamin_pp} onChange={(e) => handleSuggestFormChange('vitamin_pp', Number(e.target.value))} />
                  </FormGroup>
                  <FormGroup>
                    <Label>Vitamin C (mg)</Label>
                    <input type="number" step="0.1" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.vitamin_c} onChange={(e) => handleSuggestFormChange('vitamin_c', Number(e.target.value))} />
                  </FormGroup>
                </FormRow>

                <FormRow>
                  <FormGroup>
                    <Label>Iron (mg)</Label>
                    <input type="number" step="0.1" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.fe} onChange={(e) => handleSuggestFormChange('fe', Number(e.target.value))} />
                  </FormGroup>
                  <FormGroup>
                    <Label>Magnesium (mg)</Label>
                    <input type="number" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.mg} onChange={(e) => handleSuggestFormChange('mg', Number(e.target.value))} />
                  </FormGroup>
                </FormRow>

                <FormGroup>
                  <Label>Zinc (mg)</Label>
                  <input type="number" step="0.01" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0' }} value={suggestFormData.zn} onChange={(e) => handleSuggestFormChange('zn', Number(e.target.value))} placeholder="0" />
                </FormGroup>

                {suggestPreview && (
                  <div style={{ marginTop: 16, padding: 12, background: '#fff', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                    {renderConfidence(suggestPreview.confidence)}
                    <strong>Preview Nutrition:</strong>
                    {renderNutrition(suggestPreview.nutrition)}
                    {renderWarnings(suggestPreview.warnings)}
                    
                    {suggestPreview.candidates && suggestPreview.candidates.length > 0 && (
                      <div style={{ marginTop: 12, background: '#f0fdf4', padding: 12, borderRadius: 8 }}>
                        <strong>Similar ingredients found:</strong>
                        {suggestPreview.candidates.map(candidate => (
                          <div 
                            key={candidate.uid} 
                            style={{ 
                              padding: '6px 0', 
                              cursor: 'pointer', 
                              display: 'flex', 
                              justifyContent: 'space-between',
                              borderBottom: '1px solid #dcfce7'
                            }}
                            onClick={() => handleSelectCandidate(candidate)}
                          >
                            <span>
                              {candidate.name}
                              {candidate.is_best && <span style={{ background: '#10b981', color: 'white', padding: '2px 6px', borderRadius: 12, fontSize: '0.65rem', marginLeft: 8 }}>Best Match</span>}
                            </span>
                            <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
                              Score: {Math.round(candidate.score * 100)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
                  <Button variant="secondary" onClick={() => setShowSuggestForm(false)}>Cancel</Button>
                  <Button variant="secondary" onClick={handlePreviewSuggestion} disabled={suggestLoading}>{suggestLoading ? '...' : 'Preview'}</Button>
                  <Button $primary onClick={handleSubmitSuggestion} disabled={suggestLoading || isSubmittingRef.current}>
                    {suggestLoading ? '...' : 'Submit Suggestion'}
                  </Button>
                </div>
              </SuggestForm>
            )}
          </>
        ) : !showPreview ? (
          <>
            <FormGroup>
              <Label>Selected Ingredient</Label>
              <div style={{ padding: '8px 12px', background: '#f1f5f9', borderRadius: 8, fontWeight: 600, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>{selectedIngredient.name}</span>
                <Button size="small" variant="secondary" onClick={() => handleViewDetail(selectedIngredient)} style={{ padding: '4px 8px' }}>View Details</Button>
              </div>
            </FormGroup>
            <FormGroup>
              <Label>Weight (g)</Label>
              <WeightInput type="number" value={weight} onChange={(e) => setWeight(Number(e.target.value))} min={1} step={10} />
            </FormGroup>
            <ActionButtons>
              <Button onClick={() => setSelectedIngredient(null)}>Back</Button>
              <Button $primary onClick={handlePreview} disabled={loading}>{loading ? 'Loading...' : 'Preview & Continue'}</Button>
            </ActionButtons>
          </>
        ) : (
          <>
            <FormGroup>
              <Label>Ingredient</Label>
              <div style={{ padding: '8px 12px', background: '#f1f5f9', borderRadius: 8, fontWeight: 600 }}>{selectedIngredient.name} - {weight}g</div>
            </FormGroup>
            {renderConfidence(previewData?.confidence)}
            <NutritionPreview><strong>Nutrition Preview:</strong>{renderNutrition(previewData?.nutrition)}</NutritionPreview>
            {renderWarnings(previewData?.warnings)}
            <ActionButtons>
              <Button onClick={() => setShowPreview(false)}><MdArrowBack /> Back</Button>
              <Button $primary onClick={handleConfirmAdd} disabled={loading || isSubmittingRef.current}>{loading ? 'Adding...' : 'Confirm Add'}</Button>
            </ActionButtons>
          </>
        )}
      </Modal>
      
      <IngredientDetailModal 
        isOpen={showDetailModal} 
        ingredient={fullIngredientDetail} 
        onClose={() => { 
          setShowDetailModal(false); 
          setFullIngredientDetail(null); 
        }} 
      />
    </>
  );
};