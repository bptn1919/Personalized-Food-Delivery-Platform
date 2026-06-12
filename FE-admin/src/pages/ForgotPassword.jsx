import React, { useState } from 'react';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';
import { MdEmail, MdError, MdArrowBack, MdCheckCircle } from 'react-icons/md';
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
  border-radius: 16px;
  padding: 40px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  animation: fadeInSlide 0.5s ease-out;

  @keyframes fadeInSlide {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;

const Title = styled.h1`
  font-size: 1.75rem;
  font-weight: 700;
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
`;

const Alert = styled.div`
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.9rem;
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

const InputGroup = styled.div`
  position: relative;
  margin-bottom: 20px;
`;

const InputIcon = styled.span`
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  display: flex;
  font-size: 1.2rem;
`;

const Input = styled.input`
  width: 100%;
  padding: 14px 14px 14px 44px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 1rem;
  transition: all 0.2s;
  box-sizing: border-box;

  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  &:disabled { background: #f8fafc; cursor: not-allowed; }
`;

const MainButton = styled.button`
  width: 100%;
  background: #1e3c72;
  color: white;
  padding: 14px;
  border-radius: 10px;
  border: none;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    background: #162e5a;
    box-shadow: 0 4px 12px rgba(30, 60, 114, 0.2);
  }

  &:disabled { opacity: 0.7; cursor: not-allowed; }
`;

const BackLink = styled.button`
  background: none;
  border: none;
  color: #64748b;
  font-size: 0.9rem;
  cursor: pointer;
  width: 100%;
  margin-top: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;

  &:hover { color: #1e3c72; }
`;

const Spinner = styled.div`
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  display: inline-block;
  margin-right: 8px;

  @keyframes spin { to { transform: rotate(360deg); } }
`;

// --- Component ---

const ForgotPassword = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const validateEmail = (email) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!email) return setError('Please enter your email address');
    if (!validateEmail(email)) return setError('Please enter a valid email');

    setLoading(true);

    try {
      const response = await authService.forgotPassword(email);
      
      // Standardize token retrieval from various possible API responses
      const token = response?.data?.reset_session_token || 
                    response?.reset_session_token || 
                    response?.data?.data?.reset_session_token;

      if (token) {
        navigate('/verify-otp', { state: { email, resetSessionToken: token } });
      } else {
        setSuccess('Reset instructions sent! Please check your inbox.');
      }
    } catch (err) {
      const msg = err.message_code === 'USER_NOT_FOUND' || err.status === 404
        ? 'Email not registered in our system'
        : err.message || 'Server error. Please try again later.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container>
      <Card>
        <Title>Reset Password</Title>
        <Subtitle>We'll send you an OTP code to verify your identity</Subtitle>
        
        {error && (
          <ErrorAlert>
            <MdError size={20} />
            {error}
          </ErrorAlert>
        )}
        
        {success && (
          <SuccessAlert>
            <MdCheckCircle size={20} />
            {success}
          </SuccessAlert>
        )}
        
        <form onSubmit={handleSubmit}>
          <InputGroup>
            <InputIcon><MdEmail /></InputIcon>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              disabled={loading}
              autoComplete="email"
            />
          </InputGroup>

          <MainButton type="submit" disabled={loading}>
            {loading ? <><Spinner /> Sending...</> : 'Send Verification Code'}
          </MainButton>

          <BackLink type="button" onClick={() => navigate('/login')}>
            <MdArrowBack /> Back to Sign In
          </BackLink>
        </form>
      </Card>
    </Container>
  );
};

export default ForgotPassword;