import React from 'react';
import styled from 'styled-components';
import { 
  MdVisibility, MdEdit, MdDelete, MdCheckCircle, 
  MdBlock, MdInfoOutline 
} from 'react-icons/md';
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '../common/Table';
import { StatusBadge } from '../common/StatusBadge';
import { CERTIFICATE_STATUS, CERTIFICATE_TYPE_LABELS } from '../../utils/constants';

const ActionGroup = styled.div`
  display: flex;
  gap: 6px;
  justify-content: center;
  align-items: center;
`;

const ActionButton = styled.button`
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 10px; /* Synchronized corner radius */
  background: #f8fafc;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 1.1rem;

  &:hover {
    transform: translateY(-2px);
    background: ${({ $variant }) => {
      if ($variant === 'danger') return '#fef2f2';
      if ($variant === 'success') return '#f0fdf4';
      return '#eff6ff';
    }};
    color: ${({ $variant }) => {
      if ($variant === 'danger') return '#ef4444';
      if ($variant === 'success') return '#22c55e';
      return '#3b82f6';
    }};
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }

  &:active {
    transform: translateY(0);
  }
`;

const CertName = styled.div`
  font-weight: 700;
  color: #1e3c72;
  font-size: 0.95rem;
  /* Prevent overflow for long names */
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const EmptyState = styled.div`
  padding: 40px;
  text-align: center;
  color: #94a3b8;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;

  svg { font-size: 48px; opacity: 0.5; }
`;

const formatDate = (dateString) => {
  if (!dateString) return '---';
  return new Date(dateString).toLocaleDateString('en-US'); // Changed to US format
};

export const CertificateTable = ({ 
  certificates = [], 
  onView, 
  onEdit, 
  onDelete,
  onApprove,
  onReject,
  isAdmin = false 
}) => {
  if (certificates.length === 0) {
    return (
      // <Table>
      //   <EmptyState>
      //     <MdInfoOutline />
      //     <p>No matching certificates found</p>
      //   </EmptyState>
      // </Table>
      <EmptyState>
      <MdInfoOutline />
      <p>No matching certificates found</p>
    </EmptyState>
    );
  }

  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell>Certificate Name</TableHeaderCell>
          <TableHeaderCell>Type</TableHeaderCell>
          <TableHeaderCell>Issued By</TableHeaderCell>
          <TableHeaderCell>Issue Date</TableHeaderCell>
          <TableHeaderCell>Expiry Date</TableHeaderCell>
          <TableHeaderCell>Status</TableHeaderCell>
          <TableHeaderCell align="center">Actions</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {certificates.map((cert) => (
          <TableRow key={cert.uid}>
            <TableCell>
              <CertName title={cert.name}>{cert.name}</CertName>
            </TableCell>
            <TableCell style={{ color: '#64748b', fontSize: '0.85rem' }}>
              {CERTIFICATE_TYPE_LABELS[cert.certificate_type] || cert.certificate_type}
            </TableCell>
            <TableCell>{cert.issued_by}</TableCell>
            <TableCell>{formatDate(cert.issue_date)}</TableCell>
            <TableCell>
              <span style={{ color: cert.expiration_date ? 'inherit' : '#94a3b8' }}>
                {formatDate(cert.expiration_date)}
              </span>
            </TableCell>
            <TableCell>
              <StatusBadge status={cert.status.toLowerCase()}>
                {cert.status}
              </StatusBadge>
            </TableCell>
            <TableCell>
              <ActionGroup>
                {/* View Details */}
                <ActionButton onClick={() => onView(cert)} title="View Details">
                  <MdVisibility />
                </ActionButton>
                
                {/* Edit (For Chef & Pending only) */}
                {!isAdmin && cert.status === CERTIFICATE_STATUS.PENDING && (
                  <ActionButton onClick={() => onEdit(cert)} title="Edit">
                    <MdEdit />
                  </ActionButton>
                )}
                
                {/* Approve/Reject (For Admin & Pending only) */}
                {isAdmin && cert.status === CERTIFICATE_STATUS.PENDING && (
                  <>
                    <ActionButton 
                      $variant="success" 
                      onClick={() => onApprove(cert)} 
                      title="Approve"
                    >
                      <MdCheckCircle />
                    </ActionButton>
                    <ActionButton 
                      $variant="danger" 
                      onClick={() => onReject(cert)} 
                      title="Reject"
                    >
                      <MdBlock />
                    </ActionButton>
                  </>
                )}
                
                {/* Delete (For Chef & Pending only) */}
                {!isAdmin && cert.status === CERTIFICATE_STATUS.PENDING && (
                  <ActionButton 
                    $variant="danger" 
                    onClick={() => onDelete(cert)} 
                    title="Delete Certificate"
                  >
                    <MdDelete />
                  </ActionButton>
                )}
              </ActionGroup>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};