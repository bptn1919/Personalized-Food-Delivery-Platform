import React from 'react';
import styled from 'styled-components';
import { 
  MdPerson, MdRestaurant, MdList, MdInfo,
  MdLocalShipping, MdImage, MdReceipt
} from 'react-icons/md';
import { Modal } from '../common/Modal';
import { formatCurrency, formatDate } from '../../utils/helpers';

// --- Styled Components ---

const ModalContent = styled.div`
  padding: 10px 0;
  max-height: 75vh;
  overflow-y: auto;
  
  &::-webkit-scrollbar { width: 6px; }
  &::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }
`;

const Section = styled.div`
  margin-bottom: 24px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 16px;
  border: 1px solid #f1f5f9;
`;

const SectionTitle = styled.h4`
  display: flex;
  align-items: center;
  gap: 10px;
  color: #1e3c72;
  margin: 0 0 16px 0;
  font-size: 1.1rem;
  font-weight: 700;

  svg { color: #3b82f6; font-size: 1.3rem; }
`;

const InfoGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
`;

const InfoItem = styled.div`
  .label {
    font-size: 0.75rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 700;
    margin-bottom: 6px;
  }
  .value {
    font-size: 0.95rem;
    font-weight: 600;
    color: #1e293b;
    word-break: break-word;
  }
`;

const ItemsTable = styled.table`
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin-top: 12px;
  
  th {
    text-align: left;
    padding: 12px;
    background: #f1f5f9;
    color: #475569;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    &:first-child { border-radius: 8px 0 0 8px; }
    &:last-child { border-radius: 0 8px 8px 0; }
  }
  
  td {
    padding: 12px;
    border-bottom: 1px solid #f1f5f9;
    font-size: 0.9rem;
    color: #334155;
  }
`;

const DishCell = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;

  img {
    width: 44px;
    height: 44px;
    object-fit: cover;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
  }
`;

const StatusBadge = styled.span`
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  
  background: ${({ $status }) => {
    switch($status) {
      case 'COMPLETED': case 'SUCCESS': return '#dcfce7';
      case 'PROCESSING': case 'PENDING': return '#fef3c7';
      case 'DELIVERING': return '#dbeafe';
      case 'CANCELLED': return '#fee2e2';
      default: return '#f1f5f9';
    }
  }};
  
  color: ${({ $status }) => {
    switch($status) {
      case 'COMPLETED': case 'SUCCESS': return '#166534';
      case 'PROCESSING': case 'PENDING': return '#92400e';
      case 'DELIVERING': return '#1e40af';
      case 'CANCELLED': return '#991b1b';
      default: return '#475569';
    }
  }};
`;

const PriceBreakdown = styled.div`
  margin-top: 20px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
`;

const PriceRow = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 0.9rem;
  color: #64748b;
  
  &.discount { color: #10b981; font-weight: 600; }
  
  &.total {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 2px solid #f1f5f9;
    font-weight: 800;
    color: #1e3c72;
    font-size: 1.2rem;
  }
`;

// --- Component ---

export const OrderDetailModal = ({ isOpen, order, onClose }) => {
  if (!order) return null;

  const data = order?.data || order;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Order Invoice - ${data?.uid?.slice(0, 8).toUpperCase()}`}
      size="large"
    >
      <ModalContent>
        {/* Workflow Status */}
        <Section>
          <SectionTitle><MdInfo /> Operational Status</SectionTitle>
          <InfoGrid>
            <InfoItem>
              <div className="label">Fullfillment</div>
              <div className="value"><StatusBadge $status={data.status}>{data.status}</StatusBadge></div>
            </InfoItem>
            <InfoItem>
              <div className="label">Payment</div>
              <div className="value"><StatusBadge $status={data.payment_status}>{data.payment_status}</StatusBadge></div>
            </InfoItem>
            <InfoItem>
              <div className="label">Method</div>
              <div className="value">{data.payment_method || 'Standard'}</div>
            </InfoItem>
            <InfoItem>
              <div className="label">Voucher</div>
              <div className="value" style={{color: '#3b82f6'}}>{data.voucher_code || 'None'}</div>
            </InfoItem>
          </InfoGrid>
        </Section>

        {/* Stakeholders */}
        <InfoGrid style={{ marginBottom: '24px' }}>
          <Section style={{ marginBottom: 0 }}>
            <SectionTitle><MdPerson /> Customer Info</SectionTitle>
            <InfoItem style={{ marginBottom: '12px' }}>
              <div className="label">Name</div>
              <div className="value">{data.customer_name || 'Anonymous'}</div>
            </InfoItem>
            <InfoItem>
              <div className="label">Contact</div>
              <div className="value">{data.customer_phone || data.customer_email}</div>
            </InfoItem>
          </Section>

          <Section style={{ marginBottom: 0 }}>
            <SectionTitle><MdRestaurant /> Chef Assigned</SectionTitle>
            <InfoItem style={{ marginBottom: '12px' }}>
              <div className="label">Professional Name</div>
              <div className="value">{data.chef_name || 'Assigning...'}</div>
            </InfoItem>
            <InfoItem>
              <div className="label">Provider Email</div>
              <div className="value">{data.chef_email || 'N/A'}</div>
            </InfoItem>
          </Section>
        </InfoGrid>

        {/* Itemized List */}
        <Section>
          <SectionTitle><MdList /> Itemized Receipt</SectionTitle>
          <ItemsTable>
            <thead>
              <tr>
                <th>Product</th>
                <th>Qty</th>
                <th>Unit Price</th>
                <th style={{ textAlign: 'right' }}>Subtotal</th>
              </tr>
            </thead>
            <tbody>
              {data.items?.length > 0 ? (
                data.items.map((item, idx) => (
                  <tr key={idx}>
                    <td>
                      <DishCell>
                        {item.dish_image_url ? (
                          <img src={item.dish_image_url} alt="" />
                        ) : (
                          <MdImage size={44} color="#cbd5e1" />
                        )}
                        {item.dish_name}
                      </DishCell>
                    </td>
                    <td>x{item.quantity}</td>
                    <td>{formatCurrency(item.price)}</td>
                    <td style={{ textAlign: 'right', fontWeight: 700 }}>
                      {formatCurrency(item.subtotal)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan="4" style={{ textAlign: 'center' }}>Empty manifest</td></tr>
              )}
            </tbody>
          </ItemsTable>

          <PriceBreakdown>
            <PriceRow><span>Items Subtotal</span><span>{formatCurrency(data.sub_total)}</span></PriceRow>
            <PriceRow><span>Service Fees & Tax</span><span>{formatCurrency(data.tax_and_fees)}</span></PriceRow>
            <PriceRow><span>Logistics Fee</span><span>{formatCurrency(data.delivery_fee)}</span></PriceRow>
            
            {(data.platform_subtotal_discount > 0 || data.shop_discount > 0) && (
              <PriceRow className="discount">
                <span>Total Savings</span>
                <span>-{formatCurrency((data.platform_subtotal_discount || 0) + (data.shop_discount || 0))}</span>
              </PriceRow>
            )}
            
            <PriceRow className="total">
              <span>Grand Total</span>
              <span>{formatCurrency(data.total_price)}</span>
            </PriceRow>
          </PriceBreakdown>
        </Section>

        {/* Timeline */}
        <Section>
          <SectionTitle><MdLocalShipping /> Logistics & Timeline</SectionTitle>
          <InfoGrid>
            <InfoItem>
              <div className="label">Target Delivery</div>
              <div className="value">{data.delivery_date} at {data.delivery_time}</div>
            </InfoItem>
            <InfoItem>
              <div className="label">Order Placed</div>
              <div className="value">{formatDate(data.created_at)}</div>
            </InfoItem>
            <InfoItem style={{ gridColumn: 'span 2' }}>
              <div className="label">Destination</div>
              <div className="value">{data.delivery_address}</div>
            </InfoItem>
          </InfoGrid>
        </Section>
      </ModalContent>
    </Modal>
  );
};