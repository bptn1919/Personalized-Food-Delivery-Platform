import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { 
  MdRestaurant, MdAttachMoney, MdDescription, 
  MdCheckCircle, MdCalendarToday, MdAdd,
  MdInfo, MdImage, MdLocationOn
} from 'react-icons/md';
import { Modal } from '../common/Modal';
import { StatusBadge } from '../common/StatusBadge';
import { Loading } from '../common/Loading';
import { dishService } from '../../services/dishService';
import { dishLocationService } from '../../services/dishLocationService';
import { DISH_CATEGORY_LABELS, DISH_STATUS_LABELS } from '../../utils/constants';
import { formatCurrency, formatDate } from '../../utils/helpers';

const ModalContent = styled.div`
  padding: 10px 0;
  max-height: 75vh;
  overflow-y: auto;
  
  /* Custom Scrollbar */
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: #e2e8f0;
    border-radius: 10px;
  }
`;

const Section = styled.div`
  margin-bottom: 24px;
  padding: 20px;
  background: white;
  border: 1px solid #f1f5f9;
  border-radius: 16px;
`;

const SectionTitle = styled.h4`
  display: flex;
  align-items: center;
  gap: 10px;
  color: #1e293b;
  margin: 0 0 20px 0;
  font-size: 1rem;
  font-weight: 700;

  svg {
    color: #1e3c72;
    font-size: 1.2rem;
  }
`;

const ImageWrapper = styled.div`
  display: flex;
  justify-content: center;
  background: #f8fafc;
  padding: 24px;
  border-radius: 12px;
  border: 1px dashed #cbd5e1;
`;

const DishImage = styled.img`
  max-width: 100%;
  max-height: 320px;
  object-fit: cover;
  border-radius: 12px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
`;

const ImagePlaceholder = styled.div`
  padding: 60px;
  color: #94a3b8;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
`;

const InfoGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
`;

const InfoBox = styled.div`
  .label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
    font-weight: 700;
    margin-bottom: 6px;
  }
  .value {
    font-size: 1rem;
    font-weight: 500;
    color: #1e293b;
  }
`;

const ScheduleTable = styled.table`
  width: 100%;
  border-collapse: separate;
  border-spacing: 0 8px;
  
  th {
    text-align: left;
    padding: 8px 12px;
    color: #64748b;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
  }
  
  td {
    padding: 12px;
    background: #f8fafc;
    font-size: 0.9rem;
    color: #334155;

    &:first-child { border-radius: 8px 0 0 8px; font-weight: 600; }
    &:last-child { border-radius: 0 8px 8px 0; }
  }
`;

const AddScheduleBox = styled.div`
  margin-top: 20px;
  padding: 20px;
  background: #f1f5f9;
  border-radius: 12px;
  display: flex;
  gap: 16px;
  align-items: flex-end;

  @media (max-width: 640px) {
    flex-direction: column;
    align-items: stretch;
  }
`;

const InputGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: ${({ $flex }) => $flex || '1'};
  
  label {
    font-size: 0.75rem;
    font-weight: 700;
    color: #475569;
  }
  
  input {
    padding: 10px 14px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    font-size: 0.9rem;
    transition: all 0.2s;
    
    &:focus {
      outline: none;
      border-color: #1e3c72;
      box-shadow: 0 0 0 3px rgba(30, 60, 114, 0.1);
    }
  }
`;

const PrimaryAction = styled.button`
  padding: 10px 20px;
  background: #1e3c72;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 41px;
  transition: opacity 0.2s;
  
  &:hover:not(:disabled) { background: #0f172a; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
`;

export const DishDetailModal = ({ isOpen, dish, onClose }) => {
  const [availabilities, setAvailabilities] = useState([]);
  const [loadingAvailabilities, setLoadingAvailabilities] = useState(false);
  const [locationData, setLocationData] = useState(null);
  const [newAvailability, setNewAvailability] = useState({
    available_date: '',
    available_quantity: 0,
    note: ''
  });
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    if (isOpen && dish?.uid) {
      fetchAvailabilities();
      fetchLocationData();
    }
  }, [isOpen, dish]);

  const fetchLocationData = async () => {
    if (!dish?.location_id) return;
    try {
      const data = await dishLocationService.getById(dish.location_id);
      setLocationData(data?.data || data);
    } catch (error) {
      console.error('Fetch location error:', error);
    }
  };

  const fetchAvailabilities = async () => {
    if (!dish?.uid) return;
    setLoadingAvailabilities(true);
    try {
      const response = await dishService.getAvailabilities(dish.uid);
      const list = response?.data?.availabilities || response?.availabilities || response || [];
      setAvailabilities(Array.isArray(list) ? list : []);
    } catch (error) {
      console.error('Fetch error:', error);
    } finally {
      setLoadingAvailabilities(false);
    }
  };

  const handleAddAvailability = async () => {
    if (!newAvailability.available_date) return alert('Date is required');
    setAdding(true);
    try {
      await dishService.createAvailability(dish.uid, {
        ...newAvailability,
        available_quantity: parseInt(newAvailability.available_quantity) || 0,
        is_available: true
      });
      setNewAvailability({ available_date: '', available_quantity: 0, note: '' });
      await fetchAvailabilities();
    } catch (error) {
      alert('Failed to update schedule');
    } finally {
      setAdding(false);
    }
  };

  if (!dish) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Product Specification" size="large">
      <ModalContent>
        {/* Media Preview */}
        <Section>
          <SectionTitle><MdImage /> Culinary Presentation</SectionTitle>
          <ImageWrapper>
            {dish.public_url ? (
              <DishImage src={dish.public_url} alt={dish.name} />
            ) : (
              <ImagePlaceholder>
                <MdRestaurant size={48} />
                <span>No high-resolution image available</span>
              </ImagePlaceholder>
            )}
          </ImageWrapper>
        </Section>

        {/* Core Details */}
        <Section>
          <SectionTitle><MdInfo /> General Information</SectionTitle>
          <InfoGrid>
            <InfoBox>
              <div className="label">Dish Identity</div>
              <div className="value">{dish.name}</div>
            </InfoBox>
            <InfoBox>
              <div className="label">Classification</div>
              <div className="value">{DISH_CATEGORY_LABELS[dish.category] || dish.category}</div>
            </InfoBox>
            <InfoBox>
              <div className="label">Unit Price</div>
              <div className="value">{formatCurrency(dish.price)}</div>
            </InfoBox>
            <InfoBox>
              <div className="label">Location</div>
              <div className="value" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <MdLocationOn size={16} />
                {locationData?.name || dish.location_id || '—'}
              </div>
            </InfoBox>
            <InfoBox>
              <div className="label">Market Status</div>
              <div className="value">
                <StatusBadge status={dish.status === 'AVAILABLE' ? 'success' : 'error'}>
                  {DISH_STATUS_LABELS[dish.status] || dish.status}
                </StatusBadge>
              </div>
            </InfoBox>
          </InfoGrid>
        </Section>

        {/* Description & Social */}
        <Section>
          <SectionTitle><MdDescription /> Chef's Description</SectionTitle>
          <p style={{ color: '#475569', lineHeight: '1.6', margin: 0 }}>
            {dish.description || 'No description provided for this item.'}
          </p>
          {dish.avg_rating !== undefined && (
            <div style={{ marginTop: '16px', fontWeight: '700', color: '#1e293b' }}>
              Customer Feedback: ⭐ {dish.avg_rating.toFixed(1)} / 5.0
            </div>
          )}
        </Section>

        {/* Availability Inventory */}
        <Section>
          <SectionTitle><MdCalendarToday /> Inventory Schedule</SectionTitle>
          {loadingAvailabilities ? (
            <Loading text="Syncing schedule..." />
          ) : availabilities.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '30px', color: '#94a3b8', background: '#f8fafc', borderRadius: '8px' }}>
              No active availability windows defined.
            </div>
          ) : (
            <ScheduleTable>
              <thead>
                <tr>
                  <th>Available Date</th>
                  <th>Quantity</th>
                  <th>Internal Note</th>
                </tr>
              </thead>
              <tbody>
                {availabilities.map((avail, i) => (
                  <tr key={i}>
                    <td>{formatDate(avail.available_date)}</td>
                    <td>{avail.available_quantity} Units</td>
                    <td>{avail.note || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </ScheduleTable>
          )}

          <AddScheduleBox>
            <InputGroup>
              <label>Service Date</label>
              <input
                type="date"
                value={newAvailability.available_date}
                min={new Date().toISOString().split('T')[0]}
                onChange={(e) => setNewAvailability({ ...newAvailability, available_date: e.target.value })}
              />
            </InputGroup>
            <InputGroup $flex="0.5">
              <label>Stock</label>
              <input
                type="number"
                placeholder="0"
                value={newAvailability.available_quantity}
                onChange={(e) => setNewAvailability({ ...newAvailability, available_quantity: e.target.value })}
              />
            </InputGroup>
            <InputGroup $flex="2">
              <label>Administrative Note</label>
              <input
                type="text"
                placeholder="e.g. Special Holiday Batch"
                value={newAvailability.note}
                onChange={(e) => setNewAvailability({ ...newAvailability, note: e.target.value })}
              />
            </InputGroup>
            <PrimaryAction onClick={handleAddAvailability} disabled={adding}>
              <MdAdd size={18} /> {adding ? 'Syncing...' : 'Add Slot'}
            </PrimaryAction>
          </AddScheduleBox>
        </Section>
      </ModalContent>
    </Modal>
  );
};