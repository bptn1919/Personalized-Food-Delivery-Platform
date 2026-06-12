// components/dishLocations/LocationTreeView.jsx
import React, { useState } from 'react';
import styled from 'styled-components';
import { MdEdit, MdDelete, MdExpandMore, MdChevronRight } from 'react-icons/md';

const TreeContainer = styled.div`
  margin-top: 16px;
`;

const TreeNodeWrapper = styled.div`
  margin-left: ${({ $level }) => $level * 28}px;
  margin-bottom: 8px;
`;

const TreeNodeContent = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;

  &:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
  }
`;

const NodeInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  cursor: ${({ $hasChildren }) => $hasChildren ? 'pointer' : 'default'};
`;

const NodeName = styled.span`
  font-weight: 600;
  color: #1e293b;
`;

const NodeType = styled.span`
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 12px;
  background: ${({ $type }) => {
    if ($type === 'REGION') return '#dcfce7';
    if ($type === 'SUBREGION') return '#fef3c7';
    return '#cffafe';
  }};
  color: ${({ $type }) => {
    if ($type === 'REGION') return '#166534';
    if ($type === 'SUBREGION') return '#92400e';
    return '#155e75';
  }};
`;

const NodeActions = styled.div`
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s;

  ${TreeNodeContent}:hover & {
    opacity: 1;
  }
`;

const ActionIcon = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;

  &:hover {
    background: #e2e8f0;
    color: ${({ $danger }) => $danger ? '#ef4444' : '#1e3c72'};
  }
`;

const ChildrenContainer = styled.div`
  margin-top: 8px;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 60px;
  color: #94a3b8;
`;

const TYPE_LABELS = {
  REGION: 'Region',
  SUBREGION: 'Subregion',
  COUNTRY: 'Country',
};

const TreeNode = ({ node, level = 0, onEdit, onDelete }) => {
  const [expanded, setExpanded] = useState(true);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <TreeNodeWrapper $level={level}>
      <TreeNodeContent>
        <NodeInfo $hasChildren={hasChildren} onClick={() => hasChildren && setExpanded(!expanded)}>
          {hasChildren && (
            <span style={{ width: 24 }}>
              {expanded ? <MdExpandMore size={18} /> : <MdChevronRight size={18} />}
            </span>
          )}
          {!hasChildren && <span style={{ width: 24 }} />}
          <NodeName>{node.name}</NodeName>
          <NodeType $type={node.type}>{TYPE_LABELS[node.type]}</NodeType>
        </NodeInfo>
        <NodeActions>
          <ActionIcon onClick={() => onEdit(node)} title="Edit">
            <MdEdit size={16} />
          </ActionIcon>
          <ActionIcon $danger onClick={() => onDelete(node)} title="Delete">
            <MdDelete size={16} />
          </ActionIcon>
        </NodeActions>
      </TreeNodeContent>
      {hasChildren && expanded && (
        <ChildrenContainer>
          {node.children.map(child => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </ChildrenContainer>
      )}
    </TreeNodeWrapper>
  );
};

export const LocationTreeView = ({ locations, onEdit, onDelete }) => {
  if (!locations || locations.length === 0) {
    return <EmptyState>No locations yet. Click "New Location" to create your first location.</EmptyState>;
  }

  return (
    <TreeContainer>
      {locations.map(location => (
        <TreeNode
          key={location.id}
          node={location}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </TreeContainer>
  );
};

export default LocationTreeView;