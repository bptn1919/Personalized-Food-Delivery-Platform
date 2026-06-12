import React, { useState, useEffect, useMemo } from 'react';
import styled from 'styled-components';
import { MdRestaurantMenu, MdAdd, MdFilterList, MdRefresh, MdList } from 'react-icons/md';
import { Loading } from '../components/common/Loading';
import { Button, IconBtn } from '../components/common/Button';
import { Pagination } from '../components/common/Pagination';
import { DishTable } from '../components/dishes/DishTable';
import { DishForm } from '../components/dishes/DishForm';
import { DishFilters } from '../components/dishes/DishFilters';
import { DishDetailModal } from '../components/dishes/DishDetailModal';
import { DeleteDishModal } from '../components/dishes/DishDeleteModal';
import { ChefSuggestionsModal } from '../components/dishes/ChefSuggestionsModal';
import { dishService } from '../services/dishService';
import { attachmentService } from '../services/attachmentService';
import { ingredientService } from '../services/ingredientService';

const Container = styled.div`
  padding: 24px;
  animation: fadeIn 0.3s ease-in-out;
`;

const Header = styled.div`
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 24px; flex-wrap: wrap; gap: 16px;
`;

const TitleSection = styled.div`
  display: flex; align-items: center; gap: 16px;
`;

const TitleIcon = styled.div`
  width: 54px; height: 54px; background: #1e3c72;
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  color: white; font-size: 28px;
  box-shadow: 0 4px 12px rgba(30, 60, 114, 0.2);
`;

const Title = styled.h1`
  font-size: 1.75rem; font-weight: 700; color: #1e293b; margin: 0;
`;

const ActionBar = styled.div`
  display: flex; align-items: center; gap: 12px;
`;

const TableContainer = styled.div`
  background: white; 
  padding: 24px; 
  border-radius: 16px;
  border: 1px solid #f1f5f9; 
  margin-top: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
`;

const TableHeader = styled.div`
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;
`;

const TableTitle = styled.h3`
  font-size: 1.1rem; font-weight: 700; color: #1e3c72; margin: 0;
`;

const Dishes = () => {
  const [dishes, setDishes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedDish, setSelectedDish] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDishReferenced, setIsDishReferenced] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [showSuggestionsModal, setShowSuggestionsModal] = useState(false);

  const [appliedFilters, setAppliedFilters] = useState({
    category: 'all', status: 'all', search: ''
  });
  const [tempFilters, setTempFilters] = useState({
    category: 'all', status: 'all', search: ''
  });

  const pageSize = 10;

  const fetchDishes = async () => {
    setLoading(true);
    try {
      const response = await dishService.getMyDishes(); 
      if (response?.data?.content) {
        setDishes(response.data.content);
      }
    } catch (error) {
      console.error('Fetch Error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDishes();
  }, []);

  const { paginatedDishes, totalRows, totalPages } = useMemo(() => {
    let filtered = dishes.filter(dish => {
      const matchCategory = appliedFilters.category === 'all' || dish.category === appliedFilters.category;
      const matchStatus = appliedFilters.status === 'all' || dish.status === appliedFilters.status;
      const matchSearch = !appliedFilters.search || 
        dish.name.toLowerCase().includes(appliedFilters.search.toLowerCase()) ||
        (dish.description && dish.description.toLowerCase().includes(appliedFilters.search.toLowerCase()));
      
      return matchCategory && matchStatus && matchSearch;
    });

    const start = (currentPage - 1) * pageSize;
    return {
      paginatedDishes: filtered.slice(start, start + pageSize),
      totalRows: filtered.length,
      totalPages: Math.ceil(filtered.length / pageSize)
    };
  }, [dishes, appliedFilters, currentPage]);

  const handleCreateDish = async (formData) => {
    try {
      let attachmentUid = formData.image ? 
        await attachmentService.uploadDishImage(formData.image) : null;
      
      const dishData = {
        name: formData.name,
        category: formData.category,
        description: formData.description,
        price: parseFloat(formData.price),
        status: formData.status,
        attachment_uid: attachmentUid,
        location_id: formData.location_id || null
      };

      const dish = await dishService.createDish(dishData);
      
      if (formData.ingredients && formData.ingredients.length > 0) {
        for (const ingredient of formData.ingredients) {
          await ingredientService.addIngredientToDish(dish.uid, {
            ingredient_uid: ingredient.ingredient_uid,
            weight: ingredient.weight
          });
        }
      }
      
      setShowForm(false);
      fetchDishes();
    } catch (error) {
      alert(`Create failed: ${error.message}`);
    }
  };

  const handleUpdateDish = async (formData) => {
    try {
      let attachmentUid = selectedDish.attachment_uid;
      
      if (formData.image) {
        attachmentUid = await attachmentService.uploadDishImage(formData.image);
      }
      
      const dishData = {
        name: formData.name,
        category: formData.category,
        description: formData.description,
        price: parseFloat(formData.price),
        status: formData.status,
        attachment_uid: attachmentUid,
        location_id: formData.location_id || null
      };

      await dishService.updateDish(selectedDish.uid, dishData);
      
      setShowForm(false);
      setSelectedDish(null);
      fetchDishes();
    } catch (error) {
      alert(`Update failed: ${error.message}`);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!selectedDish?.uid) {
      alert('Cannot delete: Missing dish ID');
      return;
    }
    
    try {
      const result = await dishService.softDeleteDish(selectedDish.uid);
      
      if (result?.message_code === 'DISH_IS_REFERENCED') {
        setIsDishReferenced(true);
        return;
      }
      
      setShowDeleteModal(false);
      setSelectedDish(null);
      setIsDishReferenced(false);
      fetchDishes();
    } catch (error) {
      if (error.response?.data?.message_code === 'DISH_IS_REFERENCED') {
        setIsDishReferenced(true);
      } else {
        const errorMessage = error.response?.data?.message || error.message;
        alert(`Delete failed: ${errorMessage}`);
      }
    }
  };

  const handleHideDish = async () => {
    try {
      await dishService.updateDish(selectedDish.uid, { status: 'INACTIVE' });
      setShowDeleteModal(false);
      setSelectedDish(null);
      setIsDishReferenced(false);
      fetchDishes();
      alert(`"${selectedDish.name}" has been hidden from the menu`);
    } catch (error) {
      alert(`Failed to hide dish: ${error.message}`);
    }
  };

  const handleDeleteClick = (dish) => {
    setSelectedDish(dish);
    setIsDishReferenced(false);
    setShowDeleteModal(true);
  };

  if (loading && dishes.length === 0) {
    return <Loading fullPage text="Retrieving menu items..." />;
  }

  return (
    <Container>
      <Header>
        <TitleSection>
          <TitleIcon><MdRestaurantMenu /></TitleIcon>
          <Title>Dish Management</Title>
        </TitleSection>
        
        <ActionBar>
          <IconBtn onClick={() => setShowSuggestionsModal(true)} title="My Suggestions">
            <MdList />
          </IconBtn>
          <IconBtn $active={showFilters} onClick={() => setShowFilters(!showFilters)} title="Filters">
            <MdFilterList />
          </IconBtn>
          <Button onClick={() => { setSelectedDish(null); setShowForm(true); }}>
New
          </Button>
        </ActionBar>
      </Header>

      <DishFilters 
        show={showFilters}
        filters={tempFilters}
        onFilterChange={(k, v) => setTempFilters(p => ({...p, [k]: v}))}
        onReset={() => {
          const reset = { category: 'all', status: 'all', search: '' };
          setTempFilters(reset);
          setAppliedFilters(reset);
          setCurrentPage(1);
        }}
        onApply={() => {
          setAppliedFilters(tempFilters);
          setCurrentPage(1);
          setShowFilters(false);
        }}
        onClose={() => setShowFilters(false)}
      />

      <TableContainer>
        <DishTable 
          dishes={paginatedDishes}
          onView={(d) => { setSelectedDish(d); setShowDetailModal(true); }}
          onEdit={(d) => { setSelectedDish(d); setShowForm(true); }}
          onDelete={handleDeleteClick}
        />

        {totalPages > 1 && (
          <Pagination 
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
            totalItems={totalRows}
            pageSize={pageSize}
          />
        )}
      </TableContainer>

      <DishForm 
        isOpen={showForm}
        onClose={() => { setShowForm(false); setSelectedDish(null); }}
        onSubmit={selectedDish ? handleUpdateDish : handleCreateDish}
        initialData={selectedDish}
      />

      <DishDetailModal
        isOpen={showDetailModal}
        dish={selectedDish}
        onClose={() => { setShowDetailModal(false); setSelectedDish(null); }}
      />

      <DeleteDishModal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setSelectedDish(null);
          setIsDishReferenced(false);
        }}
        onConfirm={handleDeleteConfirm}
        onHide={handleHideDish}
        dish={selectedDish}
        isReferenced={isDishReferenced}
      />

      <ChefSuggestionsModal
        isOpen={showSuggestionsModal}
        onClose={() => setShowSuggestionsModal(false)}
      />
    </Container>
  );
};

export default Dishes;