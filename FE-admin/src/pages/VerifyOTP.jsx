import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useNavigate, useLocation } from 'react-router-dom';
import { MdLock, MdError, MdArrowBack, MdCheckCircle } from 'react-icons/md';
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
  line-height: 1.5;

  strong { color: #1e293b; }
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

const OTPInput = styled.input`
  width: 100%;
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1.5rem;
  text-align: center;
  letter-spacing: 12px;
  font-weight: 800;
  color: #1e3c72;
  background: #f8fafc;
  transition: all 0.2s;

  &:focus {
    outline: none;
    border-color: #3b82f6;
    background: white;
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
  }

  &::placeholder {
    letter-spacing: normal;
    font-size: 1rem;
    font-weight: 400;
    color: #cbd5e1;
  }
`;

const PrimaryButton = styled.button`
  width: 100%;
  background: #1e3c72;
  color: white;
  padding: 16px;
  border-radius: 12px;
  border: none;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 24px;

  &:hover:not(:disabled) {
    background: #162e5a;
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(30, 60, 114, 0.2);
  }

  &:disabled { opacity: 0.6; cursor: not-allowed; }
`;

const ResendContainer = styled.div`
  text-align: center;
  margin-top: 20px;
  font-size: 0.9rem;
  color: #64748b;
`;

const ResendButton = styled.button`
  background: none;
  border: none;
  color: #3b82f6;
  font-weight: 700;
  cursor: pointer;
  text-decoration: underline;
  padding: 0 4px;

  &:hover:not(:disabled) { color: #1e3c72; }
  &:disabled { color: #cbd5e1; cursor: not-allowed; text-decoration: none; }
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

// --- Component Logic ---

const VerifyOTP = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { email, resetSessionToken } = location.state || {};
  
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [resendTimer, setResendTimer] = useState(0);

  useEffect(() => {
    if (!resetSessionToken) {
      navigate('/forgot-password', { replace: true });
    }
  }, [resetSessionToken, navigate]);

  useEffect(() => {
    let interval;
    if (resendTimer > 0) {
      interval = setInterval(() => setResendTimer((prev) => prev - 1), 1000);
    }
    return () => clearInterval(interval);
  }, [resendTimer]);

  const handleOtpChange = (e) => {
    const val = e.target.value.replace(/\D/g, '').slice(0, 6);
    setOtp(val);
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (otp.length < 4) return setError('Please enter the full verification code');

    setLoading(true);
    setError('');

    try {
      const response = await authService.verifyOTP(resetSessionToken, otp);
      
      // Standardize response validation
      const isValid = response === true || response?.data === true || 
                      response?.message_code === 'SUCCESS' || 
                      response?.data?.message_code === 'SUCCESS';

      if (isValid) {
        navigate('/reset-password', { state: { resetSessionToken } });
      } else {
        setError('The code you entered is incorrect');
      }
    } catch (err) {
      setError(err.status === 403 ? 'Code has expired or is invalid' : (err.message || 'Verification failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!email || resendTimer > 0) return;

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await authService.forgotPassword(email);
      setSuccess('A new code has been dispatched to your email.');
      setResendTimer(60); // 1-minute cooldown
    } catch (err) {
      setError('Could not resend code. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  if (!resetSessionToken) return null;

  return (
    <Container>
      <Card>
        <Title>Verify OTP</Title>
        <Subtitle>We've sent a security code to<br/><strong>{email}</strong></Subtitle>
        
        {error && <ErrorAlert><MdError size={20}/>{error}</ErrorAlert>}
        {success && <SuccessAlert><MdCheckCircle size={20}/>{success}</SuccessAlert>}
        
        <form onSubmit={handleSubmit}>
          <OTPInput
            type="text"
            inputMode="numeric"
            value={otp}
            onChange={handleOtpChange}
            placeholder="000000"
            disabled={loading}
            autoFocus
          />

          <PrimaryButton type="submit" disabled={loading || otp.length < 4}>
            {loading ? <><Spinner /> Verifying...</> : 'Confirm Code'}
          </PrimaryButton>

          <ResendContainer>
            Didn't receive a code?{' '}
            <ResendButton 
              type="button" 
              onClick={handleResend} 
              disabled={resendTimer > 0 || loading}
            >
              {resendTimer > 0 ? `Resend in ${resendTimer}s` : 'Resend Code'}
            </ResendButton>
          </ResendContainer>

          <BackLink type="button" onClick={() => navigate('/forgot-password')}>
            <MdArrowBack /> Request new email
          </BackLink>
        </form>
      </Card>
    </Container>
  );
};

export default VerifyOTP;