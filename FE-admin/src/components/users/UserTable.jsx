import React from 'react';
import styled from 'styled-components';
import { 
  MdBlock, MdCheckCircle, MdPersonOutline
} from 'react-icons/md';
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '../common/Table';
import { StatusBadge } from '../common/StatusBadge';
import { Avatar } from '../common/Avatar';

// --- Styled Components ---

const UserProfile = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const UsernameText = styled.span`
  font-weight: 700;
  color: #1e3c72;
  font-size: 0.9rem;
`;

const RoleBadge = styled.span`
  display: inline-block;
  padding: 4px 10px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-radius: 6px;
  
  background: ${({ $role }) => 
    $role === 'admin' ? '#eff6ff' : 
    $role === 'chef' ? '#fff7ed' : 
    '#f0fdf4'};
    
  color: ${({ $role }) => 
    $role === 'admin' ? '#1d4ed8' : 
    $role === 'chef' ? '#c2410c' : 
    '#15803d'};
`;

const ActionGroup = styled.div`
  display: flex;
  gap: 8px;
  justify-content: center;
`;

const ActionButton = styled.button`
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 10px;
  background: #f8fafc;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 1.1rem;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }

  ${({ $variant }) => $variant === 'danger' && `
    &:hover { background: #fee2e2; color: #ef4444; }
  `}

  ${({ $variant }) => $variant === 'success' && `
    &:hover { background: #dcfce7; color: #10b981; }
  `}
`;

const UserId = styled.span`
  font-family: 'JetBrains Mono', monospace;
  color: #94a3b8;
  font-weight: 600;
`;

// --- Helpers ---

const formatDate = (dateString) => {
  if (!dateString) return '---';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

/**
 * UserTable Component
 * Optimized for administrative account management and role oversight.
 */
export const UserTable = ({ 
  users = [], 
  onSort, 
  sortConfig, 
  onToggleStatus 
}) => {

  const getUserRole = (user) => {
    if (user.groups?.includes('CHEF')) return 'chef';
    if (user.is_staff) return 'admin';
    return 'customer';
  };

  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell sortable onClick={() => onSort('id')} width="100px">
            ID
          </TableHeaderCell>
          <TableHeaderCell sortable onClick={() => onSort('username')}>
            Account User
          </TableHeaderCell>
          <TableHeaderCell>Email Address</TableHeaderCell>
          <TableHeaderCell>Full Name</TableHeaderCell>
          <TableHeaderCell>Role</TableHeaderCell>
          <TableHeaderCell sortable onClick={() => onSort('is_active')}>
            Status
          </TableHeaderCell>
          <TableHeaderCell sortable onClick={() => onSort('date_joined')}>
            Joined
          </TableHeaderCell>
          <TableHeaderCell align="center">Access Control</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {users.map((user) => {
          const role = getUserRole(user);
          
          return (
            <TableRow key={user.id}>
              <TableCell>
                <UserId>#{user.id.toString().padStart(4, '0')}</UserId>
              </TableCell>
              
              <TableCell>
                <UserProfile>
                  <Avatar 
                    name={user.username}
                    size="32px"
                    variant="soft" 
                  />
                  <UsernameText>{user.username}</UsernameText>
                </UserProfile>
              </TableCell>
              
              <TableCell style={{ color: '#64748b' }}>{user.email}</TableCell>
              
              <TableCell>
                {user.first_name || user.last_name 
                  ? `${user.first_name} ${user.last_name}`.trim() 
                  : <span style={{ color: '#cbd5e1' }}>Not Provided</span>}
              </TableCell>
              
              <TableCell>
                <RoleBadge $role={role}>{role}</RoleBadge>
              </TableCell>
              
              <TableCell>
                <StatusBadge status={user.is_active ? 'active' : 'inactive'}>
                  {user.is_active ? 'Active' : 'Suspended'}
                </StatusBadge>
              </TableCell>
              
              <TableCell style={{ fontSize: '0.85rem', color: '#64748b' }}>
                {formatDate(user.date_joined)}
              </TableCell>
              
              <TableCell>
                <ActionGroup>
                  {user.is_active ? (
                    <ActionButton 
                      $variant="danger" 
                      onClick={() => onToggleStatus(user, 'deactivate')} 
                      title="Suspend User Access"
                    >
                      <MdBlock />
                    </ActionButton>
                  ) : (
                    <ActionButton 
                      $variant="success" 
                      onClick={() => onToggleStatus(user, 'activate')} 
                      title="Restore User Access"
                    >
                      <MdCheckCircle />
                    </ActionButton>
                  )}
                </ActionGroup>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
};