import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { MdVerified, MdRefresh, MdFilterList, MdDownload } from 'react-icons/md';
import { Loading } from '../components/common/Loading';
import { Button, IconBtn } from '../components/common/Button';
import { Pagination } from '../components/common/Pagination';
import { CertificateStats } from '../components/certificates/CertificateStats';
import { CertificateFilters } from '../components/certificates/CertificateFilters';
import { CertificateTable } from '../components/certificates/CertificateTable';
import { CertificateDetailModal } from '../components/certificates/CertificateDetailModal';
import { RejectModal } from '../components/certificates/RejectModal';
import { certificateService } from '../services/certificateService';
import { CERTIFICATE_STATUS } from '../utils/constants';

// --- Styled Components ---

const Container = styled.div`
  padding: 24px;
  animation: fadeIn 0.3s ease-in-out;
`;

const Header = styled.div`
  display: flex; 
  justify-content: space-between; 
  align-items: center;
  margin-bottom: 24px; 
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
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
`;

const TableHeader = styled.div`
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 20px;
`;

const TableTitle = styled.h3`
  font-size: 1.1rem; 
  font-weight: 700; 
  color: #1e3c72; 
  margin: 0;
`;

// --- Component Logic ---

const AdminCertificates = () => {
  const [certificates, setCertificates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedCertificate, setSelectedCertificate] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRows, setTotalRows] = useState(0);
  
  const [tempFilters, setTempFilters] = useState({
    status: 'all', type: 'all', search: '', chef_id: ''
  });

  const [appliedFilters, setAppliedFilters] = useState({
    status: 'all', type: 'all', search: '', chef_id: ''
  });

  const [stats, setStats] = useState({
    total: 0, pending: 0, active: 0, expired: 0, revoked: 0
  });

  const pageSize = 10;

  const fetchCertificates = async () => {
    setLoading(true);
    try {
      const params = {
        page: currentPage,
        page_size: pageSize
      };

      if (appliedFilters.status !== 'all') params.status = appliedFilters.status;
      if (appliedFilters.type !== 'all') params.categories = appliedFilters.type;
      if (appliedFilters.search) params.search = appliedFilters.search;
      if (appliedFilters.chef_id) params.chef_id = appliedFilters.chef_id;

      const response = await certificateService.getAllCertificates(params);
      
      if (response?.data) {
        const certList = response.data.content || [];
        setCertificates(certList);
        setTotalRows(response.data.total_rows || 0);
        setTotalPages(response.data.total_pages || 1);

        // Map server response to dashboard stats
        setStats({
          total: response.data.total_rows || 0,
          pending: certList.filter(c => c?.status === 'PENDING').length,
          active: certList.filter(c => c?.status === 'ACTIVE').length,
          expired: certList.filter(c => c?.status === 'EXPIRED').length,
          revoked: certList.filter(c => c?.status === 'REVOKED').length
        });
      }
    } catch (error) {
      console.error('❌ Sync Error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCertificates();
  }, [currentPage, appliedFilters]);

  const handleFilterChange = (key, value) => {
    setTempFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleApplyFilters = () => {
    setAppliedFilters(tempFilters);
    setCurrentPage(1);
    setShowFilters(false);
  };

  const handleResetFilters = () => {
    const reset = { status: 'all', type: 'all', search: '', chef_id: '' };
    setTempFilters(reset);
    setAppliedFilters(reset);
    setCurrentPage(1);
    setShowFilters(false);
  };

  const handleApprove = async (cert) => {
    try {
      await certificateService.setCertificateStatus(cert.uid, CERTIFICATE_STATUS.ACTIVE);
      fetchCertificates();
    } catch (error) {
      alert(`Approval process failed: ${error.message}`);
    }
  };

  const handleRejectConfirm = async (reason) => {
    try {
      await certificateService.setCertificateStatus(
        selectedCertificate.uid, 
        CERTIFICATE_STATUS.REVOKED, 
        reason
      );
      setShowRejectModal(false);
      setSelectedCertificate(null);
      fetchCertificates();
    } catch (error) {
      alert(`Rejection failed: ${error.message}`);
    }
  };

  if (loading && certificates.length === 0) {
    return <Loading fullPage text="Retrieving credential database..." />;
  }

  return (
    <Container>
      <Header>
        <TitleSection>
          <TitleIcon><MdVerified /></TitleIcon>
          <Title>Certificates Management</Title>
        </TitleSection>
        
        <ActionBar>
          <IconBtn $active={showFilters} onClick={() => setShowFilters(!showFilters)} title="Filters">
            <MdFilterList />
          </IconBtn>
        </ActionBar>
      </Header>

      <CertificateStats stats={stats} />

      <CertificateFilters 
        show={showFilters}
        filters={tempFilters}
        onFilterChange={handleFilterChange}
        onReset={handleResetFilters}
        onApply={handleApplyFilters}
        onClose={() => setShowFilters(false)}
        isAdmin={true}
      />

      <TableContainer>

        <CertificateTable 
          certificates={certificates}
          onView={(cert) => { setSelectedCertificate(cert); setShowDetailModal(true); }}
          onApprove={handleApprove}
          onReject={(cert) => { setSelectedCertificate(cert); setShowRejectModal(true); }}
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

      <CertificateDetailModal
        isOpen={showDetailModal}
        certificate={selectedCertificate}
        onClose={() => { setShowDetailModal(false); setSelectedCertificate(null); }}
      />

      <RejectModal 
        isOpen={showRejectModal}
        onClose={() => { setShowRejectModal(false); setSelectedCertificate(null); }}
        onConfirm={handleRejectConfirm}
        certificateName={selectedCertificate?.name}
      />
    </Container>
  );
};

export default AdminCertificates;