import React, { useState, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import { MdLocationOn, MdAdd, MdRefresh } from 'react-icons/md';
import { Loading } from '../components/common/Loading';
import { Button, IconBtn } from '../components/common/Button';
import { LocationFormModal } from '../components/dishlocations/LocationFormModal';
import { LocationTreeView } from '../components/dishlocations/LocationTreeView';
import { dishLocationService } from '../services/dishLocationService';
import { DeleteDishLocationModal } from '../components/dishlocations/DeleteDishLocationModal';

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
`;

const ContentContainer = styled.div`
  background: white;
  border-radius: 16px;
  border: 1px solid #f1f5f9;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
`;

const InfoMessage = styled.div`
  background: #ecfdf5;
  border-left: 4px solid #10b981;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 0.85rem;
  color: #065f46;
`;

const flattenLocations = (nodes, result = []) => {
  nodes.forEach(node => {
    result.push({ id: node.id, name: node.name, type: node.type, parent_id: node.parent_id });
    if (node.children && node.children.length > 0) {
      flattenLocations(node.children, result);
    }
  });
  return result;
};

const AdminDishLocations = () => {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [allLocationsFlat, setAllLocationsFlat] = useState([]);

  const fetchLocations = useCallback(async () => {
    setLoading(true);
    try {
      const tree = await dishLocationService.getTree();
      setLocations(tree || []);
      
      // Flatten để dùng cho parent selection
      const flat = flattenLocations(tree || []);
      setAllLocationsFlat(flat);
    } catch (error) {
      console.error('Error fetching locations:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLocations();
  }, [fetchLocations]);

  const handleCreate = async (formData) => {
    await dishLocationService.create(formData);
    await fetchLocations();
    setShowForm(false);
  };

  const handleUpdate = async (formData) => {
    await dishLocationService.update(selectedLocation.id, formData);
    await fetchLocations();
    setShowForm(false);
    setSelectedLocation(null);
  };

  const handleDelete = async () => {
    try {
      await dishLocationService.delete(selectedLocation.id);
      await fetchLocations();
      setShowDeleteModal(false);
      setSelectedLocation(null);
    } catch (error) {
      if (error.response?.data?.message_code === 'LOCATION_HAS_CHILDREN') {
        alert('Cannot delete location with child locations. Please delete child locations first.');
      } else {
        alert(`Delete failed: ${error.message}`);
      }
    }
  };

  const handleAddChild = (parent) => {
    setSelectedLocation(null);
    setShowForm(true);
  };

  if (loading) {
    return <Loading fullPage text="Loading locations..." />;
  }

  return (
    <Container>
      <Header>
        <TitleSection>
          <TitleIcon><MdLocationOn /></TitleIcon>
          <Title>Locations Management</Title>
        </TitleSection>
        
        <ActionBar>
          <Button onClick={() => { setSelectedLocation(null); setShowForm(true); }}>
             New
          </Button>
        </ActionBar>
      </Header>

      <ContentContainer>
        
        <LocationTreeView
          locations={locations}
          onEdit={(loc) => {
            setSelectedLocation(loc);
            setShowForm(true);
          }}
          onDelete={(loc) => {
            setSelectedLocation(loc);
            setShowDeleteModal(true);
          }}
          onAddChild={handleAddChild}
        />
      </ContentContainer>

      <LocationFormModal
        isOpen={showForm}
        onClose={() => {
          setShowForm(false);
          setSelectedLocation(null);
        }}
        onSubmit={selectedLocation ? handleUpdate : handleCreate}
        initialData={selectedLocation}
        existingLocations={allLocationsFlat}
      />

      <DeleteDishLocationModal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setSelectedLocation(null);
        }}
        onConfirm={handleDelete}
        location={selectedLocation}
      />
    </Container>
  );
};

export default AdminDishLocations;