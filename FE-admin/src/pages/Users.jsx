import React, { useState, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import { 
  MdPeople, MdFilterList, MdRefresh, MdDownload 
} from 'react-icons/md';
import { useNavigate } from 'react-router-dom';
import { Loading } from '../components/common/Loading';
import { Button, IconBtn } from '../components/common/Button';
import { Pagination } from '../components/common/Pagination';
import { UserStats } from '../components/users/UserStats';
import { UserFilters } from '../components/users/UserFilters';
import { ConfirmModal } from '../components/users/ConfirmModal';
import { UserTable } from '../components/users/UserTable';
import { userService } from '../services/userService';

// --- Styled Components ---

const Container = styled.div`
  padding: 24px;
  animation: fadeIn 0.3s ease-in-out;
`;

const Header = styled.div`
  display: flex; 
  justify-content: space-between; 
  align-items: center;
  margin-bottom: 32px; 
  flex-wrap: wrap; 
  gap: 16px;
`;

const TitleSection = styled.div`display: flex; align-items: center; gap: 16px;`;

const TitleIcon = styled.div`
  width: 54px; 
  height: 54px; 
  background: #1e3c72;
  border-radius: 12px;
  display: flex; 
  align-items: center; 
  justify-content: center;
  color: white; 
  font-size: 28px;
  box-shadow: 0 4px 12px rgba(30, 60, 114, 0.2);
`;

const Title = styled.h1`
  font-size: 1.75rem; 
  font-weight: 700; 
  color: #1e293b; 
  margin: 0;
`;

const ActionBar = styled.div`
  display: flex; 
  align-items: center; 
  gap: 12px;
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
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 24px;
`;

const TableTitle = styled.h3`
  font-size: 1.1rem; 
  font-weight: 700; 
  color: #1e3c72; 
  margin: 0;
`;

// --- Component Logic ---

const Users = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState(null);
  
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalRows, setTotalRows] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  const [appliedFilters, setAppliedFilters] = useState({
    user_type: null, is_active: undefined, search: '', dateFrom: '', dateTo: ''
  });
  
  const [tempFilters, setTempFilters] = useState({ ...appliedFilters });

  const [sortConfig, setSortConfig] = useState({
    key: 'date_joined',
    direction: 'desc'
  });

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page: currentPage,
        page_size: pageSize
      };
      
      if (appliedFilters.search) params.search = appliedFilters.search;
      if (appliedFilters.user_type) params.user_type = appliedFilters.user_type;
      if (appliedFilters.is_active !== undefined) params.is_active = appliedFilters.is_active;
      if (appliedFilters.dateFrom) params.from_date = appliedFilters.dateFrom;
      if (appliedFilters.dateTo) params.to_date = appliedFilters.dateTo;
      
      const response = await userService.getUsers(params);
      
      if (response?.data) {
        setUsers(response.data.content || []);
        setTotalRows(response.data.total_rows || 0);
        setTotalPages(response.data.total_pages || 0);
      }
    } catch (error) {
      console.error('❌ Data sync error:', error);
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, appliedFilters]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Dynamic Statistics Calculation
  const stats = {
    totalUsers: totalRows,
    activeUsers: users.filter(u => u.is_active).length,
    newThisWeek: users.filter(u => {
      const date = new Date(u.date_joined);
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      return date > weekAgo;
    }).length,
    bannedUsers: users.filter(u => !u.is_active).length,
    bannedRate: totalRows > 0 
      ? ((users.filter(u => !u.is_active).length / (users.length || 1)) * 100).toFixed(1) 
      : '0.0'
  };

  const handleApplyFilters = () => {
    setAppliedFilters(tempFilters);
    setCurrentPage(1);
    setShowFilters(false);
  };

  const handleResetFilters = () => {
    const reset = { user_type: null, is_active: undefined, search: '', dateFrom: '', dateTo: '' };
    setTempFilters(reset);
    setAppliedFilters(reset);
    setCurrentPage(1);
    setShowFilters(false);
  };

  const confirmActionHandler = async () => {
    if (!selectedUser) return;
    setLoading(true);
    try {
      if (confirmAction === 'deactivate') {
        await userService.deactivateUser(selectedUser.id);
      } else if (confirmAction === 'activate') {
        await userService.activateUser(selectedUser.id);
      }
      await fetchUsers();
    } catch (error) {
      console.error(`❌ Action Error:`, error);
    } finally {
      setLoading(false);
      setShowConfirmModal(false);
      setConfirmAction(null);
      setSelectedUser(null);
    }
  };

  if (loading && users.length === 0) {
    return <Loading fullPage text="Retrieving user database..." />;
  }

  return (
    <Container>
      <Header>
        <TitleSection>
          <TitleIcon><MdPeople /></TitleIcon>
          <Title>Users Management</Title>
        </TitleSection>

        <ActionBar>
          <IconBtn $active={showFilters} onClick={() => setShowFilters(!showFilters)} title="Filters">
            <MdFilterList />
          </IconBtn>
        </ActionBar>
      </Header>

      <UserStats stats={stats} />

      <UserFilters 
        show={showFilters}
        filters={tempFilters}
        onFilterChange={(k, v) => setTempFilters(prev => ({...prev, [k]: v}))}
        onReset={handleResetFilters}
        onApply={handleApplyFilters}
        onClose={() => setShowFilters(false)}
      />

      <TableContainer>

        <UserTable 
          users={users}
          onSort={(key) => setSortConfig({
            key, 
            direction: sortConfig.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc'
          })}
          sortConfig={sortConfig}
          onToggleStatus={(user, action) => {
            setSelectedUser(user);
            setConfirmAction(action);
            setShowConfirmModal(true);
          }}
        />

        {totalPages > 0 && (
          <Pagination 
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
            totalItems={totalRows}
            pageSize={pageSize}
          />
        )}
      </TableContainer>

      <ConfirmModal 
        isOpen={showConfirmModal}
        onClose={() => { setShowConfirmModal(false); setSelectedUser(null); }}
        onConfirm={confirmActionHandler}
        action={confirmAction}
        userName={selectedUser?.username || selectedUser?.email}
      />
    </Container>
  );
};

export default Users;