import React, { useState } from 'react';
import styled from 'styled-components';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';

const LayoutContainer = styled.div`
  display: flex;
  min-height: 100vh;
  background-color: #f8fafc; /* Màu nền Slate nhẹ nhàng, hiện đại */
`;

const Main = styled.main`
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0; // Tránh lỗi overflow trong flexbox
  
  /* Tính toán padding dựa trên chiều cao Header (70px) và chiều rộng Sidebar */
  padding-top: 70px; 
  
  /* Desktop: Padding trái thay đổi theo trạng thái Sidebar */
  padding-left: ${({ $sidebarOpen }) => ($sidebarOpen ? '260px' : '80px')};
  padding-right: 24px;
  padding-bottom: 24px;
  
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  /* Nội dung bên trong Main */
  .content-wrapper {
    max-width: 1400px;
    margin: 0 auto;
    width: 100%;
    padding-top: 24px;
  }

  @media (max-width: 768px) {
    padding-left: 16px;
    padding-right: 16px;
  }
`;

const Layout = ({ isChef }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  // Log để debug khi cần thiết
  // console.log('🔷 Layout rendered with isChef:', isChef);

  return (
    <LayoutContainer>
      {/* Truyền props vào Header và Sidebar */}
      <Header 
        open={sidebarOpen} 
        setOpen={setSidebarOpen} 
        isChef={isChef} 
      />
      
      <Sidebar 
        open={sidebarOpen} 
        isChef={isChef} 
      />
      
      <Main $sidebarOpen={sidebarOpen}>
        <div className="content-wrapper">
          <Outlet />
        </div>
      </Main>
    </LayoutContainer>
  );
};

export default Layout;