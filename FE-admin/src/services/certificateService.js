import api from './api';
import { API_ENDPOINTS, CERTIFICATE_STATUS } from '../utils/constants';

export const certificateService = {
  // ========== CHEF APIs ==========
  
  // Create certificate
  createCertificate: async (certificateData) => {
    try {
      console.log('📤 [createCertificate] Creating certificate with data:', certificateData);
      const response = await api.post(API_ENDPOINTS.CERTIFICATES.CREATE, certificateData);
      console.log('📥 [createCertificate] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [createCertificate] Error:', error);
      throw error;
    }
  },

  // Get chef's own certificates
  getMyCertificates: async (params = {}) => {
    try {
      console.log('📤 [getMyCertificates] Fetching with params:', params);
      const response = await api.get(API_ENDPOINTS.CERTIFICATES.MY_LIST, { params });
      console.log('📥 [getMyCertificates] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [getMyCertificates] Error:', error);
      throw error;
    }
  },

  // Get certificate by UID (Chef or Admin)
  getCertificateById: async (uid) => {
    try {
      console.log('📤 [getCertificateById] Fetching certificate UID:', uid);
      const response = await api.get(API_ENDPOINTS.CERTIFICATES.DETAIL(uid));
      console.log('📥 [getCertificateById] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [getCertificateById] Error:', error);
      throw error;
    }
  },

  // Update certificate
  updateCertificate: async (uid, certificateData) => {
    try {
      console.log('📤 [updateCertificate] Updating certificate UID:', uid);
      const response = await api.patch(API_ENDPOINTS.CERTIFICATES.UPDATE(uid), certificateData);
      console.log('📥 [updateCertificate] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [updateCertificate] Error:', error);
      throw error;
    }
  },

  // Soft delete certificate (Chef or Admin)
  softDeleteCertificate: async (uid) => {
    try {
      console.log('📤 [softDeleteCertificate] Soft deleting UID:', uid);
      const response = await api.patch(API_ENDPOINTS.CERTIFICATES.SOFT_DELETE(uid));
      console.log('📥 [softDeleteCertificate] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [softDeleteCertificate] Error:', error);
      throw error;
    }
  },

  // Restore certificate (Chef or Admin)
  restoreCertificate: async (uid) => {
    try {
      console.log('📤 [restoreCertificate] Restoring UID:', uid);
      const response = await api.patch(API_ENDPOINTS.CERTIFICATES.RESTORE(uid));
      console.log('📥 [restoreCertificate] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [restoreCertificate] Error:', error);
      throw error;
    }
  },

  // ========== CERTIFICATE ATTACHMENTS APIs ==========
  
  // Add attachments to certificate (sau khi upload ảnh xong)
addCertificateAttachments: async (uid, attachmentUids) => {
  try {
    console.log('📤 [addCertificateAttachments] ===== START =====');
    console.log('📤 [addCertificateAttachments] Certificate UID:', uid);
    console.log('📤 [addCertificateAttachments] Attachment UIDs:', attachmentUids);
    console.log('📤 [addCertificateAttachments] Number of attachments:', attachmentUids?.length);
    console.log('🔗 [addCertificateAttachments] Endpoint:', API_ENDPOINTS.CERTIFICATE_ATTACHMENTS.ADD(uid));
    
    // Log chi tiết từng attachment UID
    if (attachmentUids && attachmentUids.length > 0) {
      attachmentUids.forEach((aid, idx) => {
        console.log(`📤 [addCertificateAttachments] Attachment ${idx + 1}: ${aid}`);
      });
    }
    
    const requestBody = {
      attachment_uids: attachmentUids
    };
    console.log('📤 [addCertificateAttachments] Request body:', JSON.stringify(requestBody, null, 2));
    
    const response = await api.post(API_ENDPOINTS.CERTIFICATE_ATTACHMENTS.ADD(uid), requestBody);
    
    console.log('📥 [addCertificateAttachments] Response status:', response.status);
    console.log('📥 [addCertificateAttachments] Response data:', response.data);
    console.log('📥 [addCertificateAttachments] Response attachments count:', response.data?.attachments?.length);
    console.log('✅ [addCertificateAttachments] ===== SUCCESS =====');
    
    return response.data;
  } catch (error) {
    console.error('❌ [addCertificateAttachments] ===== ERROR =====');
    console.error('❌ [addCertificateAttachments] Error message:', error.message);
    console.error('❌ [addCertificateAttachments] Error status:', error.response?.status);
    console.error('❌ [addCertificateAttachments] Error data:', error.response?.data);
    console.error('❌ [addCertificateAttachments] Error config:', error.config);
    throw error;
  }
},


  // ========== ADMIN APIs ==========
  
  // Get all certificates with filters
  getAllCertificates: async (params = {}) => {
    try {
      console.log('📤 [getAllCertificates] Fetching with params:', params);
      const response = await api.get(API_ENDPOINTS.CERTIFICATES.ADMIN_LIST, { params });
      console.log('📥 [getAllCertificates] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [getAllCertificates] Error:', error);
      throw error;
    }
  },

  // Set certificate status (Admin)
  setCertificateStatus: async (uid, status, rejectionReason = null) => {
    try {
      console.log('📤 [setCertificateStatus] Setting status for UID:', uid);
      console.log('📤 [setCertificateStatus] Status:', status);
      
      const body = { status };
      if (rejectionReason && status === CERTIFICATE_STATUS.REVOKED) {
        body.rejection_reason = rejectionReason;
      }
      
      const response = await api.patch(API_ENDPOINTS.CERTIFICATES.ADMIN_SET_STATUS(uid), body);
      console.log('📥 [setCertificateStatus] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [setCertificateStatus] Error:', error);
      throw error;
    }
  },
  // Thêm vào certificateService.js
removeCertificateAttachment: async (uid, attachmentUid) => {
  try {
    console.log('📤 [removeCertificateAttachment] Removing attachment:', attachmentUid);
    const response = await api.delete(API_ENDPOINTS.CERTIFICATE_ATTACHMENTS.REMOVE(uid, attachmentUid));
    console.log('📥 [removeCertificateAttachment] Response:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ [removeCertificateAttachment] Error:', error);
    throw error;
  }
},
reorderCertificateAttachments: async (uid, attachments) => {
  try {
    console.log('📤 [reorderCertificateAttachments] Certificate UID:', uid);
    console.log('📤 [reorderCertificateAttachments] Attachments:', attachments);
    
    // ✅ Chuyển đổi đúng format backend yêu cầu
    let requestBody = attachments;
    
    // Nếu attachments đang là [{attachment_uid, position}] thì giữ nguyên
    if (Array.isArray(attachments) && attachments.length > 0) {
      // Kiểm tra xem đã đúng format chưa
      const isValid = attachments.every(item => 
        item.attachment_uid && typeof item.position !== 'undefined'
      );
      
      if (!isValid) {
        // Nếu chưa đúng, chuyển đổi từ positions array
        requestBody = attachments.map((attachment, index) => ({
          attachment_uid: attachment.attachment_uid || attachment,
          position: attachment.position !== undefined ? attachment.position : index
        }));
      }
    } else if (Array.isArray(attachments) && attachments.length === 0) {
      requestBody = [];
    } else {
      console.error('❌ Invalid attachments format:', attachments);
      throw new Error('Attachments must be an array');
    }
    
    console.log('📤 Final request body:', JSON.stringify(requestBody, null, 2));
    
    const response = await api.patch(
      API_ENDPOINTS.CERTIFICATE_ATTACHMENTS.REORDER(uid),
      requestBody  // ✅ Gửi thẳng array, không wrap
    );
    
    console.log('✅ Reorder success:', response.data);
    return response.data;
    
  } catch (error) {
    console.error('❌ Reorder error:', error);
    throw error;
  }
},
};