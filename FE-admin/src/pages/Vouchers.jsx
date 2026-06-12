import React, { useState, useEffect, useMemo } from 'react';
import styled from 'styled-components';
import { MdLocalOffer, MdAdd, MdRefresh, MdFilterList } from 'react-icons/md';
import { Loading } from '../components/common/Loading';
import { Button, IconBtn } from '../components/common/Button';
import { Pagination } from '../components/common/Pagination';
import { VoucherStats } from '../components/vouchers/VoucherStats';
import { VoucherFilters } from '../components/vouchers/VoucherFilters';
import { VoucherTable } from '../components/vouchers/VoucherTable';
import { VoucherForm } from '../components/vouchers/VoucherForm';
import { DeleteVoucherModal } from '../components/vouchers/DeleteVoucherModal'; // Thay đổi import
import { voucherService } from '../services/voucherService';

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

// --- Main Component ---

const Vouchers = () => {
  const [vouchers, setVouchers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [selectedVoucher, setSelectedVoucher] = useState(null);
  
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const [voucherStats, setVoucherStats] = useState({
    totalVouchers: 0, activeVouchers: 0, inactiveVouchers: 0, expiringSoon: 0
  });

  const [appliedFilters, setAppliedFilters] = useState({
    voucher_type: 'all', discount_type: 'all', is_active: 'all', code: '', name: '', from_date: '', to_date: ''
  });
  
  const [tempFilters, setTempFilters] = useState({ ...appliedFilters });

  const fetchVouchers = async () => {
    setLoading(true);
    try {
      const response = await voucherService.getVouchers();
      const list = response?.data || response || [];
      setVouchers(Array.isArray(list) ? list : []);

      const now = new Date();
      const horizon = new Date();
      horizon.setDate(horizon.getDate() + 7);

      setVoucherStats({
        totalVouchers: list.length,
        activeVouchers: list.filter(v => v.is_active).length,
        inactiveVouchers: list.filter(v => !v.is_active).length,
        expiringSoon: list.filter(v => {
          if (!v.end_date || !v.is_active) return false;
          const end = new Date(v.end_date);
          return end <= horizon && end > now;
        }).length
      });
    } catch (error) {
      console.error('❌ Voucher Sync Error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchVouchers(); }, []);

  const { paginatedVouchers, totalRows, totalPages } = useMemo(() => {
    const filtered = vouchers.filter(v => {
      const matchScope = appliedFilters.voucher_type === 'all' || v.voucher_type === appliedFilters.voucher_type;
      const matchReward = appliedFilters.discount_type === 'all' || v.discount_type === appliedFilters.discount_type;
      const matchActive = appliedFilters.is_active === 'all' || v.is_active === (appliedFilters.is_active === 'true');
      const matchCode = !appliedFilters.code || v.code.toLowerCase().includes(appliedFilters.code.toLowerCase());
      const matchName = !appliedFilters.name || v.name.toLowerCase().includes(appliedFilters.name.toLowerCase());
      
      const matchStart = !appliedFilters.from_date || new Date(v.start_date) >= new Date(appliedFilters.from_date);
      const matchEnd = !appliedFilters.to_date || new Date(v.end_date) <= new Date(appliedFilters.to_date);

      return matchScope && matchReward && matchActive && matchCode && matchName && matchStart && matchEnd;
    });

    const start = (currentPage - 1) * pageSize;
    return {
      paginatedVouchers: filtered.slice(start, start + pageSize),
      totalRows: filtered.length,
      totalPages: Math.ceil(filtered.length / pageSize)
    };
  }, [vouchers, appliedFilters, currentPage]);

  const handleCreateOrUpdate = async (formData) => {
    try {
      if (selectedVoucher) {
        await voucherService.updateVoucher(selectedVoucher.uid, formData);
      } else {
        await voucherService.createVoucher(formData);
      }
      setShowForm(false);
      setSelectedVoucher(null);
      fetchVouchers();
    } catch (error) {
      alert(`Operation failed: ${error.message}`);
    }
  };

  const handleDeleteConfirm = async () => {
    try {
      await voucherService.deleteVoucher(selectedVoucher.uid);
      setShowConfirmModal(false);
      setSelectedVoucher(null);
      fetchVouchers();
    } catch (error) {
      alert(`Delete failed: ${error.message}`);
    }
  };

  if (loading && vouchers.length === 0) {
    return <Loading fullPage text="Syncing campaign database..." />;
  }

  return (
    <Container>
      <Header>
        <TitleSection>
          <TitleIcon><MdLocalOffer /></TitleIcon>
          <Title>Vouchers Management</Title>
        </TitleSection>
        
        <ActionBar>

          <IconBtn $active={showFilters} onClick={() => setShowFilters(!showFilters)} title="Filters">
            <MdFilterList />
          </IconBtn>
          <Button onClick={() => { setSelectedVoucher(null); setShowForm(true); }}>
        New
          </Button>
        </ActionBar>
      </Header>

      <VoucherStats stats={voucherStats} />

      <VoucherFilters 
        show={showFilters}
        filters={tempFilters}
        onFilterChange={(k, v) => setTempFilters(p => ({...p, [k]: v}))}
        onReset={() => {
          const reset = { voucher_type: 'all', discount_type: 'all', is_active: 'all', code: '', name: '', from_date: '', to_date: '' };
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
        <VoucherTable 
          vouchers={paginatedVouchers}
          onEdit={(v) => { setSelectedVoucher(v); setShowForm(true); }}
          onDelete={(v) => { setSelectedVoucher(v); setShowConfirmModal(true); }}
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

      <VoucherForm 
        isOpen={showForm}
        onClose={() => { setShowForm(false); setSelectedVoucher(null); }}
        onSubmit={handleCreateOrUpdate}
        initialData={selectedVoucher}
      />

      <DeleteVoucherModal 
        isOpen={showConfirmModal}
        onClose={() => {
          setShowConfirmModal(false);
          setSelectedVoucher(null);
        }}
        onConfirm={handleDeleteConfirm}
        voucher={selectedVoucher}
      />
    </Container>
  );
};

export default Vouchers;