import React from 'react';
import styled from 'styled-components';
import { NavLink } from 'react-router-dom';
import {
  MdDashboard,
  MdMoneyOff,
  MdPeople,
  MdShoppingBag,
  MdVerified,
  MdRestaurantMenu,
  MdMenuBook,
  MdChevronRight,
  MdScience,
  MdLocationOn,
  MdAccountBalance
} from 'react-icons/md';

const DRAWER_WIDTH = 260;
const MINI_WIDTH = 80;

const adminMenuItems = [
  { text: 'Dashboard', icon: <MdDashboard />, path: '/dashboard' },
  { text: 'Users', icon: <MdPeople />, path: '/users' },
  { text: 'Orders', icon: <MdShoppingBag />, path: '/orders' },
  { text: 'Certificates', icon: <MdVerified />, path: '/admincertificates' },
  { text: 'Vouchers', icon: <MdMoneyOff />, path: '/vouchers' },
  { text: 'Ingredients', icon: <MdScience />, path: '/ingredients' },
  { text: 'Bank Accounts', icon: <MdAccountBalance />, path: '/bank-accounts' },
  { text: 'Dish Locations', icon: < MdLocationOn />, path: '/dish-locations' },
];

const chefMenuItems = [
  { text: 'Certificates', icon: <MdVerified />, path: '/chefcertificates' },
  { text: 'Menus', icon: <MdMenuBook />, path: '/menus' },
  { text: 'Dishes', icon: <MdRestaurantMenu />, path: '/dishes' },
];

const SidebarContainer = styled.aside`
  width: ${({ $open }) => ($open ? `${DRAWER_WIDTH}px` : `${MINI_WIDTH}px`)};
  position: fixed;
  left: 0;
  top: 70px; // Khớp với chiều cao Header mới
  bottom: 0;
  background: white;
  border-right: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow-x: hidden;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.02);
`;

const Nav = styled.nav`
  padding: 16px 12px;
  flex: 1;
`;

const NavLabel = styled.div`
  padding: 0 16px 12px;
  font-size: 0.7rem;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 1px;
  display: ${({ $open }) => ($open ? 'block' : 'none')};
`;

const StyledNavLink = styled(NavLink)`
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  text-decoration: none;
  border-radius: 12px;
  color: #64748b;
  transition: all 0.3s ease;
  position: relative;
  white-space: nowrap;

  .icon {
    font-size: 1.4rem;
    min-width: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
  }

  .text {
    margin-left: 8px;
    font-size: 0.95rem;
    font-weight: 500;
    opacity: ${({ $open }) => ($open ? 1 : 0)};
    transition: opacity 0.3s ease;
  }

  .arrow {
    margin-left: auto;
    font-size: 1.1rem;
    opacity: ${({ $open }) => ($open ? 0.5 : 0)};
    transition: all 0.3s ease;
  }

  &:hover {
    background: #f1f5f9;
    color: #1e3c72;
    transform: translateX(4px);
  }

  &.active {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    color: white;
    box-shadow: 0 8px 16px rgba(30, 60, 114, 0.2);

    .icon { color: white; }
    .text { font-weight: 600; }
    .arrow { opacity: 1; transform: rotate(90deg); }

    /* Thanh chỉ thị bên cạnh */
    &::before {
      content: '';
      position: absolute;
      left: -12px;
      top: 20%;
      height: 60%;
      width: 4px;
      background: white;
      border-radius: 0 4px 4px 0;
    }
  }
`;

const SidebarFooter = styled.div`
  padding: 20px;
  border-top: 1px solid #f1f5f9;
  font-size: 0.75rem;
  color: #94a3b8;
  text-align: center;
  display: ${({ $open }) => ($open ? 'block' : 'none')};
`;

const Sidebar = ({ open, isChef }) => {
  const menuItems = isChef ? chefMenuItems : adminMenuItems;

  return (
    <SidebarContainer $open={open}>
      <Nav>        
        {menuItems.map((item) => (
          <StyledNavLink
            key={item.path}
            to={item.path}
            $open={open}
            end={item.path === '/dashboard'}
            title={!open ? item.text : ''} 
          >
            <div className="icon">{item.icon}</div>
            <span className="text">{item.text}</span>
            <div className="arrow">
              <MdChevronRight />
            </div>
          </StyledNavLink>
        ))}
      </Nav>

      <SidebarFooter $open={open}>
        © 2026 Amomeal System
      </SidebarFooter>
    </SidebarContainer>
  );
};

export default Sidebar;