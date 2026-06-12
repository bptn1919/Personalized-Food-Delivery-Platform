import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useNavigate, useLocation } from 'react-router-dom';
import { MdLock, MdError, MdCheckCircle, MdArrowBack } from 'react-icons/md';
import authService from '../services/authService';

// --- Styled Components ---

const Container = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
`;

const Card = styled.div`
  background: white;
  border-radius: 20px;
  padding: 48px 40px;
  width: 90%;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.6s cubic-bezier(0.23, 1, 0.32, 1);

  @keyframes slideUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 800;
  color: #1e3c72;
  text-align: center;
  margin-bottom: 8px;
`;

const Subtitle = styled.p`
  text-align: center;
  color: #64748b;
  margin-bottom: 32px;
  font-size: 0.95rem;
`;

const Alert = styled.div`
  padding: 12px 16px;
  border-radius: 12px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.875rem;
  border-left: 4px solid;
`;

const ErrorAlert = styled(Alert)`
  background: #fef2f2;
  color: #991b1b;
  border-color: #ef4444;
`;

const SuccessAlert = styled(Alert)`
  background: #f0fdf4;
  color: #166534;
  border-color: #22c55e;
`;

const InputWrapper = styled.div`
  position: relative;
  margin-bottom: 16px;
`;

const IconContainer = styled.span`
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  display: flex;
  font-size: 1.25rem;
`;

const StyledInput = styled.input`
  width: 100%;
  padding: 14px 14px 14px 44px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 1rem;
  background: #f8fafc;
  transition: all 0.2s;
  box-sizing: border-box;

  &:focus {
    outline: none;
    border-color: #3b82f6;
    background: white;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  &:disabled { background: #f1f5f9; cursor: not-allowed; }
`;

const StrengthMeter = styled.div`
  height: 4px;
  width: 100%;
  background: #e2e8f0;
  border-radius: 2px;
  margin: -8px 0 20px 0;
  position: relative;
  overflow: hidden;

  &::after {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    transition: all 0.3s ease;
    width: ${({ $strength }) => {
      if ($strength === 'weak') return '33%';
      if ($strength === 'medium') return '66%';
      if ($strength === 'strong') return '100%';
      return '0%';
    }};
    background: ${({ $strength }) => {
      if ($strength === 'weak') return '#ef4444';
      if ($strength === 'medium') return '#f59e0b';
      if ($strength === 'strong') return '#22c55e';
      return 'transparent';
    }};
  }
`;

const PrimaryButton = styled.button`
  width: 100%;
  background: #1e3c72;
  color: white;
  padding: 14px;
  border-radius: 12px;
  border: none;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 12px;

  &:hover:not(:disabled) {
    background: #162e5a;
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(30, 60, 114, 0.2);
  }

  &:disabled { opacity: 0.6; cursor: not-allowed; }
`;

const BackLink = styled.button`
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 0.875rem;
  cursor: pointer;
  width: 100%;
  margin-top: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;

  &:hover { color: #64748b; }
`;

const Spinner = styled.div`
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  display: inline-block;
  margin-right: 10px;
  @keyframes spin { to { transform: rotate(360deg); } }
`;

// --- Component ---

const ResetPassword = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { resetSessionToken } = location.state || {};
  
  const [formData, setFormData] = useState({ newPassword: '', confirmPassword: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!resetSessionToken) navigate('/forgot-password');
  }, [resetSessionToken, navigate]);

  const getStrength = (pwd) => {
    if (!pwd) return '';
    if (pwd.length < 6) return 'weak';
    if (pwd.length >= 8 && /[A-Z]/.test(pwd) && /[0-9]/.test(pwd)) return 'strong';
    return 'medium';
  };

  const strength = getStrength(formData.newPassword);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.newPassword !== formData.confirmPassword) return setError('Passwords do not match');
    if (formData.newPassword.length < 8) return setError('Security requirement: Minimum 8 characters');

    setLoading(true);
    setError('');

    try {
      const response = await authService.resetPassword(resetSessionToken, formData.newPassword, formData.confirmPassword);
      
      const isOk = response === true || response?.data === true || 
                   response?.message_code === 'SUCCESS' || 
                   response?.data?.message_code === 'SUCCESS';

      if (isOk) {
        setSuccess('Account secured! Redirecting to login...');
        setTimeout(() => navigate('/login'), 2500);
      } else {
        setError('Verification failed. Please request a new link.');
      }
    } catch (err) {
      setError(err.status === 403 ? 'Session expired. Please restart the process.' : (err.message || 'Error updating password'));
    } finally {
      setLoading(false);
    }
  };

  if (!resetSessionToken) return null;

  return (
    <Container>
      <Card>
        <Title>Create Password</Title>
        <Subtitle>Secure your account with a new password</Subtitle>
        
        {error && <ErrorAlert><MdError size={20}/>{error}</ErrorAlert>}
        {success && <SuccessAlert><MdCheckCircle size={20}/>{success}</SuccessAlert>}
        
        <form onSubmit={handleSubmit}>
          <InputWrapper>
            <IconContainer><MdLock /></IconContainer>
            <StyledInput
              type="password"
              placeholder="New Password"
              value={formData.newPassword}
              onChange={(e) => setFormData({...formData, newPassword: e.target.value})}
              disabled={loading || !!success}
              autoComplete="new-password"
            />
          </InputWrapper>
          
          <StrengthMeter $strength={strength} />

          <InputWrapper>
            <IconContainer><MdLock /></IconContainer>
            <StyledInput
              type="password"
              placeholder="Confirm New Password"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
              disabled={loading || !!success}
              autoComplete="new-password"
            />
          </InputWrapper>

          <PrimaryButton type="submit" disabled={loading || !!success}>
            {loading ? <><Spinner /> Updating...</> : 'Save Password'}
          </PrimaryButton>

          <BackLink type="button" onClick={() => navigate('/login')} disabled={!!success}>
            <MdArrowBack /> Cancel and return
          </BackLink>
        </form>
      </Card>
    </Container>
  );
};

export default ResetPassword;