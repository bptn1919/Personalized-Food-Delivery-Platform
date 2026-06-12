import styled from 'styled-components';

// Stats Grid cơ bản
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

export const KPIGrid = styled(StatsGrid)`
  grid-template-columns: repeat(5, 1fr);
  
  @media (max-width: 1400px) {
    grid-template-columns: repeat(3, 1fr);
  }
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

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

export const DateRange = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  color: #555;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: #1e3c72;
    box-shadow: 0 2px 8px rgba(30, 60, 114, 0.1);
  }

  svg {
    color: #1e3c72;
  }
`;

export const ExportButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: linear-gradient(45deg, #1e3c72 0%, #2a5298 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(30, 60, 114, 0.3);
  }

  &:active {
    transform: translateY(0);
  }
`;

export const TabBar = styled.div`
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  background: white;
  padding: 4px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  flex-wrap: wrap;
`;

export const Tab = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  background: ${({ active }) => active ? 'linear-gradient(45deg, #1e3c72 0%, #2a5298 100%)' : 'transparent'};
  color: ${({ active }) => active ? 'white' : '#555'};
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: ${({ active }) => active ? 'linear-gradient(45deg, #1e3c72 0%, #2a5298 100%)' : '#f5f5f5'};
  }

  svg {
    font-size: 1.2rem;
  }
`;

export const FilterGroup = styled.div`
  display: flex;
  background: white;
  border-radius: 8px;
  padding: 2px;
  border: 1px solid #e0e0e0;
`;

export const FilterButton = styled.button`
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background: ${({ active }) => active ? '#1e3c72' : 'transparent'};
  color: ${({ active }) => active ? 'white' : '#555'};
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: ${({ active }) => active ? '#1e3c72' : '#f5f5f5'};
  }
`;

export const CompareButton = styled(FilterButton)`
  display: flex;
  align-items: center;
  gap: 4px;
  background: ${({ active }) => active ? '#2e7d32' : 'white'};
  color: ${({ active }) => active ? 'white' : '#555'};
  border: 1px solid ${({ active }) => active ? '#2e7d32' : '#e0e0e0'};

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

export const FiltersPanel = styled.div`
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

export const FiltersRow = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
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

export const SmallButton = styled.button`
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  background: ${({ active }) => active ? '#1e3c72' : 'transparent'};
  color: ${({ active }) => active ? 'white' : '#666'};
  font-size: 0.8rem;
  cursor: pointer;

  &:hover {
    background: ${({ active }) => active ? '#1e3c72' : '#f5f5f5'};
  }
`;

export const SmallGroup = styled.div`
  display: flex;
  gap: 4px;
  background: #f5f5f5;
  padding: 2px;
  border-radius: 6px;
`;

export const ChartGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 24px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

export const DoubleGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

export const ChartCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
`;

export const ChartHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
`;

export const ChartTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 500;
  color: #1e3c72;
  margin: 0;
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
  margin-bottom: 8px;
`;

export const StatChange = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.9rem;
  color: ${({ positive }) => positive ? '#2e7d32' : '#c62828'};
`;

export const TableContainer = styled.div`
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow-x: auto;
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
`;

export const Td = styled.td`
  padding: 12px;
  border-bottom: 1px solid #e0e0e0;
  color: #333;
`;

export const StatusBadge = styled.span`
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  background: ${({ status }) => 
    status === 'completed' ? '#e8f5e8' : 
    status === 'pending' ? '#fff3e0' : 
    '#ffebee'};
  color: ${({ status }) => 
    status === 'completed' ? '#2e7d32' : 
    status === 'pending' ? '#ed6c02' : 
    '#c62828'};
`;

export const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
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

export const COLORS = ['#1e3c72', '#2a5298', '#1976d2', '#42a5f5', '#64b5f6'];

export const TopList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

export const TopListItem = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 8px;
  background: #f9f9f9;
  transition: all 0.2s ease;

  &:hover {
    background: #f0f0f0;
  }
`;

export const TopRank = styled.div`
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: ${({ index }) => 
    index === 0 ? '#FFD700' : 
    index === 1 ? '#C0C0C0' : 
    index === 2 ? '#CD7F32' : '#e0e0e0'};
  color: ${({ index }) => index < 3 ? '#333' : '#666'};
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.85rem;
`;

export const TopInfo = styled.div`
  flex: 1;
`;

export const TopName = styled.div`
  font-weight: 500;
  color: #333;
  margin-bottom: 2px;
`;

export const TopMeta = styled.div`
  display: flex;
  gap: 8px;
  font-size: 0.8rem;
  color: #666;
`;

export const TopGrowth = styled.div`
  font-size: 0.9rem;
  font-weight: 500;
  color: ${({ positive }) => positive ? '#2e7d32' : '#c62828'};
`;

export const ViewAllButton = styled.button`
  background: transparent;
  border: none;
  color: #1e3c72;
  font-size: 0.85rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;

  &:hover {
    background: #f0f7ff;
  }
`;

export const WarningBadge = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #ffebee;
  color: #c62828;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;

  svg {
    font-size: 1rem;
  }
`;

export const ReportList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

export const ReportItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
  border-left: 4px solid #c62828;
`;

export const ReportName = styled.div`
  font-weight: 500;
  color: #333;
`;

export const ReportReason = styled.div`
  font-size: 0.85rem;
  color: #666;
  margin-top: 2px;
`;

export const ReportCount = styled.div`
  padding: 4px 8px;
  background: #ffebee;
  color: #c62828;
  border-radius: 4px;
  font-weight: 500;
  font-size: 0.85rem;
`;

export const ActionButton = styled.button`
  background: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;

  &:hover {
    background: #f0f0f0;
    color: #333;
  }

  svg {
    font-size: 1.2rem;
  }
`;

export const LegendGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-top: 16px;
`;

export const LegendItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #555;
`;

export const LegendColor = styled.div`
  width: 12px;
  height: 12px;
  border-radius: 3px;
  background: ${({ color }) => color};
`;

export const CompareGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 16px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

export const CompareItem = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;

  span {
    font-size: 0.9rem;
    color: #666;
  }

  strong {
    font-size: 1.3rem;
    color: #333;
  }
`;

export const CompareChange = styled.div`
  font-size: 0.85rem;
  font-weight: 500;
  color: ${({ positive }) => positive ? '#2e7d32' : '#c62828'};
`;