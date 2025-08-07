import React from 'react';
import { Badge, Tooltip, Space } from 'antd';
import { WifiOutlined, DisconnectOutlined, LoadingOutlined } from '@ant-design/icons';
import { useConnectionIndicator } from '../hooks/useWebSocket';
import './ConnectionIndicator.css';

const ConnectionIndicator: React.FC = () => {
  const { showIndicator, isConnected, connectionState, color, text } = useConnectionIndicator();

  if (!showIndicator && isConnected) {
    return null;
  }

  const getIcon = () => {
    switch (connectionState) {
      case 'OPEN':
        return <WifiOutlined />;
      case 'CONNECTING':
        return <LoadingOutlined spin />;
      case 'CLOSING':
      case 'CLOSED':
        return <DisconnectOutlined />;
      default:
        return <DisconnectOutlined />;
    }
  };

  return (
    <div className="connection-indicator">
      <Tooltip title={`Real-time connection: ${text}`}>
        <Space size="small">
          <Badge 
            status={isConnected ? "success" : connectionState === 'CONNECTING' ? "processing" : "error"} 
          />
          <span style={{ color }}>{getIcon()}</span>
          <span className="connection-text" style={{ color }}>{text}</span>
        </Space>
      </Tooltip>
    </div>
  );
};

export default ConnectionIndicator;