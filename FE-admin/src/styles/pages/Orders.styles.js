import styled from 'styled-components';

export const Container = styled.div`
  padding: 24px;
`;

export const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
`;

export const TitleSection = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

export const TitleIcon = styled.div`
  width: 48px;
  height: 48px;
  background: linear-gradient(45deg, #1e3c72 0%, #2a5298 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
`;

export const Title = styled.h1`
  font-size: 2rem;
  font-weight: 600;
  color: #1e3c72;
  margin: 0;
`;

export const ActionBar = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
`;

export const SearchInput = styled.div`
  display: flex;
  align-items: center;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 8px 16px;
  width: 300px;

  svg {
    color: #666;
    margin-right: 8px;
    font-size: 1.2rem;
  }

  input {
    border: none;
    outline: none;
    width: 100%;
    font-size: 0.95rem;

    &::placeholder {
      color: #999;
    }
  }
`;

export const FilterButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  color: #555;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #f5f5f5;
    border-color: #999;
  }
`;

export const ExportButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: white;
  border: 1px solid #1e3c72;
  border-radius: 8px;
  color: #1e3c72;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #1e3c72;
    color: white;
  }

  svg {
    font-size: 1.1rem;
  }
`;

export const IconButton = styled.button`
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  background: white;
  color: #555;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #f5f5f5;
    border-color: #999;
  }

  svg {
    font-size: 1.2rem;
  }
`;

export const RefreshButton = styled(IconButton)`
  &:hover {
    color: #1e3c72;
    border-color: #1e3c72;
  }
`;

export const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;

  @media (max-width: 1200px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

export const StatCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  }
`;

export const StatHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
`;

export const StatTitle = styled.div`
  color: #666;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

export const StatIcon = styled.div`
  width: 40px;
  height: 40px;
  background: ${({ color }) => color || '#f5f5f5'};
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
`;

export const StatValue = styled.div`
  font-size: 1.8rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
`;

export const StatSub = styled.div`
  font-size: 0.85rem;
  color: #666;
`;

export const StatChange = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85rem;
  color: ${({ positive }) => positive ? '#2e7d32' : '#c62828'};
`;

export const FilterPanel = styled.div`
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  animation: slideDown 0.3s ease;

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

export const FilterRow = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
`;

export const FilterItem = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;

  label {
    font-size: 0.85rem;
    color: #666;
    font-weight: 500;
  }

  input, select {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 0.95rem;

    &:focus {
      outline: none;
      border-color: #1e3c72;
    }
  }
`;

export const FilterActions = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid #e0e0e0;
  padding-top: 16px;
`;

export const ApplyButton = styled.button`
  padding: 8px 16px;
  background: linear-gradient(45deg, #1e3c72 0%, #2a5298 100%);
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;

  &:hover {
    opacity: 0.9;
  }
`;

export const ResetButton = styled.button`
  padding: 8px 16px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  color: #666;
  font-size: 0.9rem;
  cursor: pointer;

  &:hover {
    background: #f5f5f5;
  }
`;

export const StatusTabs = styled.div`
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
`;

export const StatusTab = styled.button`
  padding: 8px 16px;
  border: none;
  border-radius: 20px;
  background: ${({ active }) => active ? '#1e3c72' : 'white'};
  color: ${({ active }) => active ? 'white' : '#555'};
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid ${({ active }) => active ? '#1e3c72' : '#ddd'};
  transition: all 0.2s ease;

  &:hover {
    background: ${({ active }) => active ? '#1e3c72' : '#f5f5f5'};
  }
`;

export const TableContainer = styled.div`
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow-x: auto;
`;

export const TableHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
`;

export const TableTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 500;
  color: #1e3c72;
  margin: 0;
`;

export const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
`;

export const Th = styled.th`
  text-align: left;
  padding: 12px;
  background: #f5f5f5;
  color: #1e3c72;
  font-weight: 500;
  font-size: 0.9rem;
  white-space: nowrap;
  cursor: ${({ sortable }) => sortable ? 'pointer' : 'default'};

  &:hover {
    background: ${({ sortable }) => sortable ? '#e8e8e8' : '#f5f5f5'};
  }

  svg {
    margin-left: 4px;
    font-size: 0.9rem;
    vertical-align: middle;
  }
`;

export const Td = styled.td`
  padding: 12px;
  border-bottom: 1px solid #e0e0e0;
  color: #333;
  vertical-align: middle;
`;

export const OrderInfo = styled.div`
  display: flex;
  flex-direction: column;
`;

export const OrderId = styled.div`
  font-weight: 600;
  color: #1e3c72;
`;

export const CustomerInfo = styled.div`
  display: flex;
  flex-direction: column;
`;

export const CustomerName = styled.div`
  font-weight: 500;
  color: #333;
`;

export const CustomerPhone = styled.div`
  font-size: 0.8rem;
  color: #666;
`;

export const ChefInfo = styled.div`
  display: flex;
  flex-direction: column;
`;

export const ChefName = styled.div`
  font-weight: 500;
  color: #333;
`;

export const ChefAddress = styled.div`
  font-size: 0.8rem;
  color: #666;
`;

export const StatusBadge = styled.span`
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  text-align: center;
  min-width: 80px;
  
  ${({ status }) => {
    switch(status) {
      case 'pending':
        return `
          background: #fff3e0;
          color: #ed6c02;
        `;
      case 'confirmed':
        return `
          background: #e3f2fd;
          color: #1976d2;
        `;
      case 'preparing':
        return `
          background: #e8eaf6;
          color: #3f51b5;
        `;
      case 'shipping':
        return `
          background: #f3e5f5;
          color: #9c27b0;
        `;
      case 'completed':
        return `
          background: #e8f5e8;
          color: #2e7d32;
        `;
      case 'cancelled':
        return `
          background: #ffebee;
          color: #c62828;
        `;
      case 'refunded':
        return `
          background: #e0e0e0;
          color: #666;
        `;
      default:
        return `
          background: #f5f5f5;
          color: #666;
        `;
    }
  }}
`;

export const PaymentBadge = styled.span`
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  background: ${({ method }) => 
    method === 'cod' ? '#fff3e0' : 
    method === 'banking' ? '#e3f2fd' : 
    '#e8f5e8'};
  color: ${({ method }) => 
    method === 'cod' ? '#ed6c02' : 
    method === 'banking' ? '#1976d2' : 
    '#2e7d32'};
`;

export const ActionGroup = styled.div`
  display: flex;
  gap: 4px;
`;

export const ActionButton = styled.button`
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #f0f0f0;
    color: #1e3c72;
  }

  ${({ danger }) => danger && `
    &:hover {
      background: #ffebee;
      color: #c62828;
    }
  `}

  ${({ success }) => success && `
    &:hover {
      background: #e8f5e8;
      color: #2e7d32;
    }
  `}
`;

export const Pagination = styled.div`
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
`;

export const PaginationInfo = styled.div`
  color: #666;
  font-size: 0.9rem;
`;

export const PaginationButtons = styled.div`
  display: flex;
  gap: 4px;
`;

export const PageButton = styled.button`
  width: 36px;
  height: 36px;
  border: 1px solid ${({ active }) => active ? '#1e3c72' : '#ddd'};
  border-radius: 6px;
  background: ${({ active }) => active ? '#1e3c72' : 'white'};
  color: ${({ active }) => active ? 'white' : '#666'};
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: ${({ active }) => active ? '#1e3c72' : '#f5f5f5'};
    border-color: #1e3c72;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

// Modal styles
export const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
`;

export const Modal = styled.div`
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  overflow-y: auto;
  animation: slideUp 0.3s ease;

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

export const ModalHeader = styled.div`
  padding: 20px 24px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  background: white;
  z-index: 10;

  h2 {
    margin: 0;
    font-size: 1.5rem;
    color: #1e3c72;
  }
`;

export const CloseButton = styled.button`
  background: transparent;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  border-radius: 50%;

  &:hover {
    background: #f5f5f5;
    color: #333;
  }
`;

export const ModalContent = styled.div`
  padding: 24px;
`;

export const ModalFooter = styled.div`
  padding: 16px 24px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  position: sticky;
  bottom: 0;
  background: white;
`;

export const CancelButton = styled.button`
  padding: 8px 16px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  color: #666;
  font-size: 0.9rem;
  cursor: pointer;

  &:hover {
    background: #f5f5f5;
  }
`;

export const ConfirmButton = styled.button`
  padding: 8px 16px;
  background: ${({ danger }) => danger ? '#c62828' : 'linear-gradient(45deg, #1e3c72 0%, #2a5298 100%)'};
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;

  &:hover {
    opacity: 0.9;
  }
`;

// Order Detail styles
export const OrderDetailGrid = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

export const DetailSection = styled.div`
  background: #f9f9f9;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
`;

export const SectionTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 500;
  color: #1e3c72;
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

export const InfoRow = styled.div`
  display: flex;
  margin-bottom: 12px;
`;

export const InfoLabel = styled.div`
  width: 120px;
  color: #666;
  font-size: 0.9rem;
`;

export const InfoValue = styled.div`
  flex: 1;
  color: #333;
  font-weight: 500;
`;

export const Timeline = styled.div`
  position: relative;
  padding-left: 20px;
  
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #e0e0e0;
  }
`;

export const TimelineItem = styled.div`
  position: relative;
  padding-bottom: 20px;
  
  &::before {
    content: '';
    position: absolute;
    left: -24px;
    top: 4px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: ${({ active }) => active ? '#1e3c72' : '#e0e0e0'};
    border: 2px solid ${({ active }) => active ? '#1e3c72' : 'transparent'};
  }

  &:last-child {
    padding-bottom: 0;
  }
`;

export const TimelineTime = styled.div`
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 4px;
`;

export const TimelineStatus = styled.div`
  font-weight: 500;
  color: #333;
`;

export const TimelineNote = styled.div`
  font-size: 0.85rem;
  color: #999;
`;

export const ItemsTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 16px;

  th {
    text-align: left;
    padding: 8px;
    background: #f0f0f0;
    color: #666;
    font-weight: 500;
    font-size: 0.85rem;
  }

  td {
    padding: 8px;
    border-bottom: 1px solid #e0e0e0;
  }
`;

export const TotalRow = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-weight: 500;
  
  &:last-child {
    font-size: 1.2rem;
    color: #1e3c72;
    border-top: 2px solid #e0e0e0;
    margin-top: 8px;
    padding-top: 12px;
  }
`;

export const ShippingInfo = styled.div`
  background: #f0f7ff;
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
`;

export const TrackingStatus = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  color: #1976d2;
  font-weight: 500;
`;

export const PaymentInfo = styled.div`
  background: #f5f5f5;
  border-radius: 8px;
  padding: 16px;
`;

export const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
`;

export const Spinner = styled.div`
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #1e3c72;
  border-radius: 50%;
  animation: spin 1s linear infinite;

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

export const Notification = styled.div`
  position: fixed;
  top: 20px;
  right: 20px;
  background: white;
  border-radius: 8px;
  padding: 12px 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 2000;
  animation: slideIn 0.3s ease;

  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  ${({ type }) => {
    switch(type) {
      case 'success':
        return `border-left: 4px solid #2e7d32;`;
      case 'warning':
        return `border-left: 4px solid #ed6c02;`;
      case 'error':
        return `border-left: 4px solid #c62828;`;
      default:
        return `border-left: 4px solid #1976d2;`;
    }
  }}
`;