import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { MdVerified, MdAdd, MdRefresh, MdFilterList } from 'react-icons/md';
import { Loading } from '../components/common/Loading';
import { Button, IconBtn } from '../components/common/Button';
import { Pagination } from '../components/common/Pagination';
import { CertificateStats } from '../components/certificates/CertificateStats';
import { CertificateFilters } from '../components/certificates/CertificateFilters';
import { CertificateTable } from '../components/certificates/CertificateTable';
import { CertificateForm } from '../components/certificates/CertificateForm';
import { CertificateDetailModal } from '../components/certificates/CertificateDetailModal';
import { DeleteCertificateModal } from '../components/certificates/DeleteCertificateModal';
import { certificateService } from '../services/certificateService';
import { attachmentService } from '../services/attachmentService';

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
  flex-wrap: wrap;
`;

const TableContainer = styled.div`
  background: white;
  padding: 24px;
  border-radius: 16px;
  border: 1px solid #f1f5f9;
  margin-top: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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

const ChefCertificates = () => {
  const [certificates, setCertificates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedCertificate, setSelectedCertificate] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRows, setTotalRows] = useState(0);
  
  const [tempFilters, setTempFilters] = useState({ status: 'all', type: 'all', search: '' });
  const [appliedFilters, setAppliedFilters] = useState({ status: 'all', type: 'all', search: '' });

  const [stats, setStats] = useState({
    total: 0, pending: 0, active: 0, expired: 0, revoked: 0
  });

  const pageSize = 10;

  const fetchCertificates = async () => {
    setLoading(true);
    try {
      const params = { page: currentPage, page_size: pageSize };

      if (appliedFilters.status !== 'all') params.status = appliedFilters.status;
      if (appliedFilters.type !== 'all') params.categories = appliedFilters.type;
      if (appliedFilters.search) params.search = appliedFilters.search;

      const response = await certificateService.getMyCertificates(params);
      
      if (response?.data) {
        const certList = response.data.content || [];
        setCertificates(certList);
        setTotalRows(response.data.total_rows || 0);
        setTotalPages(response.data.total_pages || 1);

        setStats({
          total: response.data.total_rows || 0,
          pending: certList.filter(c => c?.status === 'PENDING').length,
          active: certList.filter(c => c?.status === 'ACTIVE').length,
          expired: certList.filter(c => c?.status === 'EXPIRED').length,
          revoked: certList.filter(c => c?.status === 'REVOKED').length
        });
      }
    } catch (error) {
      console.error('Data Fetch Error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCertificates();
  }, [currentPage, appliedFilters]);

  const handleApplyFilters = () => {
    setAppliedFilters(tempFilters);
    setCurrentPage(1);
    setShowFilters(false);
  };

  const handleResetFilters = () => {
    const reset = { status: 'all', type: 'all', search: '' };
    setTempFilters(reset);
    setAppliedFilters(reset);
    setCurrentPage(1);
    setShowFilters(false);
  };

const handleCreateCertificate = async (formData) => {
  try {
    console.log('📤 [handleCreateCertificate] Form data:', formData);
    
    // Bước 1: Tạo certificate trước (không có ảnh)
    const certificateData = {
      name: formData.name,
      description: formData.description,
      issued_by: formData.issued_by,
      issue_date: formData.issue_date,
      expiration_date: formData.expiration_date || null,
      certificate_type: formData.certificate_type,
    };
    
    const response = await certificateService.createCertificate(certificateData);
    console.log('📥 Create certificate response:', response);
    
    // ✅ SỬA: Lấy UID từ response.data (vì response có cấu trúc { data: {...} })
    const certificateUid = response?.data?.uid;
    console.log('📥 Certificate UID:', certificateUid);
    
    if (!certificateUid) {
      throw new Error('Failed to get certificate UID from response');
    }
    
    // Bước 2: Gắn ảnh vào certificate (nếu có)
    // ✅ SỬA: Lọc bỏ undefined/null và đảm bảo là string
    const attachmentUids = (formData.attachment_uids || [])
      .filter(uid => uid && typeof uid === 'string');
    console.log('📤 Attachment UIDs to add:', attachmentUids);
    
    if (attachmentUids.length > 0) {
      await certificateService.addCertificateAttachments(certificateUid, attachmentUids);
    }
    
    setShowForm(false);
    fetchCertificates();
  } catch (error) {
    console.error('❌ Submission failed:', error);
    alert(`Submission failed: ${error.message}`);
  }
};

const handleUpdateCertificate = async (formData) => {
  try {
    // Bước 1: Cập nhật thông tin certificate
    await certificateService.updateCertificate(selectedCertificate.uid, {
      name: formData.name,
      description: formData.description,
      issued_by: formData.issued_by,
      issue_date: formData.issue_date,
      expiration_date: formData.expiration_date || null,
      certificate_type: formData.certificate_type,
    });
    
    // Bước 2: Lọc ra những attachment mới (chưa có trong certificate)
    const existingAttachmentUids = selectedCertificate.attachments?.map(att => att.uid) || [];
    const newAttachmentUids = (formData.attachment_uids || []).filter(
      uid => !existingAttachmentUids.includes(uid)
    );
    
    console.log('Existing attachments:', existingAttachmentUids);
    console.log('New attachments to add:', newAttachmentUids);
    
    // Bước 3: Chỉ thêm những attachment mới
    if (newAttachmentUids.length > 0) {
      await certificateService.addCertificateAttachments(selectedCertificate.uid, newAttachmentUids);
    }
    
    setShowForm(false);
    setSelectedCertificate(null);
    fetchCertificates();
  } catch (error) {
    console.error('Update failed:', error);
    alert(`Update failed: ${error.message}`);
  }
};
  const handleDeleteConfirm = async () => {
    try {
      await certificateService.softDeleteCertificate(selectedCertificate.uid);
      setShowDeleteModal(false);
      setSelectedCertificate(null);
      fetchCertificates();
    } catch (error) {
      alert(`Deletion failed: ${error.message}`);
    }
  };

  if (loading && certificates.length === 0) {
    return <Loading fullPage text="Syncing your credentials..." />;
  }

  return (
    <Container>
      <Header>
        <TitleSection>
          <TitleIcon><MdVerified /></TitleIcon>
          <Title>Certificates Management</Title>
        </TitleSection>
        
        <ActionBar>
          <IconBtn $active={showFilters} onClick={() => setShowFilters(!showFilters)} title="Toggle Filters">
            <MdFilterList />
          </IconBtn>
          <Button onClick={() => { setSelectedCertificate(null); setShowForm(true); }}>
             New
          </Button>
        </ActionBar>
      </Header>

      <CertificateStats stats={stats} />

      <CertificateFilters 
        show={showFilters}
        filters={tempFilters}
        onFilterChange={(k, v) => setTempFilters(p => ({ ...p, [k]: v }))}
        onReset={handleResetFilters}
        onApply={handleApplyFilters}
        onClose={() => setShowFilters(false)}
        isAdmin={false}
      />

      <TableContainer>
        <CertificateTable 
          certificates={certificates}
          onView={(cert) => { setSelectedCertificate(cert); setShowDetailModal(true); }}
          onEdit={(cert) => { setSelectedCertificate(cert); setShowForm(true); }}
          onDelete={(cert) => { setSelectedCertificate(cert); setShowDeleteModal(true); }}
          isAdmin={false}
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

      <CertificateForm 
        isOpen={showForm}
        onClose={() => { setShowForm(false); setSelectedCertificate(null); }}
        onSubmit={selectedCertificate ? handleUpdateCertificate : handleCreateCertificate}
        initialData={selectedCertificate ? {
          ...selectedCertificate,
          existing_image_url: selectedCertificate.public_url
        } : null}
      />

      <CertificateDetailModal
        isOpen={showDetailModal}
        certificate={selectedCertificate}
        onClose={() => { setShowDetailModal(false); setSelectedCertificate(null); }}
      />

      <DeleteCertificateModal 
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setSelectedCertificate(null);
        }}
        onConfirm={handleDeleteConfirm}
        certificate={selectedCertificate}
      />
    </Container>
  );
};

export default ChefCertificates;