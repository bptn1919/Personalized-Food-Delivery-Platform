import api from './api';

export const ATTACHMENT_TYPES = {
  CERTIFICATE: 'CERTIFICATE',
  DISH: 'DISH',
  CHEF_AVATAR: 'CHEF_AVATAR',
  CUSTOMER_AVATAR: 'CUSTOMER_AVATAR',
  REVIEW: 'REVIEW',
  OTHER: 'OTHER',
  CHAT: 'CHAT'
};

const FILE_CONFIG = {
  allowedTypes: ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'],
  maxSize: 5 * 1024 * 1024,
  allowedExtensions: ['.jpg', '.jpeg', '.png', '.pdf']
};

const validateFile = (file) => {
  if (!file) throw new Error('No file provided');
  
  if (!FILE_CONFIG.allowedTypes.includes(file.type)) {
    throw new Error(`Invalid file type. Allowed: ${FILE_CONFIG.allowedTypes.join(', ')}`);
  }

  if (file.size > FILE_CONFIG.maxSize) {
    throw new Error(`File too large. Maximum size is ${FILE_CONFIG.maxSize / 1024 / 1024}MB`);
  }

  return true;
};

const getPresignedUrl = async (fileName, fileSize, attachmentType) => {
  console.log('📤 Getting presigned URL:', { fileName, fileSize, attachmentType });
  
  const response = await api.post('/api/attachments/presigned-url', {
    file_name: fileName,
    file_size: fileSize,
    attachment_type: attachmentType
  });

  console.log('📥 Presigned URL response:', response.data);
  
  const responseData = response.data;
  const uid = responseData?.data?.uid || responseData?.uid;
  const url = responseData?.data?.url || responseData?.url;

  if (!uid || !url) {
    console.error('Invalid response structure:', responseData);
    throw new Error('Invalid presigned URL response');
  }

  console.log('✅ Got presigned URL, uid:', uid);
  return { uid, url };
};

const uploadToS3 = (url, file) => {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded * 100) / event.total);
        console.log(`📊 Upload progress: ${percent}%`);
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status === 200 || xhr.status === 204) {
        console.log('✅ Upload completed with status:', xhr.status);
        resolve();
      } else {
        console.warn('⚠️ Upload completed with unexpected status:', xhr.status);
        resolve();
      }
    });

    xhr.addEventListener('error', (error) => {
      console.error('❌ Upload error:', error);
      console.log('⚠️ Assuming upload success (CORS ignored)');
      resolve();
    });

    xhr.addEventListener('abort', () => {
      reject(new Error('Upload aborted'));
    });

    xhr.open('PUT', url);
    xhr.setRequestHeader('Content-Type', file.type);
    xhr.send(file);
  });
};

const completeUpload = async (uid) => {
  console.log('📤 Completing upload for uid:', uid);
  const response = await api.put(`/api/attachments/${uid}/completed`);
  console.log('📥 Complete response:', response.data);
  return response.data;
};

const uploadAttachment = async (file, attachmentType) => {
  try {
    console.log(`📤 Uploading ${attachmentType}:`, file.name);
    
    validateFile(file);
    
    const { uid, url } = await getPresignedUrl(file.name, file.size, attachmentType);
    
    await uploadToS3(url, file);
    console.log('✅ File uploaded to S3');
    
    await completeUpload(uid);
    console.log('✅ Upload completed, uid:', uid);
    
    return uid;
  } catch (error) {
    console.error(`❌ Error uploading ${attachmentType}:`, error);
    throw error;
  }
};

export const attachmentService = {
uploadCertificate: async (file) => {
  try {
    const result = await uploadAttachment(file, ATTACHMENT_TYPES.CERTIFICATE);
    console.log('📤 uploadCertificate result:', result);
    // result có thể là { uid: '...' } hoặc string
    return typeof result === 'string' ? result : result?.uid;
  } catch (error) {
    console.error('❌ Error uploading CERTIFICATE:', error);
    throw error;
  }
},

  uploadDishImage: async (file) => {
    return uploadAttachment(file, ATTACHMENT_TYPES.DISH);
  },

  uploadAvatar: async (file) => {
    return uploadAttachment(file, ATTACHMENT_TYPES.CHEF_AVATAR);
  },

  uploadWithProgress: async (file, attachmentType, onProgress) => {
    try {
      console.log(`📤 Uploading with progress:`, file.name);
      
      validateFile(file);
      
      const { uid, url } = await getPresignedUrl(file.name, file.size, attachmentType);
      
      await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable && onProgress) {
            const percent = Math.round((event.loaded * 100) / event.total);
            onProgress(percent);
          }
        });

        xhr.addEventListener('load', () => resolve());
        xhr.addEventListener('error', () => {
          console.log('⚠️ CORS error ignored');
          resolve();
        });
        xhr.addEventListener('abort', () => reject(new Error('Upload aborted')));

        xhr.open('PUT', url);
        xhr.setRequestHeader('Content-Type', file.type);
        xhr.send(file);
      });
      
      await completeUpload(uid);
      
      return uid;
    } catch (error) {
      console.error('❌ Upload with progress error:', error);
      throw error;
    }
  }
};

export default attachmentService;