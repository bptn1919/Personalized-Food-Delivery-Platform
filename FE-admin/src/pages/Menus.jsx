import React, { useState, useEffect, useMemo, useCallback } from 'react';
import styled from 'styled-components';
import { MdMenuBook, MdAdd, MdFilterList, MdRefresh } from 'react-icons/md';
import { Loading } from '../components/common/Loading';
import { Button, IconBtn } from '../components/common/Button';
import { Pagination } from '../components/common/Pagination';
import { MenuTable } from '../components/menus/MenuTable';
import { MenuForm } from '../components/menus/MenuForm';
import { MenuFilters } from '../components/menus/MenuFilters';
import { MenuDetailModal } from '../components/menus/MenuDetailModal';
import { AddDishToMenuModal } from '../components/menus/AddDishToMenuModal';
import { DeleteMenuModal } from '../components/menus/DeleteMenuModal';
import { menuService } from '../services/menuService';

// --- Styled Components ---

const Container = styled.div`
  padding: 24px;
  animation: fadeIn 0.3s ease-in-out;
`;

const Header = styled.div`
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 32px; flex-wrap: wrap; gap: 16px;
`;

const TitleSection = styled.div`display: flex; align-items: center; gap: 16px;`;

const TitleIcon = styled.div`
  width: 54px; height: 54px; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: white; font-size: 28px;
  box-shadow: 0 4px 12px rgba(30, 60, 114, 0.2);
`;

const Title = styled.h1`
  font-size: 1.75rem; font-weight: 700; color: #1e293b; margin: 0;
`;

const ActionBar = styled.div`display: flex; align-items: center; gap: 12px;`;

const TableContainer = styled.div`
  background: white; 
  padding: 24px; 
  border-radius: 16px; 
  border: 1px solid #f1f5f9;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
`;

const TableHeader = styled.div`
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;
`;

const TableTitle = styled.h3`
  font-size: 1.1rem; font-weight: 700; color: #1e3c72; margin: 0;
`;

// --- Component Logic ---

const Menus = () => {
  const [menus, setMenus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showAddDishModal, setShowAddDishModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  
  const [selectedMenu, setSelectedMenu] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // Filters State
  const [appliedFilters, setAppliedFilters] = useState({ status: 'all', search: '' });
  const [tempFilters, setTempFilters] = useState({ status: 'all', search: '' });

  const fetchMenus = useCallback(async () => {
    setLoading(true);
    try {
      const response = await menuService.getMyMenus();
      const data = response?.data || response || [];
      setMenus(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('❌ Error fetching menus:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchMenus(); }, [fetchMenus]);

  // --- Computed State: Filtering & Pagination ---
  const { paginatedMenus, totalRows, totalPages } = useMemo(() => {
    const filtered = menus.filter(menu => {
      const matchStatus = appliedFilters.status === 'all' || menu.status === appliedFilters.status;
      const matchSearch = !appliedFilters.search || 
        menu.name.toLowerCase().includes(appliedFilters.search.toLowerCase()) ||
        (menu.description && menu.description.toLowerCase().includes(appliedFilters.search.toLowerCase()));
      return matchStatus && matchSearch;
    });

    const start = (currentPage - 1) * pageSize;
    return {
      paginatedMenus: filtered.slice(start, start + pageSize),
      totalRows: filtered.length,
      totalPages: Math.ceil(filtered.length / pageSize)
    };
  }, [menus, appliedFilters, currentPage]);

  const handleAddDish = async (menuUid, dishUid) => {
    try {
      await menuService.addDishToMenu(menuUid, dishUid);
      setShowAddDishModal(false);
      // Re-trigger the detail view to show updated dish list
      setShowDetailModal(true); 
      fetchMenus(); 
    } catch (error) {
      alert(`Operation failed: ${error.message}`);
    }
  };

  const handleCreateOrUpdate = async (formData) => {
    try {
      const menuData = { ...formData };
      if (selectedMenu) {
        await menuService.updateMenu(selectedMenu.uid, menuData);
      } else {
        await menuService.createMenu(menuData);
      }
      setShowForm(false);
      setSelectedMenu(null);
      fetchMenus();
    } catch (error) {
      alert(`Save failed: ${error.message}`);
    }
  };

  const handleDeleteConfirm = async () => {
    try {
      await menuService.softDeleteMenu(selectedMenu.uid);
      setShowDeleteModal(false);
      setSelectedMenu(null);
      fetchMenus();
    } catch (error) {
      alert(`Delete failed: ${error.message}`);
    }
  };

  if (loading && menus.length === 0) {
    return <Loading fullPage text="Preparing your menus..." />;
  }

  return (
    <Container>
      <Header>
        <TitleSection>
          <TitleIcon><MdMenuBook /></TitleIcon>
          <Title>Menus Management</Title>
        </TitleSection>
        
        <ActionBar>
          <IconBtn $active={showFilters} onClick={() => setShowFilters(!showFilters)}>
            <MdFilterList />
          </IconBtn>
          <Button onClick={() => { setSelectedMenu(null); setShowForm(true); }}>
New
          </Button>
        </ActionBar>
      </Header>

      <MenuFilters 
        show={showFilters}
        filters={tempFilters}
        onFilterChange={(k, v) => setTempFilters(p => ({...p, [k]: v}))}
        onReset={() => {
          const reset = { status: 'all', search: '' };
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


        <MenuTable 
          menus={paginatedMenus}
          onViewDishes={(m) => { setSelectedMenu(m); setShowDetailModal(true); }}
          onEdit={(m) => { setSelectedMenu(m); setShowForm(true); }}
          onDelete={(m) => { setSelectedMenu(m); setShowDeleteModal(true); }}
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

      {/* Modals Section */}
      <MenuForm 
        isOpen={showForm}
        onClose={() => { setShowForm(false); setSelectedMenu(null); }}
        onSubmit={handleCreateOrUpdate}
        initialData={selectedMenu}
      />

      <MenuDetailModal
        isOpen={showDetailModal}
        menu={selectedMenu}
        onClose={() => { setShowDetailModal(false); setSelectedMenu(null); }}
        onAddDish={() => {
          setShowDetailModal(false);
          setShowAddDishModal(true);
        }}
      />

      <AddDishToMenuModal
        isOpen={showAddDishModal}
        menu={selectedMenu}
        onClose={() => {
          setShowAddDishModal(false);
          setShowDetailModal(true); // Return to detail view
        }}
        onAdd={handleAddDish}
      />

    <DeleteMenuModal 
      isOpen={showDeleteModal}
      onClose={() => {
        setShowDeleteModal(false);
        setSelectedMenu(null);
      }}
      onConfirm={handleDeleteConfirm}
      menu={selectedMenu}
    />
    </Container>
  );
};

export default Menus;