import React from 'react';
import styled from 'styled-components';

const AvatarContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: ${({ $size }) => $size || '40px'};
  height: ${({ $size }) => $size || '40px'};
  border-radius: 50%;
  background: ${({ $color }) => $color};
  color: white;
  font-weight: 600;
  font-size: ${({ $fontSize }) => $fontSize || '0.9rem'};
  overflow: hidden;
  border: 2px solid #fff;
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
  transition: all 0.2s ease;

  &:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 14px rgba(0,0,0,0.15);
  }
`;

const AvatarImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
`;

const getColorFromName = (name = '') => {
  const colors = [
    'linear-gradient(135deg, #667eea, #764ba2)',
    'linear-gradient(135deg, #f093fb, #f5576c)',
    'linear-gradient(135deg, #4facfe, #00f2fe)',
    'linear-gradient(135deg, #43e97b, #38f9d7)',
    'linear-gradient(135deg, #fa709a, #fee140)',
  ];

  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }

  return colors[Math.abs(hash) % colors.length];
};

export const Avatar = ({ src, name, size, fontSize, color }) => {
  const getInitials = (name) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const bgColor = color || getColorFromName(name);

  if (src) {
    return (
      <AvatarContainer $size={size}>
        <AvatarImage src={src} alt={name} />
      </AvatarContainer>
    );
  }

  return (
    <AvatarContainer
      $size={size}
      $fontSize={fontSize}
      $color={bgColor}
    >
      {getInitials(name)}
    </AvatarContainer>
  );
};