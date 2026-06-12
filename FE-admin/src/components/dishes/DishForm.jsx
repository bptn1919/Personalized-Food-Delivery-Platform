import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { MdCloudUpload, MdAdd, MdDelete, MdEdit, MdVisibility, MdInfo, MdTrendingUp, MdErrorOutline, MdCheckCircle } from 'react-icons/md';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { DISH_CATEGORIES, DISH_STATUS } from '../../utils/constants';
import { AddIngredientModal } from './AddIngredientModal';
import { EditIngredientModal } from './EditIngredientModal';
import { IngredientDetailModal } from '../ingredients/IngredientDetailModal';
import { ingredientService } from '../../services/ingredientService';
import { dishLocationService } from '../../services/dishLocationService';

// --- Styled Components ---

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 10px 0;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const Label = styled.label`
  font-size: 0.85rem;
  color: #475569;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 4px;

  span { color: #ef4444; }
`;

const CommonInputStyles = `
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  font-size: 0.95rem;
  color: #1e293b;
  background: #f8fafc;
  transition: all 0.2s;

  &:focus {
    outline: none;
    border-color: #1e3c72;
    background: white;
    box-shadow: 0 0 0 4px rgba(30, 60, 114, 0.1);
  }
`;

const Input = styled.input`${CommonInputStyles}`;
const Select = styled.select`${CommonInputStyles} cursor: pointer;`;
const TextArea = styled.textarea`${CommonInputStyles} min-height: 100px; resize: vertical;`;

const FormRow = styled.div`
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  
  @media (min-width: 640px) {
    grid-template-columns: 1fr 1fr;
  }
`;

const UploadZone = styled.label`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  border: 2px dashed #e2e8f0;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: ${({ $hasImage }) => ($hasImage ? '#fff' : '#f8fafc')};

  &:hover {
    border-color: #1e3c72;
    background: #f1f5f9;
  }

  input { display: none; }
`;

const PreviewWrapper = styled.div`
  width: 100%;
  max-height: 200px;
  overflow: hidden;
  border-radius: 12px;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }
`;

const PlaceholderContent = styled.div`
  text-align: center;
  color: #94a3b8;
  svg { font-size: 32px; margin-bottom: 8px; }
  p { font-size: 0.85rem; font-weight: 500; }
`;

const ActionButtons = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 10px;
  padding-top: 20px;
  border-top: 1px solid #f1f5f9;
`;

// Ingredients Section
const IngredientsSection = styled.div`
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 16px;
  margin-top: 8px;
`;

const IngredientsHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
`;

const IngredientsTitle = styled.h4`
  margin: 0;
  font-size: 0.9rem;
  font-weight: 700;
  color: #1e3c72;
`;

const AddIngredientButton = styled.button`
  background: #1e3c72;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.75rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;

  &:hover {
    background: #2a5298;
  }
`;

const IngredientList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;
`;

const IngredientItem = styled.div`
  background: #f8fafc;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s;

  &:hover {
    background: #f1f5f9;
  }
`;

const IngredientInfo = styled.div`
  flex: 1;
`;

const IngredientName = styled.div`
  font-weight: 600;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
`;

const IngredientWeight = styled.div`
  font-size: 0.75rem;
  color: #64748b;
`;

const IngredientNutrition = styled.div`
  font-size: 0.7rem;
  color: #94a3b8;
  margin-top: 4px;
`;

const ActionGroup = styled.div`
  display: flex;
  gap: 4px;
  align-items: center;
`;

const ActionIcon = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;

  &:hover {
    background: #e2e8f0;
    color: ${({ $danger }) => $danger ? '#ef4444' : '#1e3c72'};
  }
`;

const EditIcon = styled.div`
  color: #64748b;
  margin-right: 4px;
`;

const ConfidenceBox = styled.div`
  background: ${({ $confidence }) => {
    if ($confidence >= 0.8) return '#dcfce7';
    if ($confidence >= 0.5) return '#fef3c7';
    return '#fee2e2';
  }};
  border-left: 4px solid ${({ $confidence }) => {
    if ($confidence >= 0.8) return '#10b981';
    if ($confidence >= 0.5) return '#f59e0b';
    return '#ef4444';
  }};
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 0.85rem;
`;

const NutritionTotalBox = styled.div`
  background: #f8fafc;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 16px;
  border: 1px solid #e2e8f0;
`;

const NutritionTitle = styled.div`
  font-weight: 700;
  color: #1e3c72;
  margin-bottom: 12px;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const NutritionGridFull = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  
  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
  }
`;

const NutritionItemFull = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  font-size: 0.8rem;
  
  .label {
    color: #64748b;
    font-weight: 500;
  }
  
  .value {
    font-weight: 700;
    color: #1e293b;
  }
`;
const InfoMessage = styled.div`
  background: #e0f2fe;
  border-left: 4px solid #0284c7;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 0.85rem;
  color: #0369a1;
`;

// --- Main Component ---

export const DishForm = ({ isOpen, onClose, onSubmit, initialData = null }) => {
  const [formData, setFormData] = useState({
    name: '',
    category: DISH_CATEGORIES.FOOD,
    description: '',
    price: '',
    status: DISH_STATUS.AVAILABLE,
  });

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [ingredients, setIngredients] = useState([]);
  const [showAddIngredient, setShowAddIngredient] = useState(false);
  const [editingIngredient, setEditingIngredient] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [loadingIngredients, setLoadingIngredients] = useState(false);
  const [dishConfidence, setDishConfidence] = useState(null);
  const [dishConfidenceText, setDishConfidenceText] = useState('');
  const [dishNote, setDishNote] = useState('');
  const [nutritionTotal, setNutritionTotal] = useState(null);
  const [showIngredientDetail, setShowIngredientDetail] = useState(false);
  const [selectedIngredientDetail, setSelectedIngredientDetail] = useState(null);
  
  // Location state
  const [locations, setLocations] = useState([]);
  const [selectedLocationId, setSelectedLocationId] = useState(null);
  const [loadingLocations, setLoadingLocations] = useState(false);

  const isEdit = !!initialData;

const fetchLocations = async () => {
  setLoadingLocations(true);
  try {
    const locationsList = await dishLocationService.getCountries();
    console.log('✅ Fetched locations:', locationsList);
    
    // locationsList đã là array rồi
    setLocations(locationsList);
    
    // Debug: Kiểm tra selected location khi edit
    if (initialData?.location_id) {
      const found = locationsList.find(loc => loc.id === initialData.location_id);
      console.log('📍 Current dish location_id:', initialData.location_id);
      console.log('📍 Found location:', found);
    }
  } catch (error) {
    console.error('Failed to fetch locations:', error);
    setLocations([]);
  } finally {
    setLoadingLocations(false);
  }
};

const fetchDishIngredients = async (dishUid) => {
  if (!dishUid) return;
  setLoadingIngredients(true);
  try {
    const data = await ingredientService.getDishIngredientsForChef(dishUid);
    console.log('📦 Fetched dish ingredients for dish:', dishUid);
    
    // ✅ THÊM LOG NÀY ĐỂ KIỂM TRA RESPONSE GỐC
    console.log('📦 Full API response:', JSON.stringify(data, null, 2));
    
    if (data?.data?.confidence_of_dish !== undefined) {
      setDishConfidence(data.data.confidence_of_dish);
      setDishConfidenceText(data.data.confidence_text || '');
      setDishNote(data.data.note || '');
    } else {
      setDishConfidence(null);
      setDishConfidenceText('');
      setDishNote('');
    }
    
    if (data?.data?.nutrition_total) {
      setNutritionTotal(data.data.nutrition_total);
    } else {
      setNutritionTotal(null);
    }
    
    if (data?.data?.ingredients && data.data.ingredients.length > 0) {
      // ✅ LOG TỪNG INGREDIENT ĐỂ XEM CÓ ingredient_uid KHÔNG
      console.log('📦 Raw ingredients from API:');
      data.data.ingredients.forEach((ing, idx) => {
        console.log(`  ${idx + 1}. name: ${ing.ingredient_name}, ingredient_uid: ${ing.ingredient_uid}, uid: ${ing.uid}`);
      });
      
      const formattedIngredients = data.data.ingredients.map(ing => ({
        dishIngredientUid: ing.uid,
        uid: ing.uid,
        name: ing.ingredient_name,
        ingredient_uid: ing.ingredient_uid,  // Nếu API trả về null thì sẽ là null
        weight: ing.weight,
        energy: ing.energy,
        protein: ing.protein,
        lipid: ing.lipid,
        carbohydrate: ing.carbohydrate,
        fiber: ing.fiber,
        source: ing.source,
        approval_status: ing.approval_status
      }));
      
      console.log('📦 Formatted ingredients:', formattedIngredients);
      setIngredients(formattedIngredients);
    } else {
      setIngredients([]);
    }
  } catch (error) {
    console.error('❌ Failed to fetch dish ingredients:', error);
    setIngredients([]);
  } finally {
    setLoadingIngredients(false);
  }
};

 useEffect(() => {
  if (isOpen) {
    console.log('📂 [DishForm] Modal opened');
    console.log('📂 [DishForm] isEdit:', !!initialData);
    
    fetchLocations();
    
    if (initialData) {
      console.log('🔵 [DishForm] Opening EDIT mode for dish:', {
        uid: initialData.uid,
        name: initialData.name,
        location_id: initialData.location_id,
        category: initialData.category,
        status: initialData.status,
        price: initialData.price,
        hasImage: !!initialData.public_url,
        fullData: initialData
      });
      
      console.log('📍 [DishForm] Setting selectedLocationId to:', initialData.location_id || 'null (no location)');
      setSelectedLocationId(initialData.location_id || null);
      
      console.log('📝 [DishForm] Setting form data...');
      setFormData({
        name: initialData.name || '',
        category: initialData.category || DISH_CATEGORIES.FOOD,
        description: initialData.description || '',
        price: initialData.price ? Math.floor(initialData.price) : '',
        status: initialData.status || DISH_STATUS.AVAILABLE,
      });
      
      console.log('🖼️ [DishForm] Setting preview URL:', initialData.public_url || 'none');
      setPreviewUrl(initialData.public_url || null);
      
      setSelectedFile(null);
      
      console.log('🍽️ [DishForm] Fetching ingredients for dish:', initialData.uid);
      fetchDishIngredients(initialData.uid);
      
    } else {
      console.log('🟢 [DishForm] Opening CREATE mode - new dish');
      console.log('🟢 [DishForm] Resetting all form fields');
      
      setFormData({
        name: '', 
        category: DISH_CATEGORIES.FOOD, 
        description: '', 
        price: '', 
        status: DISH_STATUS.AVAILABLE,
      });
      setPreviewUrl(null);
      setIngredients([]);
      setDishConfidence(null);
      setNutritionTotal(null);
      setSelectedLocationId(null);
      setSelectedFile(null);
      
      console.log('✅ [DishForm] Create mode ready, location_id set to null');
    }
  } else {
    console.log('🚪 [DishForm] Modal closed');
  }
}, [isOpen, initialData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleAddIngredient = async (newIngredient) => {
    if (isEdit && initialData?.uid) {
      try {
        await ingredientService.addIngredientToDish(initialData.uid, {
          ingredient_uid: newIngredient.ingredient_uid,
          weight: newIngredient.weight
        });
        await fetchDishIngredients(initialData.uid);
      } catch (error) {
        console.error('Add ingredient failed:', error);
        alert('Failed to add ingredient: ' + error.message);
      }
    } else {
      const calculatedNutrition = {
        energy: (newIngredient.energy || 0) * newIngredient.weight / 100,
        protein: (newIngredient.protein || 0) * newIngredient.weight / 100,
        lipid: (newIngredient.lipid || 0) * newIngredient.weight / 100,
        carbohydrate: (newIngredient.carbohydrate || 0) * newIngredient.weight / 100,
      };
      setIngredients([...ingredients, { ...newIngredient, ...calculatedNutrition }]);
    }
  };

  const handleUpdateIngredient = async (updatedIngredient, shouldRefresh = true) => {
    console.log('✏️ Updating ingredient:', updatedIngredient);
    
    if (updatedIngredient.uid) {
      const index = ingredients.findIndex(i => i.uid === updatedIngredient.uid);
      if (index !== -1) {
        const newIngredients = [...ingredients];
        newIngredients[index] = updatedIngredient;
        setIngredients(newIngredients);
      }
      
      if (shouldRefresh && initialData?.uid) {
        await fetchDishIngredients(initialData.uid);
      }
    }
  };

  const handleRemoveIngredient = async (index) => {
    const ingredientToRemove = ingredients[index];
    const dishIngredientUid = ingredientToRemove.dishIngredientUid || ingredientToRemove.uid;
    
    if (!dishIngredientUid) {
      console.error('❌ No DishIngredient UID found!');
      const newIngredients = [...ingredients];
      newIngredients.splice(index, 1);
      setIngredients(newIngredients);
      return;
    }
    
    if (isEdit && initialData?.uid) {
      try {
        await ingredientService.softDeleteDishIngredient(dishIngredientUid);
        await fetchDishIngredients(initialData.uid);
      } catch (error) {
        console.error('❌ Delete failed:', error);
        if (error.response?.data?.message_code === 'DISH_INGREDIENT_NOT_FOUND') {
          console.warn('⚠️ Ingredient not found on server, removing from UI only');
          const newIngredients = [...ingredients];
          newIngredients.splice(index, 1);
          setIngredients(newIngredients);
        } else {
          alert('Delete failed: ' + error.message);
        }
      }
    } else {
      const newIngredients = [...ingredients];
      newIngredients.splice(index, 1);
      setIngredients(newIngredients);
    }
  };

  const handleEditIngredient = (item) => {
    setEditingIngredient(item);
    setShowEditModal(true);
  };

const handleViewIngredientDetail = async (item) => {
  console.log('🔍 Viewing ingredient detail:', item);
  console.log('🔍 Ingredient UID:', item.ingredient_uid);
  
  // ✅ SỬA: Kiểm tra ingredient_uid thay vì ingredient_uid
  if (item.ingredient_uid) {
    setLoadingIngredients(true);
    try {
      const detail = await ingredientService.getIngredientDetail(item.ingredient_uid);
      console.log('📥 Ingredient detail response:', detail);
      
      const ingredientData = detail?.data || detail;
      setSelectedIngredientDetail(ingredientData);
      setShowIngredientDetail(true);
    } catch (error) {
      console.error('❌ Failed to fetch ingredient detail:', error);
      alert('Failed to load ingredient details');
    } finally {
      setLoadingIngredients(false);
    }
  } else {
    console.warn('❌ No ingredient_uid found for item:', item);
    alert('Cannot view details: No ingredient UID available');
  }
};

  const getConfidenceIcon = (confidence) => {
    if (confidence >= 0.8) return <MdCheckCircle size={16} />;
    if (confidence >= 0.5) return <MdTrendingUp size={16} />;
    return <MdErrorOutline size={16} />;
  };

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title={isEdit ? 'Update Dish Details' : 'Create New Menu Item'}
        size="large"
      >
        <Form onSubmit={(e) => { 
          e.preventDefault(); 
          onSubmit({ ...formData, image: selectedFile, ingredients, location_id: selectedLocationId }); 
        }}>
          <FormRow>
            <FormGroup>
              <Label>Dish Name <span>*</span></Label>
              <Input
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="e.g. Traditional Beef Pho"
              />
            </FormGroup>

            <FormGroup>
              <Label>Category <span>*</span></Label>
              <Select name="category" value={formData.category} onChange={handleChange} required>
                <option value={DISH_CATEGORIES.FOOD}>Main Course</option>
                <option value={DISH_CATEGORIES.BEVERAGES}>Beverages</option>
                <option value={DISH_CATEGORIES.DESSERT}>Dessert</option>
              </Select>
            </FormGroup>
          </FormRow>

          <FormGroup>
            <Label>Product Description</Label>
            <TextArea
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Describe the ingredients, taste, or special preparation..."
            />
          </FormGroup>

          <FormRow>
            <FormGroup>
              <Label>Price (VND) <span>*</span></Label>
              <Input
                type="number"
                name="price"
                value={formData.price}
                onChange={handleChange}
                required
                min="0"
                step="1000"
                placeholder="55000"
              />
            </FormGroup>

            <FormGroup>
              <Label>Availability Status</Label>
              <Select name="status" value={formData.status} onChange={handleChange}>
                <option value={DISH_STATUS.AVAILABLE}>Active / In Stock</option>
                <option value={DISH_STATUS.UNAVAILABLE}>Unavailable / Out of Stock</option>
              </Select>
            </FormGroup>
          </FormRow>

          {/* Location Select */}
          <FormRow>
            <FormGroup>
              <Label>📍 Location</Label>
              <Select 
                value={selectedLocationId || ''}
                onChange={(e) => setSelectedLocationId(e.target.value ? parseInt(e.target.value) : null)}
                disabled={loadingLocations}
              >
                <option value="">Select a location (optional)</option>
                {locations.map(loc => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </Select>
              <p style={{ fontSize: '0.7rem', color: '#64748b', marginTop: 4 }}>
                Choose the region/country where this dish is available
              </p>
            </FormGroup>
            <div></div>
          </FormRow>

          {/* Confidence Box */}
          {isEdit && dishConfidence !== null && (
            <ConfidenceBox $confidence={dishConfidence}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                {getConfidenceIcon(dishConfidence)}
                <strong>{dishConfidenceText || `Confidence: ${Math.round(dishConfidence * 100)}%`}</strong>
              </div>
              {dishNote && <div style={{ marginTop: 4, fontSize: '0.75rem' }}>{dishNote}</div>}
            </ConfidenceBox>
          )}

          {isEdit && nutritionTotal && (
            <NutritionTotalBox>
              <NutritionTitle>
                <span>📊</span> Total Nutrition (per serving)
              </NutritionTitle>
              <NutritionGridFull>
                <NutritionItemFull>
                  <span className="label">Energy</span>
                  <span className="value">{Math.round(nutritionTotal.energy || 0)} kcal</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Protein</span>
                  <span className="value">{(nutritionTotal.protein || 0).toFixed(1)} g</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Fat</span>
                  <span className="value">{(nutritionTotal.lipid || 0).toFixed(1)} g</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Carbohydrates</span>
                  <span className="value">{(nutritionTotal.carbohydrate || 0).toFixed(1)} g</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Fiber</span>
                  <span className="value">{(nutritionTotal.fiber || 0).toFixed(1)} g</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Sodium</span>
                  <span className="value">{Math.round(nutritionTotal.natri || 0)} mg</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Potassium</span>
                  <span className="value">{Math.round(nutritionTotal.kali || 0)} mg</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Calcium</span>
                  <span className="value">{Math.round(nutritionTotal.calcium || 0)} mg</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Iron</span>
                  <span className="value">{(nutritionTotal.fe || 0).toFixed(1)} mg</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Magnesium</span>
                  <span className="value">{Math.round(nutritionTotal.mg || 0)} mg</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Phosphorus</span>
                  <span className="value">{Math.round(nutritionTotal.phosphorus || 0)} mg</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Zinc</span>
                  <span className="value">{(nutritionTotal.zn || 0).toFixed(1)} mg</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Cholesterol</span>
                  <span className="value">{Math.round(nutritionTotal.cholesterol || 0)} mg</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Vitamin A</span>
                  <span className="value">{Math.round(nutritionTotal.retinol || 0)} µg</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Beta-carotene</span>
                  <span className="value">{Math.round(nutritionTotal.caroten || 0)} µg</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Vitamin B1</span>
                  <span className="value">{(nutritionTotal.vitamin_b_1 || 0).toFixed(2)} mg</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Vitamin B2</span>
                  <span className="value">{(nutritionTotal.vitamin_b_2 || 0).toFixed(2)} mg</span>
                </NutritionItemFull>
                <NutritionItemFull>
                  <span className="label">Vitamin C</span>
                  <span className="value">{Math.round(nutritionTotal.vitamin_c || 0)} mg</span>
                </NutritionItemFull>
              </NutritionGridFull>
            </NutritionTotalBox>
          )}

          <IngredientsSection>
            <IngredientsHeader>
              <IngredientsTitle>Ingredients ({ingredients.length})</IngredientsTitle>
              {isEdit && (
                <AddIngredientButton type="button" onClick={() => setShowAddIngredient(true)}>
                  <MdAdd size={14} /> Add Ingredient
                </AddIngredientButton>
              )}
            </IngredientsHeader>
            
            <IngredientList>
              {loadingIngredients ? (
                <div style={{ textAlign: 'center', padding: 20, color: '#94a3b8' }}>
                  Loading ingredients...
                </div>
              ) : (
                ingredients.map((item, index) => (
                  <IngredientItem key={item.dishIngredientUid || item.uid || index}>
                    <IngredientInfo>
                      <IngredientName>
                        {item.name}
                        {item.source === 'CHEF_SUGGESTION' && item.approval_status === 'PENDING' && (
                          <span style={{ 
                            fontSize: '0.6rem', 
                            background: '#fef3c7', 
                            color: '#92400e',
                            padding: '2px 6px',
                            borderRadius: '12px'
                          }}>
                            Pending
                          </span>
                        )}
                      </IngredientName>
                      <IngredientWeight>Weight: {item.weight}g</IngredientWeight>
                      <IngredientNutrition>
                        Energy: {Math.round(item.energy)} kcal | Protein: {item.protein}g | Carbs: {item.carbohydrate}g
                      </IngredientNutrition>
                    </IngredientInfo>
                    <ActionGroup>
                      <ActionIcon 
                        onClick={() => handleEditIngredient(item)} 
                        title="Edit"
                      >
                        <MdEdit size={16} />
                      </ActionIcon>
                    </ActionGroup>
                  </IngredientItem>
                ))
              )}
              {!loadingIngredients && ingredients.length === 0 && isEdit && (
                <div style={{ textAlign: 'center', color: '#94a3b8', padding: '20px' }}>
                  No ingredients added yet. Click "Add Ingredient" to add.
                </div>
              )}
              {!loadingIngredients && ingredients.length === 0 && !isEdit && (
                <div style={{ textAlign: 'center', color: '#94a3b8', padding: '20px' }}>
                  No ingredients yet. Save the dish first to add ingredients.
                </div>
              )}
            </IngredientList>
          </IngredientsSection>

          <FormGroup>
            <Label>Visual Representation</Label>
            <UploadZone $hasImage={!!previewUrl}>
              <input type="file" onChange={handleFileChange} accept="image/*" />
              {previewUrl ? (
                <PreviewWrapper>
                  <img src={previewUrl} alt="Dish Preview" />
                </PreviewWrapper>
              ) : (
                <PlaceholderContent>
                  <MdCloudUpload />
                  <p>Click to upload dish photo</p>
                  <small>Supports: JPG, PNG (Max 5MB)</small>
                </PlaceholderContent>
              )}
            </UploadZone>
            {isEdit && !selectedFile && initialData?.public_url && (
              <p style={{ fontSize: '0.75rem', color: '#64748b', textAlign: 'center', marginTop: '4px' }}>
                Current image will be maintained unless a new one is selected.
              </p>
            )}
          </FormGroup>

          <ActionButtons>
            <Button type="button" onClick={onClose}>Cancel</Button>
            <Button type="submit" $primary>
              {isEdit ? 'Save Changes' : 'Publish Dish'}
            </Button>
          </ActionButtons>
        </Form>
      </Modal>

      <AddIngredientModal
        isOpen={showAddIngredient}
        onClose={() => setShowAddIngredient(false)}
        onAdd={handleAddIngredient}
        dishUid={initialData?.uid}
      />

      <EditIngredientModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setEditingIngredient(null);
        }}
        onSave={handleUpdateIngredient}
        onDelete={() => {
          if (editingIngredient) {
            handleRemoveIngredient(ingredients.findIndex(i => i.dishIngredientUid === editingIngredient.dishIngredientUid));
          }
          setShowEditModal(false);
          setEditingIngredient(null);
        }}
        dishIngredientUid={editingIngredient?.uid}  // ✅ Truyền UID
        dishUid={initialData?.uid}
      />

      <IngredientDetailModal
        isOpen={showIngredientDetail}
        ingredient={selectedIngredientDetail}
        onClose={() => {
          setShowIngredientDetail(false);
          setSelectedIngredientDetail(null);
        }}
      />
    </>
  );
};