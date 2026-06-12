import React, { useState, useEffect, useRef } from 'react';
import styled, { keyframes } from 'styled-components';
import { MdNotifications, MdWarning, MdClose, MdCheckCircle, MdError } from 'react-icons/md';

// --- Animations ---
const slideDown = keyframes`
  from { opacity: 0; transform: translateY(-10px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
`;

const pulse = keyframes`
  0% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(220, 53, 69, 0); }
  100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); }
`;

// --- Styled Components ---
const NotificationContainer = styled.div`
  position: relative;
`;

const IconButton = styled.button`
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  font-size: 22px;
  cursor: pointer;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;

  &:hover {
    background-color: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
  }
`;

const Badge = styled.span`
  position: absolute;
  top: -2px;
  right: -2px;
  background: #ff4d4f;
  color: white;
  font-size: 0.65rem;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
  border: 2px solid #1e3c72; // Trùng màu nền Header
  font-weight: 700;
  animation: ${pulse} 2s infinite;
`;

const Dropdown = styled.div`
  position: absolute;
  top: calc(100% + 12px);
  right: -10px;
  width: 350px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  z-index: 1200;
  overflow: hidden;
  display: ${({ $show }) => $show ? 'block' : 'none'};
  transform-origin: top right;
  animation: ${slideDown} 0.3s cubic-bezier(0.16, 1, 0.3, 1);

  &::before {
    content: '';
    position: absolute;
    top: -6px;
    right: 20px;
    width: 12px;
    height: 12px;
    background: white;
    transform: rotate(45deg);
  }
`;

const DropdownHeader = styled.div`
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;

  h4 {
    margin: 0;
    color: #1e293b;
    font-size: 1rem;
    font-weight: 700;
  }

  button {
    background: none;
    border: none;
    color: #2575fc;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 6px;
    &:hover { background: #f0f7ff; }
  }
`;

const NotificationList = styled.div`
  max-height: 400px;
  overflow-y: auto;

  &::-webkit-scrollbar { width: 5px; }
  &::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }
`;

const NotificationItem = styled.div`
  padding: 16px 20px;
  border-bottom: 1px solid #f8fafc;
  display: flex;
  gap: 12px;
  background: ${({ $read }) => $read ? 'white' : '#f0f9ff'};
  cursor: pointer;
  transition: all 0.2s;
  position: relative;

  &:hover {
    background: #f8fafc;
    & .close-btn { opacity: 1; }
  }
`;

const IconBox = styled.div`
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  
  background: ${({ $type }) => {
    switch($type) {
      case 'warning': return '#fff7ed';
      case 'success': return '#f0fdf4';
      case 'error': return '#fef2f2';
      default: return '#eff6ff';
    }
  }};
  
  color: ${({ $type }) => {
    switch($type) {
      case 'warning': return '#f97316';
      case 'success': return '#22c55e';
      case 'error': return '#ef4444';
      default: return '#3b82f6';
    }
  }};
`;

const Content = styled.div`
  flex: 1;
  min-width: 0;

  .msg {
    color: #334155;
    font-size: 0.875rem;
    line-height: 1.4;
    margin-bottom: 4px;
    font-weight: ${({ $read }) => $read ? '400' : '600'};
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .time {
    color: #94a3b8;
    font-size: 0.75rem;
  }
`;

const ItemCloseBtn = styled.button`
  position: absolute;
  top: 12px;
  right: 12px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #94a3b8;
  cursor: pointer;
  padding: 2px;
  display: flex;
  opacity: 0;
  transition: all 0.2s;

  &:hover { color: #ef4444; border-color: #fecaca; }
`;

const Empty = styled.div`
  padding: 40px 20px;
  text-align: center;
  color: #94a3b8;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  svg { font-size: 40px; opacity: 0.3; }
`;

// --- Component Logic ---
export const NotificationBadge = ({ notifications = [], onMarkAsRead, onMarkAllRead, onClear }) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setShowDropdown(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const unreadCount = notifications.filter(n => !n.read).length;

  const renderIcon = (type) => {
    switch(type) {
      case 'warning': return <MdWarning />;
      case 'success': return <MdCheckCircle />;
      case 'error': return <MdError />;
      default: return <MdNotifications />;
    }
  };

  const formatTime = (ts) => {
    const diff = Math.floor((new Date() - new Date(ts)) / 60000);
    if (diff < 1) return 'Vừa xong';
    if (diff < 60) return `${diff} phút trước`;
    if (diff < 1440) return `${Math.floor(diff/60)} giờ trước`;
    return `${Math.floor(diff/1440)} ngày trước`;
  };

  return (
    <NotificationContainer ref={dropdownRef}>
      <IconButton onClick={() => setShowDropdown(!showDropdown)}>
        <MdNotifications />
        {unreadCount > 0 && <Badge>{unreadCount > 99 ? '99+' : unreadCount}</Badge>}
      </IconButton>

      <Dropdown $show={showDropdown}>
        <DropdownHeader>
          <h4>Thông báo</h4>
          {unreadCount > 0 && (
            <button onClick={onMarkAllRead}>Đọc tất cả</button>
          )}
        </DropdownHeader>

        <NotificationList>
          {notifications.length === 0 ? (
            <Empty>
              <MdNotifications />
              <p>Bạn không có thông báo mới</p>
            </Empty>
          ) : (
            notifications.map(notif => (
              <NotificationItem 
                key={notif.id} 
                $read={notif.read}
                onClick={() => onMarkAsRead?.(notif.id)}
              >
                <IconBox $type={notif.type}>
                  {renderIcon(notif.type)}
                </IconBox>
                <Content $read={notif.read}>
                  <div className="msg">{notif.message}</div>
                  <div className="time">{formatTime(notif.timestamp)}</div>
                </Content>
                <ItemCloseBtn 
                  className="close-btn"
                  onClick={(e) => { e.stopPropagation(); onClear?.(notif.id); }}
                >
                  <MdClose />
                </ItemCloseBtn>
              </NotificationItem>
            ))
          )}
        </NotificationList>
      </Dropdown>
    </NotificationContainer>
  );
};