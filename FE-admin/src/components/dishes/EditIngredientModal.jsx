import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { ingredientService } from '../../services/ingredientService';

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

const Input = styled.input`
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;

  &:focus {
    outline: none;
    border-color: #1e3c72;
  }
`;

const SectionTitle = styled.h4`
  font-size: 0.85rem;
  font-weight: 700;
  color: #1e3c72;
  margin: 16px 0 12px 0;
  padding-bottom: 6px;
  border-bottom: 1px solid #e2e8f0;
`;

const NutritionGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
`;

const ActionButtons = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 12px;
`;

const NutritionPreview = styled.div`
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
  margin-top: 12px;
  font-size: 0.8rem;
`;

const PreviewRow = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
`;

const WarningBox = styled.div`
  background: #fef3c7;
  border-left: 4px solid #f59e0b;
  padding: 12px;
  margin-top: 12px;
  margin-bottom: 16px;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #92400e;
`;

const WarningItem = styled.div`
  padding: 6px 0;
  border-bottom: 1px solid #fde68a;
  
  &:last-child {
    border-bottom: none;
  }
`;

const LoadingOverlay = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px;
  color: #64748b;
`;

// ✅ Hàm làm tròn 2 số thập phân
const roundTo2 = (num) => {
  if (num === null || num === undefined) return 0;
  return Math.round(num * 100) / 100;
};

// Danh sách các field dinh dưỡng
const NUTRITION_FIELDS = [
  'energy', 'protein', 'lipid', 'carbohydrate', 'fiber',
  'natri', 'kali', 'cholesterol', 'retinol', 'caroten',
  'vitamin_b_1', 'vitamin_b_2', 'vitamin_pp', 'vitamin_c',
  'calcium', 'phosphorus', 'fe', 'mg', 'zn'
];

export const EditIngredientModal = ({ isOpen, onClose, onSave, onDelete, dishIngredientUid, dishUid }) => {
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [warnings, setWarnings] = useState([]);
  const [ingredientName, setIngredientName] = useState('');
  
  // Lưu giá trị per 100g để tính toán khi weight thay đổi
  const [baseNutrition, setBaseNutrition] = useState({});
  
  const [formData, setFormData] = useState({
    weight: 100,
    energy: 0,
    protein: 0,
    lipid: 0,
    carbohydrate: 0,
    fiber: 0,
    natri: 0,
    kali: 0,
    cholesterol: 0,
    retinol: 0,
    caroten: 0,
    vitamin_b_1: 0,
    vitamin_b_2: 0,
    vitamin_pp: 0,
    vitamin_c: 0,
    calcium: 0,
    phosphorus: 0,
    fe: 0,
    mg: 0,
    zn: 0
  });

  // Gọi API khi modal mở và có dishIngredientUid
  useEffect(() => {
    if (isOpen && dishIngredientUid) {
      fetchDishIngredientDetail();
    }
  }, [isOpen, dishIngredientUid]);

  const fetchDishIngredientDetail = async () => {
    setFetching(true);
    try {
      console.log('📤 [EditIngredientModal] Fetching dish ingredient detail for UID:', dishIngredientUid);
      const response = await ingredientService.getDishIngredient(dishIngredientUid);
      console.log('📥 [EditIngredientModal] Response:', response);
      
      const data = response?.data || response;
      
      setIngredientName(data.ingredient_name || data.custom_name || 'Unknown Ingredient');
      
      const currentWeight = data.weight || 100;
      
      // ✅ Tính giá trị per 100g từ dữ liệu hiện tại, làm tròn 2 số thập phân
      const scaleTo100 = 100 / currentWeight;
      const baseValues = {};
      NUTRITION_FIELDS.forEach(field => {
        baseValues[field] = roundTo2((data[field] || 0) * scaleTo100);
      });
      setBaseNutrition(baseValues);
      
      // ✅ Set form data với giá trị hiện tại, làm tròn 2 số thập phân
      const currentValues = {};
      NUTRITION_FIELDS.forEach(field => {
        currentValues[field] = roundTo2(data[field] || 0);
      });
      
      setFormData({
        weight: currentWeight,
        ...currentValues
      });
      
      setWarnings([]);
    } catch (error) {
      console.error('❌ [EditIngredientModal] Failed to fetch dish ingredient:', error);
      alert('Failed to load ingredient details: ' + error.message);
    } finally {
      setFetching(false);
    }
  };

  // ✅ Xử lý khi weight thay đổi - scale tất cả giá trị theo tỷ lệ dựa trên per 100g
  const handleWeightChange = (newWeight) => {
    const newWeightNum = parseFloat(newWeight) || 0;
    if (newWeightNum <= 0) {
      setFormData(prev => ({ ...prev, weight: newWeightNum }));
      return;
    }
    
    // Tính giá trị mới dựa trên base (per 100g), làm tròn 2 số thập phân
    const ratio = newWeightNum / 100;
    const scaledValues = {};
    NUTRITION_FIELDS.forEach(field => {
      scaledValues[field] = roundTo2((baseNutrition[field] || 0) * ratio);
    });
    
    setFormData(prev => ({
      ...prev,
      weight: newWeightNum,
      ...scaledValues
    }));
  };

  // ✅ Xử lý khi thay đổi một field dinh dưỡng - cập nhật cả baseNutrition để giữ tỷ lệ
  const handleNutritionChange = (field, value) => {
    const newValue = roundTo2(parseFloat(value) || 0);
    const currentWeight = formData.weight || 100;
    
    // Tính lại giá trị per 100g dựa trên giá trị mới và weight hiện tại, làm tròn 2 số thập phân
    const newBaseValue = roundTo2(newValue * (100 / currentWeight));
    
    setBaseNutrition(prev => ({
      ...prev,
      [field]: newBaseValue
    }));
    
    setFormData(prev => ({
      ...prev,
      [field]: newValue
    }));
  };

  const handleChange = (field, value) => {
    if (field === 'weight') {
      handleWeightChange(value);
    } else {
      handleNutritionChange(field, value);
    }
  };

  const handleSave = async () => {
    if (formData.weight <= 0) {
      alert('Weight must be greater than 0');
      return;
    }
    
    setLoading(true);
    setWarnings([]);
    
    try {
      const updateData = {
        weight: roundTo2(formData.weight),
        energy: roundTo2(formData.energy),
        protein: roundTo2(formData.protein),
        lipid: roundTo2(formData.lipid),
        carbohydrate: roundTo2(formData.carbohydrate),
        fiber: roundTo2(formData.fiber),
        natri: roundTo2(formData.natri),
        kali: roundTo2(formData.kali),
        cholesterol: roundTo2(formData.cholesterol),
        retinol: roundTo2(formData.retinol),
        caroten: roundTo2(formData.caroten),
        vitamin_b_1: roundTo2(formData.vitamin_b_1),
        vitamin_b_2: roundTo2(formData.vitamin_b_2),
        vitamin_pp: roundTo2(formData.vitamin_pp),
        vitamin_c: roundTo2(formData.vitamin_c),
        calcium: roundTo2(formData.calcium),
        phosphorus: roundTo2(formData.phosphorus),
        fe: roundTo2(formData.fe),
        mg: roundTo2(formData.mg),
        zn: roundTo2(formData.zn)
      };
      
      console.log('📤 [EditIngredientModal] Updating dish ingredient:', dishIngredientUid, updateData);
      const response = await ingredientService.updateDishIngredient(dishIngredientUid, updateData);
      console.log('📥 [EditIngredientModal] Update response:', response);
      
      if (response?.warnings && response.warnings.length > 0) {
        setWarnings(response.warnings);
        const updatedIngredient = { 
          uid: dishIngredientUid,
          name: ingredientName,
          ...formData 
        };
        onSave(updatedIngredient, false);
        return;
      }
      
      const updatedIngredient = { 
        uid: dishIngredientUid,
        name: ingredientName,
        ...formData 
      };
      onSave(updatedIngredient);
      onClose();
    } catch (error) {
      console.error('❌ [EditIngredientModal] Update failed:', error);
      if (error.response?.data?.message) {
        alert('Update failed: ' + error.response.data.message);
      } else if (error.response?.data?.message_code === 'VALIDATION_ERROR') {
        alert('Validation error: ' + JSON.stringify(error.response.data.data));
      } else {
        alert('Update failed: ' + error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to remove this ingredient from the dish?')) {
      setLoading(true);
      try {
        console.log('📤 [EditIngredientModal] Deleting dish ingredient:', dishIngredientUid);
        await ingredientService.softDeleteDishIngredient(dishIngredientUid);
        onDelete();
        onClose();
      } catch (error) {
        console.error('❌ [EditIngredientModal] Delete failed:', error);
        alert('Delete failed: ' + error.message);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Edit Ingredient: ${ingredientName}`} size="large">
      {fetching ? (
        <LoadingOverlay>Loading ingredient details...</LoadingOverlay>
      ) : (
        <>
          {warnings.length > 0 && (
            <WarningBox>
              <strong>⚠️ Warnings:</strong>
              {warnings.map((warning, idx) => (
                <WarningItem key={idx}>
                  <strong>{warning.field || 'General'}:</strong> {warning.message}
                </WarningItem>
              ))}
              <div style={{ marginTop: 8, fontSize: '0.75rem', color: '#92400e' }}>
                Your changes have been saved but may need review.
              </div>
            </WarningBox>
          )}

          <FormGroup>
            <Label>Ingredient Name</Label>
            <div style={{ padding: '8px 12px', background: '#f1f5f9', borderRadius: 8 }}>
              {ingredientName}
            </div>
          </FormGroup>

          <FormGroup>
            <Label>Weight (g) *</Label>
            <Input
              type="number"
              value={formData.weight}
              onChange={(e) => handleChange('weight', e.target.value)}
              min={1}
              step={10}
            />
            <small style={{ color: '#64748b', fontSize: '0.7rem' }}>
              💡 Changing weight will automatically scale all nutrition values
            </small>
          </FormGroup>

          <SectionTitle>📊 Basic Nutrition (per {formData.weight}g)</SectionTitle>
          <NutritionGrid>
            <FormGroup>
              <Label>Energy (kcal)</Label>
              <Input type="number" step="0.1" value={formData.energy} onChange={(e) => handleChange('energy', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Protein (g)</Label>
              <Input type="number" step="0.1" value={formData.protein} onChange={(e) => handleChange('protein', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Fat (g)</Label>
              <Input type="number" step="0.1" value={formData.lipid} onChange={(e) => handleChange('lipid', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Carbohydrates (g)</Label>
              <Input type="number" step="0.1" value={formData.carbohydrate} onChange={(e) => handleChange('carbohydrate', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Fiber (g)</Label>
              <Input type="number" step="0.1" value={formData.fiber} onChange={(e) => handleChange('fiber', e.target.value)} />
            </FormGroup>
          </NutritionGrid>

          <SectionTitle>🧂 Minerals (mg)</SectionTitle>
          <NutritionGrid>
            <FormGroup>
              <Label>Sodium</Label>
              <Input type="number" step="0.1" value={formData.natri} onChange={(e) => handleChange('natri', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Potassium</Label>
              <Input type="number" step="0.1" value={formData.kali} onChange={(e) => handleChange('kali', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Calcium</Label>
              <Input type="number" step="0.1" value={formData.calcium} onChange={(e) => handleChange('calcium', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Phosphorus</Label>
              <Input type="number" step="0.1" value={formData.phosphorus} onChange={(e) => handleChange('phosphorus', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Iron</Label>
              <Input type="number" step="0.1" value={formData.fe} onChange={(e) => handleChange('fe', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Magnesium</Label>
              <Input type="number" step="0.1" value={formData.mg} onChange={(e) => handleChange('mg', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Zinc</Label>
              <Input type="number" step="0.1" value={formData.zn} onChange={(e) => handleChange('zn', e.target.value)} />
            </FormGroup>
          </NutritionGrid>

          <SectionTitle>💊 Vitamins & Others</SectionTitle>
          <NutritionGrid>
            <FormGroup>
              <Label>Cholesterol (mg)</Label>
              <Input type="number" step="0.1" value={formData.cholesterol} onChange={(e) => handleChange('cholesterol', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Vitamin A - Retinol (µg)</Label>
              <Input type="number" step="0.1" value={formData.retinol} onChange={(e) => handleChange('retinol', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Beta-carotene (µg)</Label>
              <Input type="number" step="0.1" value={formData.caroten} onChange={(e) => handleChange('caroten', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Vitamin B1 (mg)</Label>
              <Input type="number" step="0.01" value={formData.vitamin_b_1} onChange={(e) => handleChange('vitamin_b_1', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Vitamin B2 (mg)</Label>
              <Input type="number" step="0.01" value={formData.vitamin_b_2} onChange={(e) => handleChange('vitamin_b_2', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Vitamin PP - Niacin (mg)</Label>
              <Input type="number" step="0.01" value={formData.vitamin_pp} onChange={(e) => handleChange('vitamin_pp', e.target.value)} />
            </FormGroup>
            <FormGroup>
              <Label>Vitamin C (mg)</Label>
              <Input type="number" step="0.1" value={formData.vitamin_c} onChange={(e) => handleChange('vitamin_c', e.target.value)} />
            </FormGroup>
          </NutritionGrid>

          <NutritionPreview>
            <strong>📊 Total Nutrition (for {formData.weight}g):</strong>
            <PreviewRow><span>Energy:</span><span>{roundTo2(formData.energy)} kcal</span></PreviewRow>
            <PreviewRow><span>Protein:</span><span>{roundTo2(formData.protein)} g</span></PreviewRow>
            <PreviewRow><span>Fat:</span><span>{roundTo2(formData.lipid)} g</span></PreviewRow>
            <PreviewRow><span>Carbs:</span><span>{roundTo2(formData.carbohydrate)} g</span></PreviewRow>
          </NutritionPreview>

          <ActionButtons>
            <Button variant="danger" onClick={handleDelete} disabled={loading}>
              Remove
            </Button>
            <ButtonGroup>
              <Button onClick={onClose}>Cancel</Button>
              <Button $primary onClick={handleSave} disabled={loading}>
                {loading ? 'Saving...' : 'Save Changes'}
              </Button>
            </ButtonGroup>
          </ActionButtons>
        </>
      )}
    </Modal>
  );
};