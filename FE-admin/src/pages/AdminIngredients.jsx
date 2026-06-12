import React, { useState, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import { 
  MdLocalDining, MdFilterList, MdAdd, MdDownload, MdUpload, MdPendingActions, MdDeleteSweep
} from 'react-icons/md';
import { Loading } from '../components/common/Loading';
import { Button, IconBtn } from '../components/common/Button';
import { Pagination } from '../components/common/Pagination';
import { IngredientStats } from '../components/ingredients/IngredientStats';
import { IngredientFilters } from '../components/ingredients/IngredientFilters';
import { IngredientTable } from '../components/ingredients/IngredientTable';
import { IngredientForm } from '../components/ingredients/IngredientForm';
import { IngredientDetailModal } from '../components/ingredients/IngredientDetailModal';
import { DeleteIngredientModal } from '../components/ingredients/DeleteIngredientModal';
import { AliasesPanel } from '../components/ingredients/AliasesPanel';
import { SuggestionModal } from '../components/ingredients/SuggestionModal';
import { ImportResultModal } from '../components/ingredients/ImportResultModal';
import { ingredientService } from '../services/ingredientService';

// --- Constants & Enums ---

const CATEGORIES = [
  { value: 'all', label: 'All Categories' },
  { value: 'GRAIN', label: 'Grain' },
  { value: 'PROTEIN', label: 'Protein' },
  { value: 'VEGETABLE', label: 'Vegetable' },
  { value: 'FRUIT', label: 'Fruit' },
  { value: 'OILFATBUTTER', label: 'Oil/Fat/Butter' },
  { value: 'SPICE', label: 'Spice' },
  { value: 'MILK', label: 'Milk' }
];

// --- Styled Components ---

const Container = styled.div`
  padding: 24px;
  animation: fadeIn 0.3s ease-in-out;
`;

const Header = styled.div`
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 32px; flex-wrap: wrap; gap: 16px;
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
  flex-wrap: wrap;
`;

const TableContainer = styled.div`
  background: white; 
  padding: 24px; 
  border-radius: 16px;
  border: 1px solid #f1f5f9; 
  margin-top: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
`;

const TableHeader = styled.div`
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;
`;

const TableTitle = styled.h3`
  font-size: 1.1rem; font-weight: 700; color: #1e3c72; margin: 0;
`;

const FileInput = styled.input`
  display: none;
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

const SuggestionBadge = styled.button`
  background: #fef3c7;
  color: #92400e;
  border: none;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  
  &:hover {
    background: #fde68a;
  }
`;

// --- Component Logic ---

const AdminIngredients = () => {
  const [activeTab, setActiveTab] = useState('ingredients');
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedIngredient, setSelectedIngredient] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRows, setTotalRows] = useState(0);
  const [showSuggestionModal, setShowSuggestionModal] = useState(false);
  const [suggestionType, setSuggestionType] = useState('ingredient');
  const [showDeleted, setShowDeleted] = useState(false);
  const [showImportResultModal, setShowImportResultModal] = useState(false);
  const [importResult, setImportResult] = useState(null);
  
  const [appliedFilters, setAppliedFilters] = useState({
    search: '', categories: 'all', min_energy: '', max_energy: ''
  });
  const [tempFilters, setTempFilters] = useState({ ...appliedFilters });

  const [ingredientStats, setIngredientStats] = useState({
    total: 0, grain: 0, protein: 0, vegetable: 0, fruit: 0, oilFatButter: 0, spice: 0, milk: 0
  });

  const pageSize = 10;

  const fetchIngredients = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page: currentPage, page_size: pageSize };
      
      // Thêm tham số để lấy cả ingredient đã xóa
      if (showDeleted) {
        params.include_deleted = true;
      }

      if (appliedFilters.search) params.search = appliedFilters.search;
      if (appliedFilters.categories !== 'all') params.categories = appliedFilters.categories;
      if (appliedFilters.min_energy) params.min_energy = appliedFilters.min_energy;
      if (appliedFilters.max_energy) params.max_energy = appliedFilters.max_energy;

      const response = await ingredientService.getAllIngredients(params);

      if (response) {
        setIngredients(response.content || []);
        setTotalRows(response.total_rows || 0);
        setTotalPages(response.total_pages || 1);
        
        const content = response.content || [];
        setIngredientStats({
          total: response.total_rows || 0,
          grain: content.filter(i => i.category === 'GRAIN').length,
          protein: content.filter(i => i.category === 'PROTEIN').length,
          vegetable: content.filter(i => i.category === 'VEGETABLE').length,
          fruit: content.filter(i => i.category === 'FRUIT').length,
          oilFatButter: content.filter(i => i.category === 'OILFATBUTTER').length,
          spice: content.filter(i => i.category === 'SPICE').length,
          milk: content.filter(i => i.category === 'MILK').length
        });
      }
    } catch (error) {
      console.error('Error fetching ingredients:', error);
    } finally {
      setLoading(false);
    }
  }, [currentPage, appliedFilters, showDeleted]);

  useEffect(() => {
    fetchIngredients();
  }, [fetchIngredients]);

  const handleCreateIngredient = async (formData) => {
    try {
      setLoading(true);
      await ingredientService.createIngredient(formData);
      setShowForm(false);
      setImportResult({ created_count: 1, failed_count: 0 });
      setShowImportResultModal(true);
      fetchIngredients();
    } catch (error) {
      setImportResult({ created_count: 0, failed_count: 1, errors: [{ message: error.message }] });
      setShowImportResultModal(true);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateIngredient = async (formData) => {
    try {
      setLoading(true);
      await ingredientService.updateIngredient(selectedIngredient.uid, formData);
      setShowForm(false);
      setSelectedIngredient(null);
      setImportResult({ created_count: 1, failed_count: 0 });
      setShowImportResultModal(true);
      fetchIngredients();
    } catch (error) {
      setImportResult({ created_count: 0, failed_count: 1, errors: [{ message: error.message }] });
      setShowImportResultModal(true);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    try {
      await ingredientService.softDeleteIngredient(selectedIngredient.uid);
      setShowDeleteModal(false);
      setSelectedIngredient(null);
      fetchIngredients();
    } catch (error) {
      alert(`Delete failed: ${error.message}`);
    }
  };

  const handleRestoreIngredient = async (item) => {
    try {
      await ingredientService.restoreIngredient(item.uid);
      fetchIngredients();
    } catch (error) {
      alert(`Restore failed: ${error.message}`);
    }
  };

  const handleExportTemplate = async () => {
    try {
      const blob = await ingredientService.exportTemplate();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'ingredient_template.xlsx';
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      alert(`Export failed: ${error.message}`);
    }
  };

  const handleImportExcel = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
      setLoading(true);
      const result = await ingredientService.importIngredients(file);
      setImportResult(result);
      setShowImportResultModal(true);
      fetchIngredients();
    } catch (error) {
      alert(`Import failed: ${error.message}`);
    } finally {
      setLoading(false);
      event.target.value = ''; // Reset input
    }
  };

  if (loading && ingredients.length === 0) {
    return <Loading fullPage text="Loading ingredient database..." />;
  }

  return (
    <Container>
      <Header>
        <TitleSection>
          <TitleIcon><MdLocalDining /></TitleIcon>
          <div>
            <Title>Ingredient Management</Title>
          </div>
        </TitleSection>
        
        <ActionBar>
          <Button onClick={() => { setSelectedIngredient(null); setShowForm(true); }}>
   New
          </Button>
          <Button $variant="secondary" onClick={handleExportTemplate}>
            <MdDownload /> Export Template
          </Button>
          <label>
            <FileInput type="file" accept=".xlsx, .xls" onChange={handleImportExcel} />
            <Button as="span" $variant="secondary">
              <MdUpload /> Import Excel
            </Button>
          </label>
          <IconBtn $active={showFilters} onClick={() => setShowFilters(!showFilters)} title="Filters">
            <MdFilterList />
          </IconBtn>
        </ActionBar>
      </Header>

      <IngredientStats stats={ingredientStats} />

      <TabsContainer>
        <Tab $active={activeTab === 'ingredients'} onClick={() => setActiveTab('ingredients')}>
          Ingredients
        </Tab>
        <Tab $active={activeTab === 'aliases'} onClick={() => setActiveTab('aliases')}>
          Aliases
        </Tab>
      </TabsContainer>

      {activeTab === 'ingredients' ? (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <SuggestionBadge onClick={() => {
              setSuggestionType('ingredient');
              setShowSuggestionModal(true);
            }}>
              <MdPendingActions /> Pending Ingredient Suggestions
            </SuggestionBadge>
          </div>
          
          <IngredientFilters 
            show={showFilters}
            filters={tempFilters}
            categories={CATEGORIES}
            onFilterChange={(k, v) => setTempFilters(p => ({...p, [k]: v}))}
            onReset={() => {
              const reset = { search: '', categories: 'all', min_energy: '', max_energy: '' };
              setTempFilters(reset);
              setAppliedFilters(reset);
              setCurrentPage(1);
              setShowFilters(false);
            }}
            onApply={() => {
              setAppliedFilters(tempFilters);
              setCurrentPage(1);
              setShowFilters(false);
            }}
            onClose={() => setShowFilters(false)}
          />

          <TableContainer>
            <IngredientTable 
              ingredients={ingredients}
              onView={(item) => { setSelectedIngredient(item); setShowDetailModal(true); }}
              onEdit={(item) => { setSelectedIngredient(item); setShowForm(true); }}
              onDelete={(item) => { setSelectedIngredient(item); setShowDeleteModal(true); }}
              onRestore={handleRestoreIngredient}
              isAdmin={true}
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
        </>
      ) : (
        <AliasesPanel onShowSuggestions={() => {
          setSuggestionType('alias');
          setShowSuggestionModal(true);
        }} />
      )}

      <SuggestionModal
        isOpen={showSuggestionModal}
        onClose={() => setShowSuggestionModal(false)}
        type={suggestionType}
        onApprove={() => {
          if (suggestionType === 'ingredient') {
            fetchIngredients();
          }
          setShowSuggestionModal(false);
        }}
        onReject={() => {
          if (suggestionType === 'ingredient') {
            fetchIngredients();
          }
          setShowSuggestionModal(false);
        }}
      />

      <IngredientForm 
        isOpen={showForm}
        onClose={() => { setShowForm(false); setSelectedIngredient(null); }}
        onSubmit={selectedIngredient ? handleUpdateIngredient : handleCreateIngredient}
        initialData={selectedIngredient}
        isAdmin={true}
      />

      <IngredientDetailModal
        isOpen={showDetailModal}
        ingredient={selectedIngredient}
        onClose={() => { setShowDetailModal(false); setSelectedIngredient(null); }}
      />

      <DeleteIngredientModal 
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setSelectedIngredient(null);
        }}
        onConfirm={handleDeleteConfirm}
        ingredient={selectedIngredient}
      />

      <ImportResultModal
        isOpen={showImportResultModal}
        onClose={() => {
          setShowImportResultModal(false);
          setImportResult(null);
        }}
        result={importResult}
        titleSuccess={importResult?.total_rows > 1 ? "Import Successful" : (selectedIngredient ? "Update Successful" : "Create Successful")}
        titleError={importResult?.total_rows > 1 ? "Import Failed" : (selectedIngredient ? "Update Failed" : "Create Failed")}
      />
    </Container>
  );
};

export default AdminIngredients;