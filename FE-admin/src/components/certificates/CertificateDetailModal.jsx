import React, { useState } from 'react';
import styled from 'styled-components';
import { 
  MdVisibility, MdPerson, MdCalendarToday, MdInfo, 
  MdCancel, MdImage, MdVerifiedUser
} from 'react-icons/md';
import { Modal } from '../common/Modal';
import { StatusBadge } from '../common/StatusBadge';
import { CERTIFICATE_TYPE_LABELS } from '../../utils/constants';

const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
  
  @media (min-width: 992px) {
    flex-direction: row;
    align-items: flex-start;
  }
`;

const ImageSide = styled.div`
  flex: 1;
  position: sticky;
  top: 0;
`;

const InfoSide = styled.div`
  flex: 1.2;
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const Section = styled.div`
  padding: 20px;
  background: white;
  border: 1px solid #f1f5f9;
  border-radius: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
`;

const SectionTitle = styled.h4`
  display: flex;
  align-items: center;
  gap: 10px;
  color: #1e293b;
  margin: 0 0 16px 0;
  font-size: 0.95rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;

  svg {
    color: #1e3c72;
    font-size: 1.2rem;
  }
`;

const ImageGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
`;

const ImageWrapper = styled.div`
  background: #f8fafc;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.3s ease;
  aspect-ratio: 1 / 1;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    border-color: #1e3c72;
    transform: scale(1.02);
  }
`;

const CertificateImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
`;

const PlaceholderImage = styled.div`
  text-align: center;
  color: #94a3b8;
  padding: 20px;
  
  svg {
    font-size: 48px;
    margin-bottom: 8px;
  }
  
  p {
    font-size: 0.85rem;
  }
`;

const InfoGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
`;

const InfoBox = styled.div`
  .label {
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 4px;
  }
  .value {
    font-size: 0.95rem;
    font-weight: 500;
    color: #1e293b;
    line-height: 1.5;
  }
`;

const RejectionAlert = styled(Section)`
  background: #fef2f2;
  border: 1px solid #fee2e2;
  
  ${SectionTitle} { color: #991b1b; }
  .value { color: #dc2626; font-weight: 600; }
`;

// Lightbox Modal
const Lightbox = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.9);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  
  img {
    max-width: 90%;
    max-height: 90%;
    object-fit: contain;
  }
`;

const formatDate = (date) => {
  if (!date) return 'N/A';
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

export const CertificateDetailModal = ({ isOpen, certificate, onClose }) => {
  const [lightboxImage, setLightboxImage] = useState(null);
  const [imageErrors, setImageErrors] = useState({});

  if (!certificate) return null;

  const attachments = certificate.attachments || [];
  const hasImages = attachments.length > 0;

  const handleImageError = (uid) => {
    setImageErrors(prev => ({ ...prev, [uid]: true }));
  };

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title={`Certificate Details: ${certificate.name}`}
        size="large"
      >
        <Container>
          {/* Left Side: Images Gallery */}
          <ImageSide>
            <SectionTitle><MdImage /> Evidence Images ({attachments.length})</SectionTitle>
            {hasImages ? (
              <ImageGrid>
                {attachments.map((att) => (
                  <ImageWrapper key={att.uid} onClick={() => setLightboxImage(att.public_url)}>
                    {!imageErrors[att.uid] ? (
                      <CertificateImage 
                        src={att.public_url} 
                        alt={att.original_name || 'Certificate evidence'}
                        onError={() => handleImageError(att.uid)}
                      />
                    ) : (
                      <PlaceholderImage>
                        <MdImage size={32} />
                        <p>Failed to load</p>
                      </PlaceholderImage>
                    )}
                  </ImageWrapper>
                ))}
              </ImageGrid>
            ) : (
              <PlaceholderImage>
                <MdVisibility size={48} />
                <p>No images available</p>
              </PlaceholderImage>
            )}
          </ImageSide>

          {/* Right Side: Information */}
          <InfoSide>
            {/* Rejection Alert if Status is REVOKED */}
            {certificate.status === 'REVOKED' && (
              <RejectionAlert>
                <SectionTitle><MdCancel /> Rejection Reason</SectionTitle>
                <div className="value">{certificate.rejection_reason || "No specific reason provided."}</div>
              </RejectionAlert>
            )}

            <Section>
              <SectionTitle><MdInfo /> Basic Information</SectionTitle>
              <InfoGrid>
                <InfoBox>
                  <div className="label">Certificate Name</div>
                  <div className="value">{certificate.name}</div>
                </InfoBox>
                <InfoBox>
                  <div className="label">Status</div>
                  <div className="value">
                    <StatusBadge status={certificate.status?.toLowerCase()}>
                      {certificate.status}
                    </StatusBadge>
                  </div>
                </InfoBox>
                <InfoBox>
                  <div className="label">Type</div>
                  <div className="value">
                    {CERTIFICATE_TYPE_LABELS[certificate.certificate_type] || certificate.certificate_type}
                  </div>
                </InfoBox>
                <InfoBox>
                  <div className="label">Issued By</div>
                  <div className="value">{certificate.issued_by}</div>
                </InfoBox>
              </InfoGrid>
            </Section>

            <Section>
              <SectionTitle><MdCalendarToday /> Validity Period</SectionTitle>
              <InfoGrid>
                <InfoBox>
                  <div className="label">Issue Date</div>
                  <div className="value">{formatDate(certificate.issue_date)}</div>
                </InfoBox>
                <InfoBox>
                  <div className="label">Expiry Date</div>
                  <div className="value">
                    {certificate.expiration_date ? formatDate(certificate.expiration_date) : 'Non-expiring'}
                  </div>
                </InfoBox>
              </InfoGrid>
            </Section>

            <Section>
              <SectionTitle><MdVerifiedUser /> System Verification</SectionTitle>
              <InfoGrid>
                <InfoBox>
                  <div className="label">Owner ID</div>
                  <div className="value">#{certificate.owner}</div>
                </InfoBox>
                <InfoBox>
                  <div className="label">Updated At</div>
                  <div className="value">{formatDate(certificate.updated_at)}</div>
                </InfoBox>
              </InfoGrid>
            </Section>
            
            {certificate.description && (
              <Section>
                <SectionTitle><MdInfo /> Additional Description</SectionTitle>
                <div className="value" style={{fontSize: '0.9rem', color: '#475569'}}>
                  {certificate.description}
                </div>
              </Section>
            )}
          </InfoSide>
        </Container>
      </Modal>

      {/* Lightbox for fullscreen image */}
      {lightboxImage && (
        <Lightbox onClick={() => setLightboxImage(null)}>
          <img src={lightboxImage} alt="Full size" />
        </Lightbox>
      )}
    </>
  );
};