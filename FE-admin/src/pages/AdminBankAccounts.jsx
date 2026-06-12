import React, { useState, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import { 
  MdAccountBalance, MdFilterList, MdCheckCircle, MdCancel, MdSearch
} from 'react-icons/md';
import { Loading } from '../components/common/Loading';
import { Button, IconBtn } from '../components/common/Button';
import { Pagination } from '../components/common/Pagination';
import { bankAccountService } from '../services/bankAccountService';

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

const TitleSection = styled.div`
  display: flex; 
  align-items: center; 
  gap: 16px;
`;

const TitleIcon = styled.div`
  width: 54px; 
  height: 54px; 
  background: #1e3c72;
  border-radius: 14px;
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

const StyledTable = styled.table`
  width: 100%;
  border-collapse: collapse;
`;

const Th = styled.th`
  text-align: left;
  padding: 12px 16px;
  background: #f8fafc;
  color: #64748b;
  font-weight: 600;
  font-size: 0.85rem;
  border-bottom: 1px solid #e2e8f0;
`;

const Td = styled.td`
  padding: 16px;
  color: #1e293b;
  font-size: 0.9rem;
  border-bottom: 1px solid #f1f5f9;
`;

const StatusBadge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  background: ${({ $verified }) => $verified ? '#dcfce7' : '#fee2e2'};
  color: ${({ $verified }) => $verified ? '#166534' : '#991b1b'};
`;

const ActionButton = styled.button`
  padding: 6px 12px;
  border-radius: 6px;
  border: none;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  
  ${({ $variant }) => $variant === 'approve' ? `
    background: #dcfce7;
    color: #166534;
    &:hover { background: #bbf7d0; }
  ` : $variant === 'reject' ? `
    background: #fee2e2;
    color: #991b1b;
    &:hover { background: #fecaca; }
  ` : `
    background: #f1f5f9;
    color: #64748b;
    &:hover { background: #e2e8f0; }
  `}
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

const FilterSection = styled.div`
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
`;

const SearchInput = styled.input`
  padding: 10px 16px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  font-size: 0.9rem;
  width: 300px;
  
  &:focus {
    outline: none;
    border-color: #1e3c72;
    box-shadow: 0 0 0 4px rgba(30, 60, 114, 0.1);
  }
`;

const SelectInput = styled.select`
  padding: 10px 16px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  font-size: 0.9rem;
  background: white;
  cursor: pointer;
  
  &:focus {
    outline: none;
    border-color: #1e3c72;
  }
`;

// --- Component Logic ---

const AdminBankAccounts = () => {
  const [activeTab, setActiveTab] = useState('customers'); // 'customers' or 'chefs'
  const [bankAccounts, setBankAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalRows, setTotalRows] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  
  const [filters, setFilters] = useState({
    search: '',
    status: ''
  });

  const fetchBankAccounts = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page: currentPage,
        page_size: pageSize
      };
      
      if (filters.search) params.search = filters.search;
      if (filters.status !== '') params.status = filters.status;
      
      let response;
      if (activeTab === 'customers') {
        response = await bankAccountService.getCustomerBankAccounts(params);
      } else {
        response = await bankAccountService.getChefBankAccounts(params);
      }
      
      if (response) {
        setBankAccounts(response.content || []);
        setTotalRows(response.total_rows || 0);
        setTotalPages(response.total_pages || 0);
      }
    } catch (error) {
      console.error('❌ Error fetching bank accounts:', error);
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, filters, activeTab]);

  useEffect(() => {
    fetchBankAccounts();
  }, [fetchBankAccounts]);

  const handleVerify = async (bankAccountId, status) => {
    try {
      if (activeTab === 'customers') {
        await bankAccountService.verifyCustomerBankAccount(bankAccountId, status);
      } else {
        await bankAccountService.verifyChefBankAccount(bankAccountId, status);
      }
      fetchBankAccounts();
    } catch (error) {
      alert(`Verification failed: ${error.message}`);
    }
  };

  const handleSearchChange = (e) => {
    setFilters(prev => ({ ...prev, search: e.target.value }));
  };

  const handleStatusChange = (e) => {
    setFilters(prev => ({ ...prev, status: e.target.value }));
  };

  const handleResetFilters = () => {
    setFilters({ search: '', status: '' });
    setCurrentPage(1);
  };

  return (
    <Container>
      <Header>
        <TitleSection>
          <TitleIcon><MdAccountBalance /></TitleIcon>
          <div>
            <Title>Bank Accounts Management</Title>
          </div>
        </TitleSection>
        
        <ActionBar>
          <IconBtn $active={showFilters} onClick={() => setShowFilters(!showFilters)} title="Filters">
            <MdFilterList />
          </IconBtn>
        </ActionBar>
      </Header>

      <TabsContainer>
        <Tab 
          $active={activeTab === 'customers'} 
          onClick={() => { setActiveTab('customers'); setCurrentPage(1); handleResetFilters(); }}
        >
          Customer Bank Accounts
        </Tab>
        <Tab 
          $active={activeTab === 'chefs'} 
          onClick={() => { setActiveTab('chefs'); setCurrentPage(1); handleResetFilters(); }}
        >
          Chef Bank Accounts
        </Tab>
      </TabsContainer>

      {showFilters && (
        <FilterSection>
          <SearchInput 
            type="text" 
            placeholder={`Search by ${activeTab === 'customers' ? 'customer' : 'chef'} email...`}
            value={filters.search}
            onChange={handleSearchChange}
          />
          <SelectInput 
            value={filters.status}
            onChange={handleStatusChange}
          >
            <option value="">All Status</option>
            <option value="true">Verified</option>
            <option value="false">Not Verified</option>
          </SelectInput>
          <Button $variant="secondary" onClick={handleResetFilters}>
            Reset
          </Button>
        </FilterSection>
      )}

      <TableContainer>
        <TableHeader>
          <TableTitle>
            {activeTab === 'customers' ? 'Customer' : 'Chef'} Bank Accounts 
            ({totalRows} total)
          </TableTitle>
        </TableHeader>

        {loading ? (
          <Loading text="Loading bank accounts..." />
        ) : (
          <>
            <StyledTable>
              <thead>
                <tr>
                  <Th>ID</Th>
                  <Th>Email</Th>
                  <Th>Bank Name</Th>
                  <Th>Account Number</Th>
                  <Th>Account Holder</Th>
                  <Th>Status</Th>
                  <Th>Actions</Th>
                </tr>
              </thead>
              <tbody>
                {bankAccounts.length > 0 ? (
                  bankAccounts.map((account) => (
                    <tr key={account.uid || account.id}>
                      <Td>{account.uid || account.id}</Td>
                      <Td>{account.email || account.user?.email || 'N/A'}</Td>
                      <Td>{account.bank_name || 'N/A'}</Td>
                      <Td>{account.account_number || 'N/A'}</Td>
                      <Td>{account.account_holder_name || 'N/A'}</Td>
                      <Td>
                        <StatusBadge $verified={account.is_verified}>
                          {account.is_verified ? (
                            <>
                              <MdCheckCircle /> Verified
                            </>
                          ) : (
                            <>
                              <MdCancel /> Pending
                            </>
                          )}
                        </StatusBadge>
                      </Td>
                      <Td>
                        {account.is_verified ? (
                          <ActionButton 
                            $variant="reject"
                            onClick={() => handleVerify(account.uid || account.id, false)}
                          >
                            Reject
                          </ActionButton>
                        ) : (
                          <ActionButton 
                            $variant="approve"
                            onClick={() => handleVerify(account.uid || account.id, true)}
                          >
                            Approve
                          </ActionButton>
                        )}
                      </Td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <Td colSpan="7" style={{ textAlign: 'center', color: '#64748b' }}>
                      No bank accounts found
                    </Td>
                  </tr>
                )}
              </tbody>
            </StyledTable>

            {totalPages > 1 && (
              <Pagination 
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={setCurrentPage}
                totalItems={totalRows}
                pageSize={pageSize}
              />
            )}
          </>
        )}
      </TableContainer>
    </Container>
  );
};

export default AdminBankAccounts;