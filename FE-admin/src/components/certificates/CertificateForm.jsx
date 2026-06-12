import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Modal } from '../common/Modal';
import { CERTIFICATE_TYPES } from '../../utils/constants';
import { MdCloudUpload, MdErrorOutline, MdDelete, MdAdd, MdDragHandle } from 'react-icons/md';
import { attachmentService } from '../../services/attachmentService';
import { certificateService } from '../../services/certificateService';

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 10px 0;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const Label = styled.label`
  font-size: 0.85rem;
  color: #475569;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;

  span { color: #ef4444; }
`;

const CommonInputStyles = `
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  font-size: 0.95rem;
  color: #1e293b;
  background: #f8fafc;
  transition: all 0.2s ease;

  &:focus {
    outline: none;
    border-color: #1e3c72;
    background: white;
    box-shadow: 0 0 0 4px rgba(30, 60, 114, 0.1);
  }

  &::placeholder { color: #cbd5e1; }
`;

const Input = styled.input`${CommonInputStyles}`;
const Select = styled.select`${CommonInputStyles} cursor: pointer;`;
const TextArea = styled.textarea`${CommonInputStyles} min-height: 100px; resize: vertical;`;

const FormRow = styled.div`
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  
  @media (min-width: 640px) {
    grid-template-columns: 1fr 1fr;
  }
`;

const FileUploadZone = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  border: 2px dashed #e2e8f0;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #f8fafc;

  &:hover {
    border-color: #1e3c72;
    background: #f1f5f9;
  }

  svg {
    font-size: 32px;
    color: #94a3b8;
    margin-bottom: 8px;
  }

  span {
    font-size: 0.9rem;
    color: #64748b;
    font-weight: 500;
    text-align: center;
  }

  input { display: none; }
`;

const ImageList = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
`;

const ImageItem = styled.div`
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  cursor: grab;
  
  &:active {
    cursor: grabbing;
  }
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .actions {
    position: absolute;
    top: 4px;
    right: 4px;
    display: flex;
    gap: 4px;
    opacity: 0;
    transition: opacity 0.2s;
  }
  
  &:hover .actions {
    opacity: 1;
  }
`;

const DeleteBtn = styled.button`
  background: rgba(0,0,0,0.6);
  border: none;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    background: #ef4444;
  }
`;

const DragHandle = styled.div`
  position: absolute;
  top: 4px;
  left: 4px;
  background: rgba(0,0,0,0.6);
  border-radius: 4px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: grab;
  
  &:active {
    cursor: grabbing;
  }
`;

const ActionButtons = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 10px;
  padding-top: 20px;
  border-top: 1px solid #f1f5f9;
`;

const Button = styled.button`
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;

  ${({ $primary }) => $primary ? `
    background: #1e3c72;
    color: white;
    border: none;
    box-shadow: 0 4px 12px rgba(30, 60, 114, 0.2);
    &:hover { background: #2a5298; transform: translateY(-2px); }
  ` : `
    background: white;
    color: #64748b;
    border: 1px solid #e2e8f0;
    &:hover { background: #f8fafc; }
  `}
  
  ${({ $danger }) => $danger && `
    background: #fee2e2;
    color: #dc2626;
    border-color: #fecaca;
    &:hover { background: #fecaca; }
  `}
`;

export const CertificateForm = ({ isOpen, onClose, onSubmit, initialData = null }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    issued_by: '',
    issue_date: '',
    expiration_date: '',
    certificate_type: CERTIFICATE_TYPES.FOOD_SAFETY,
  });

  const [selectedFiles, setSelectedFiles] = useState([]);
  const [previewUrls, setPreviewUrls] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState(null);
  const [existingAttachments, setExistingAttachments] = useState([]);
  const [reorderChanged, setReorderChanged] = useState(false); // ✅ Thêm state để track thay đổi thứ tự

  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setFormData({
          name: initialData.name || '',
          description: initialData.description || '',
          issued_by: initialData.issued_by || '',
          issue_date: initialData.issue_date ? initialData.issue_date.slice(0, 10) : '',
          expiration_date: initialData.expiration_date ? initialData.expiration_date.slice(0, 10) : '',
          certificate_type: initialData.certificate_type || CERTIFICATE_TYPES.FOOD_SAFETY,
        });
        
        const attachments = initialData.attachments || [];
        setExistingAttachments(attachments);
        setPreviewUrls(attachments.map(att => att.public_url));
        setSelectedFiles(attachments);
        setReorderChanged(false); // ✅ Reset reorder flag
      } else {
        setFormData({
          name: '', description: '', issued_by: '', issue_date: '', expiration_date: '',
          certificate_type: CERTIFICATE_TYPES.FOOD_SAFETY,
        });
        setExistingAttachments([]);
        setPreviewUrls([]);
        setSelectedFiles([]);
        setReorderChanged(false);
      }
    }
  }, [isOpen, initialData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    const newPreviewUrls = files.map(file => URL.createObjectURL(file));
    
    setSelectedFiles(prev => [...prev, ...files]);
    setPreviewUrls(prev => [...prev, ...newPreviewUrls]);
  };

  const handleRemoveFile = async (index) => {
    const fileToRemove = selectedFiles[index];
    
    if (fileToRemove.uid && initialData) {
      try {
        await certificateService.removeCertificateAttachment(initialData.uid, fileToRemove.uid);
      } catch (error) {
        console.error('Failed to remove attachment:', error);
        alert('Failed to remove image: ' + error.message);
        return;
      }
    }
    
    const newFiles = [...selectedFiles];
    const newUrls = [...previewUrls];
    
    URL.revokeObjectURL(newUrls[index]);
    
    newFiles.splice(index, 1);
    newUrls.splice(index, 1);
    
    setSelectedFiles(newFiles);
    setPreviewUrls(newUrls);
    
    if (fileToRemove.uid) {
      setExistingAttachments(prev => prev.filter(att => att.uid !== fileToRemove.uid));
    }
  };

  const handleDragStart = (e, index) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  // ✅ SỬA: Chỉ cập nhật UI, KHÔNG gọi API reorder
  const handleDrop = (e, dropIndex) => {
    e.preventDefault();
    if (draggedIndex === null) return;

    const newFiles = [...selectedFiles];
    const newUrls = [...previewUrls];
    
    const [draggedFile] = newFiles.splice(draggedIndex, 1);
    const [draggedUrl] = newUrls.splice(draggedIndex, 1);
    
    newFiles.splice(dropIndex, 0, draggedFile);
    newUrls.splice(dropIndex, 0, draggedUrl);
    
    setSelectedFiles(newFiles);
    setPreviewUrls(newUrls);
    setDraggedIndex(null);
    
    // ✅ Đánh dấu là đã thay đổi thứ tự, sẽ gọi reorder khi save
    setReorderChanged(true);
  };

  // ✅ SỬA: Gọi reorder khi bấm Save
  const handleSubmit = async (e) => {
    e.preventDefault();
    setUploading(true);
    
    try {
      // 1. Nếu có thay đổi thứ tự, gọi API reorder trước
      if (isEdit && reorderChanged && existingAttachments.length > 0) {
        const existingUids = selectedFiles
          .filter(f => f.uid)
          .map((f, idx) => f.uid);
        
        if (existingUids.length > 0) {
          console.log('📤 Reordering attachments:', existingUids);
          await certificateService.reorderCertificateAttachments(initialData.uid, existingUids);
        }
      }
      
      // 2. Upload những file mới
      const attachmentUids = [...existingAttachments.map(a => a.uid)];
      
      for (const file of selectedFiles) {
        if (!file.uid) {
          const result = await attachmentService.uploadCertificate(file);
          attachmentUids.push(result);
        }
      }
      
      // 3. Submit form
      await onSubmit({ ...formData, attachment_uids: attachmentUids });
      
      setUploading(false);
      onClose();
    } catch (error) {
      console.error('Submit failed:', error);
      alert(`Submission failed: ${error.message}`);
      setUploading(false);
    }
  };

  const isEdit = !!initialData;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? 'Update Certificate' : 'Add New Certificate'}
      size="large"
    >
      <Form onSubmit={handleSubmit}>
        <FormRow>
          <FormGroup>
            <Label>Certificate Name <span>*</span></Label>
            <Input 
              name="name" 
              value={formData.name} 
              onChange={handleChange} 
              required 
              placeholder="e.g., Food Safety Level 1" 
            />
          </FormGroup>

          <FormGroup>
            <Label>Certificate Type <span>*</span></Label>
            <Select name="certificate_type" value={formData.certificate_type} onChange={handleChange} required>
              <option value={CERTIFICATE_TYPES.FOOD_SAFETY}>Food Safety</option>
              <option value={CERTIFICATE_TYPES.BUSINESS_LICENSE}>Business License</option>
            </Select>
          </FormGroup>
        </FormRow>

        <FormGroup>
          <Label>Detailed Description</Label>
          <TextArea 
            name="description" 
            value={formData.description} 
            onChange={handleChange} 
            placeholder="Provide additional details or notes about this certificate..." 
          />
        </FormGroup>

        <FormRow>
          <FormGroup>
            <Label>Issued By <span>*</span></Label>
            <Input 
              name="issued_by" 
              value={formData.issued_by} 
              onChange={handleChange} 
              required 
              placeholder="Issuing authority or organization" 
            />
          </FormGroup>
          <FormGroup>
            <Label>Issue Date <span>*</span></Label>
            <Input type="date" name="issue_date" value={formData.issue_date} onChange={handleChange} required />
          </FormGroup>
        </FormRow>

        <FormRow>
          <FormGroup>
            <Label>Expiration Date</Label>
            <Input type="date" name="expiration_date" value={formData.expiration_date} onChange={handleChange} />
          </FormGroup>
          <FormGroup>
            <Label>Certificate Images</Label>
            <FileUploadZone onClick={() => document.getElementById('fileInput').click()}>
              <MdCloudUpload />
              <span>Click to add more images</span>
              <input 
                id="fileInput"
                type="file" 
                onChange={handleFileSelect} 
                accept=".jpg,.jpeg,.png" 
                multiple
                style={{ display: 'none' }}
              />
            </FileUploadZone>
            
            {previewUrls.length > 0 && (
              <ImageList>
                {previewUrls.map((url, index) => (
                  <ImageItem 
                    key={index}
                    draggable={!!selectedFiles[index]?.uid}
                    onDragStart={(e) => handleDragStart(e, index)}
                    onDragOver={handleDragOver}
                    onDrop={(e) => handleDrop(e, index)}
                  >
                    {selectedFiles[index]?.uid && (
                      <DragHandle>
                        <MdDragHandle size={16} />
                      </DragHandle>
                    )}
                    <img src={url} alt={`Preview ${index + 1}`} />
                    <div className="actions">
                      <DeleteBtn type="button" onClick={() => handleRemoveFile(index)}>
                        <MdDelete size={14} />
                      </DeleteBtn>
                    </div>
                  </ImageItem>
                ))}
              </ImageList>
            )}
            {isEdit && previewUrls.length > 0 && (
              <p style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: 8 }}>
                    💡 Drag and drop to reorder images (Only reorders existing images, new images will be added at the end. Changes saved when you click Save)
              </p>
            )}
          </FormGroup>
        </FormRow>

        <ActionButtons>
          <Button type="button" onClick={onClose}>Cancel</Button>
          <Button type="submit" $primary disabled={uploading}>
            {uploading ? 'Uploading...' : (isEdit ? 'Save Changes' : 'Create Certificate')}
          </Button>
        </ActionButtons>
      </Form>
    </Modal>
  );
};