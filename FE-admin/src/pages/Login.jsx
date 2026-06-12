import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';
import { MdLock, MdError, MdEmail } from 'react-icons/md';
import authService from '../services/authService';

// --- Styled Components ---

const Container = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
`;

const LoginCard = styled.div`
  background: white;
  border-radius: 20px;
  padding: 48px 40px;
  width: 90%;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideIn 0.6s cubic-bezier(0.23, 1, 0.32, 1);

  @keyframes slideIn {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;

const Title = styled.h1`
  font-size: 2.25rem;
  font-weight: 800;
  color: #1e3c72;
  text-align: center;
  margin-bottom: 8px;
  letter-spacing: -0.02em;
`;

const Subtitle = styled.p`
  text-align: center;
  color: #64748b;
  margin-bottom: 32px;
  font-size: 0.95rem;
`;

const Alert = styled.div`
  background: #fef2f2;
  color: #991b1b;
  padding: 14px;
  border-radius: 12px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.875rem;
  border: 1px solid #fee2e2;
  font-weight: 500;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const InputWrapper = styled.div`
  position: relative;
`;

const IconLeft = styled.span`
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  font-size: 1.25rem;
  display: flex;
  pointer-events: none;
`;

const StyledInput = styled.input`
  width: 100%;
  padding: 14px 16px 14px 48px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1rem;
  color: #1e293b;
  background: #f8fafc;
  transition: all 0.2s ease;
  box-sizing: border-box;

  &:focus {
    outline: none;
    border-color: #3b82f6;
    background: white;
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
  }

  &::placeholder { color: #94a3b8; }
  &:disabled { opacity: 0.6; cursor: not-allowed; }
`;

const PrimaryButton = styled.button`
  background: #1e3c72;
  color: white;
  border: none;
  border-radius: 12px;
  padding: 16px;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  margin-top: 10px;

  &:hover:not(:disabled) {
    background: #162e5a;
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(30, 60, 114, 0.2);
  }

  &:active:not(:disabled) { transform: translateY(0); }
  &:disabled { opacity: 0.7; cursor: not-allowed; }
`;

const GhostLink = styled.button`
  background: none;
  border: none;
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  margin-top: 16px;
  width: 100%;
  transition: color 0.2s;

  &:hover { color: #1e3c72; text-decoration: underline; }
`;

const Spinner = styled.div`
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
  margin-right: 10px;
  display: inline-block;

  @keyframes spin { to { transform: rotate(360deg); } }
`;

// --- Component Logic ---

const Login = () => {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({ email: '', password: '' });

  useEffect(() => {
    // Check auth status on mount to prevent double-login
    if (authService.isAuthenticated()) {
      handleRoleRedirection();
    }
  }, []);

  const handleRoleRedirection = async () => {
    try {
      const { is_chef } = await authService.checkIsChef();
      console.log('Chef status--------------------------------:', is_chef);
      
      // Dispatch custom event to notify App.jsx BEFORE navigating!
      window.dispatchEvent(new CustomEvent('auth-change', {
        detail: {
          token: authService.getToken(),
          isChef: is_chef
        }
      }));

      navigate(is_chef ? '/chefcertificates' : '/dashboard', { replace: true });
    } catch (error) {
      console.error('Error redirecting role:', error);
      navigate('/login', { replace: true });
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (error) setError('');
  };

  const validate = () => {
    if (!formData.email || !formData.password) return 'Please enter both email and password';
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) return 'Invalid email format';
    return null;
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    const validationError = validate();
    if (validationError) return setError(validationError);

    setLoading(true);
    try {
      await authService.login(formData);
      await handleRoleRedirection();
    } catch (err) {
      const msg = err.status === 403 ? 'Invalid email or password' : (err.message || 'Server error. Please try again.');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container>
      <LoginCard>
        <Title>Sign In</Title>
        <Subtitle>Welcome back! Please enter your details.</Subtitle>
        
        {error && (
          <Alert role="alert">
            <MdError size={20} />
            {error}
          </Alert>
        )}
        
        <Form onSubmit={handleLogin}>
          <InputWrapper>
            <IconLeft><MdEmail /></IconLeft>
            <StyledInput
              type="email"
              name="email"
              placeholder="Email address"
              value={formData.email}
              onChange={handleChange}
              disabled={loading}
              autoComplete="email"
              aria-label="Email Address"
            />
          </InputWrapper>

          <InputWrapper>
            <IconLeft><MdLock /></IconLeft>
            <StyledInput
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              disabled={loading}
              autoComplete="current-password"
              aria-label="Password"
            />
          </InputWrapper>

          <PrimaryButton type="submit" disabled={loading}>
            {loading ? <><Spinner /> Authenticating...</> : 'Login'}
          </PrimaryButton>

          <GhostLink type="button" onClick={() => navigate('/forgot-password')}>
            Forgot password?
          </GhostLink>
        </Form>
      </LoginCard>
    </Container>
  );
};

export default Login;