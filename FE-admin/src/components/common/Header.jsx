import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { MdMenu, MdClose, MdChevronRight } from 'react-icons/md';
import { FaUserCircle, FaSignOutAlt, FaIdBadge, FaEnvelope } from 'react-icons/fa';
import { NotificationBadge } from './Notification';
import { useNavigate } from 'react-router-dom';
import authService from '../../services/authService';

// --- Styled Components ---
const HeaderContainer = styled.header`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 70px; // Tăng nhẹ chiều cao
  background: rgba(30, 60, 114, 0.95);
  backdrop-filter: blur(10px); // Hiệu ứng kính mờ
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
  z-index: 1100;
`;

const Toolbar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 24px;
  max-width: 1600px; // Rộng hơn cho màn hình lớn
  margin: 0 auto;
`;

const MenuButton = styled.button`
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    background-color: rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
  }
`;

const Title = styled.h1`
  flex: 1;
  margin-left: 20px;
  color: white;
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: -0.5px;
  background: linear-gradient(to right, #fff, #a5c9fd);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
`;

const Actions = styled.div`
  display: flex;
  gap: 12px;
  align-items: center;
`;

const AccountContainer = styled.div`
  position: relative;
`;

const UserAvatar = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid rgba(255, 255, 255, 0.2);

  &:hover {
    transform: scale(1.05);
    border-color: #fff;
    box-shadow: 0 0 15px rgba(37, 117, 252, 0.4);
  }
`;

const DropdownMenu = styled.div`
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  min-width: 260px;
  overflow: hidden;
  z-index: 1200;
  padding: 8px;
  transform-origin: top right;
  animation: popIn 0.25s cubic-bezier(0.68, -0.55, 0.265, 1.55);

  @keyframes popIn {
    from { opacity: 0; transform: scale(0.9) translateY(-10px); }
    to { opacity: 1; transform: scale(1) translateY(0); }
  }
`;

const UserInfo = styled.div`
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  margin-bottom: 8px;

  .name {
    font-weight: 700;
    color: #1e293b;
    font-size: 1rem;
    margin-bottom: 2px;
  }

  .email {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.8rem;
    color: #64748b;
  }
`;

const MenuItem = styled.button`
  width: 100%;
  padding: 12px 14px;
  background: transparent;
  border: none;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: ${({ $danger }) => ($danger ? '#ef4444' : '#475569')};
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  div { display: flex; align-items: center; gap: 12px; }

  &:hover {
    background: ${({ $danger }) => ($danger ? '#fef2f2' : '#f1f5f9')};
    color: ${({ $danger }) => ($danger ? '#dc2626' : '#1e3c72')};
    padding-left: 18px;
  }
`;

const Backdrop = styled.div`
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(4px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.3s ease;

  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
`;

const ModalContent = styled.div`
  background: white;
  border-radius: 24px;
  padding: 32px;
  width: 90%;
  max-width: 400px;
  text-align: center;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);

  .icon-box {
    width: 64px;
    height: 64px;
    background: #fef2f2;
    color: #ef4444;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    margin: 0 auto 20px;
  }

  h3 { font-size: 1.5rem; color: #1e293b; margin-bottom: 12px; }
  p { color: #64748b; line-height: 1.6; margin-bottom: 30px; }
`;

const ModalButton = styled.button`
  flex: 1;
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  ${({ $primary }) => $primary ? `
    background: #1e3c72;
    color: white;
    border: none;
    box-shadow: 0 4px 12px rgba(30, 60, 114, 0.3);
    &:hover { background: #2a5298; transform: translateY(-2px); }
  ` : `
    background: #f1f5f9;
    color: #475569;
    border: none;
    &:hover { background: #e2e8f0; }
  `}
`;

// --- Main Component ---
const Header = ({ open, setOpen, notifications = [], onMarkAsRead, onMarkAllRead, onClear, isChef: propIsChef }) => {
  const navigate = useNavigate();
  const [showDropdown, setShowDropdown] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [chefId, setChefId] = useState(null);
  const dropdownRef = useRef(null);

  const currentUser = authService.getCurrentUser();
  const getInitials = (name) => name ? name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2) : 'AD';

  useEffect(() => {
    const fetchChefId = async () => {
      if (propIsChef) {
        try {
          const result = await authService.checkIsChef();
          setChefId(result.chef_id);
        } catch (error) { console.error('Error:', error); }
      }
    };
    if (propIsChef) fetchChefId();
  }, [propIsChef]);

  useEffect(() => {
    const handleOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setShowDropdown(false);
    };
    document.addEventListener('mousedown', handleOutside);
    return () => document.removeEventListener('mousedown', handleOutside);
  }, []);

  const handleLogout = async () => {
    setLoading(true);
    try {
      await authService.logout();
      localStorage.clear();
      navigate('/login', { replace: true });
    } catch (error) {
      localStorage.clear();
      navigate('/login', { replace: true });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <HeaderContainer>
        <Toolbar>
          <MenuButton onClick={() => setOpen(!open)} $open={open}>
            {open ? <MdClose /> : <MdMenu />}
          </MenuButton>
          
          <Title>{propIsChef ? 'Chef Dashboard' : 'Admin Management'}</Title>
          
          <Actions>
            {/* <NotificationBadge 
              notifications={notifications}
              onMarkAsRead={onMarkAsRead}
              onMarkAllRead={onMarkAllRead}
              onClear={onClear}
            /> */}
            
            <AccountContainer ref={dropdownRef}>
              <UserAvatar onClick={() => setShowDropdown(!showDropdown)}>
                {getInitials(currentUser?.username)}
              </UserAvatar>
              
              {showDropdown && (
                <DropdownMenu>
                  <UserInfo>
                    <div className="name">{currentUser?.username || 'Administrator'}</div>
                    <div className="email"><FaEnvelope size={12}/> {currentUser?.email}</div>
                    {propIsChef && chefId && (
                      <div className="email" style={{color: '#ed6c02', marginTop: 4}}>
                        <FaIdBadge size={12}/> ID: {chefId}
                      </div>
                    )}
                  </UserInfo>
                
                  
                  <MenuItem $danger onClick={() => { setShowDropdown(false); setShowLogoutConfirm(true); }}>
                    <div><FaSignOutAlt /> Sign Out</div>
                  </MenuItem>
                </DropdownMenu>
              )}
            </AccountContainer>
          </Actions>
        </Toolbar>
      </HeaderContainer>

      {showLogoutConfirm && (
        <Backdrop onClick={() => setShowLogoutConfirm(false)}>
          <ModalContent onClick={e => e.stopPropagation()}>
            <div className="icon-box"><FaSignOutAlt /></div>
            <h3>Ready to leave?</h3>
            <p>Are you sure you want to log out? You will need to sign in again to access your dashboard.</p>
            <div style={{display: 'flex', gap: 16}}>
              <ModalButton onClick={() => setShowLogoutConfirm(false)}>Stay here</ModalButton>
              <ModalButton $primary onClick={handleLogout} disabled={loading}>
                {loading ? 'Signing out...' : 'Yes, Sign out'}
              </ModalButton>
            </div>
          </ModalContent>
        </Backdrop>
      )}
    </>
  );
};

export default Header;