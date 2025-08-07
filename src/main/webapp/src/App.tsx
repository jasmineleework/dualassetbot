import React, { useState, useEffect } from 'react';
import { ConfigProvider, Layout, Typography, Menu, notification } from 'antd';
import { 
  DashboardOutlined, 
  LineChartOutlined, 
  SettingOutlined,
  RobotOutlined,
  ThunderboltOutlined,
  WalletOutlined,
  PlayCircleOutlined,
  MonitorOutlined,
  FileTextOutlined,
  CommentOutlined
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import AIRecommendations from './pages/AIRecommendations';
import Portfolio from './pages/Portfolio';
import AutoTrading from './pages/AutoTrading';
import SystemMonitor from './pages/SystemMonitor';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import MarketAnalysis from './pages/MarketAnalysis';
import AIChat from './pages/AIChat';
import wsService from './services/websocket';
import { useSystemAlerts } from './hooks/useWebSocket';
import './App.css';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

function App() {
  const [selectedKey, setSelectedKey] = useState('dashboard');
  const { alerts } = useSystemAlerts(10);
  
  // Initialize WebSocket connection
  useEffect(() => {
    wsService.connect().catch(console.error);
    return () => {
      wsService.disconnect();
    };
  }, []);
  
  // Show notifications for critical alerts
  useEffect(() => {
    const latestAlert = alerts[0];
    if (latestAlert && (latestAlert.level === 'ERROR' || latestAlert.level === 'CRITICAL')) {
      notification.error({
        message: latestAlert.title,
        description: latestAlert.message,
        duration: latestAlert.level === 'CRITICAL' ? 0 : 10,
      });
    }
  }, [alerts]);

  const renderContent = () => {
    switch (selectedKey) {
      case 'dashboard':
        return <Dashboard />;
      case 'portfolio':
        return <Portfolio />;
      case 'auto-trading':
        return <AutoTrading />;
      case 'system-monitor':
        return <SystemMonitor />;
      case 'reports':
        return <Reports />;
      case 'ai-recommendations':
        return <AIRecommendations />;
      case 'ai-chat':
        return <AIChat />;
      case 'market':
        return <MarketAnalysis />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <ConfigProvider>
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{ display: 'flex', alignItems: 'center', background: '#001529' }}>
          <RobotOutlined style={{ fontSize: 32, color: 'white', marginRight: 16 }} />
          <Title level={3} style={{ color: 'white', margin: 0 }}>
            🤖 Dual Asset Bot - AI双币赢交易机器人
          </Title>
        </Header>
        <Layout>
          <Sider width={200} style={{ background: '#fff' }}>
            <Menu
              mode="inline"
              selectedKeys={[selectedKey]}
              onSelect={({ key }) => setSelectedKey(key)}
              style={{ height: '100%', borderRight: 0 }}
            >
              <Menu.Item key="dashboard" icon={<DashboardOutlined />}>
                Dashboard
              </Menu.Item>
              <Menu.Item key="portfolio" icon={<WalletOutlined />}>
                Portfolio
              </Menu.Item>
              <Menu.Item key="auto-trading" icon={<PlayCircleOutlined />}>
                Auto Trading
              </Menu.Item>
              <Menu.Item key="system-monitor" icon={<MonitorOutlined />}>
                System Monitor
              </Menu.Item>
              <Menu.Item key="reports" icon={<FileTextOutlined />}>
                Reports
              </Menu.Item>
              <Menu.Item key="ai-recommendations" icon={<ThunderboltOutlined />}>
                AI Recommendations
              </Menu.Item>
              <Menu.Item key="ai-chat" icon={<CommentOutlined />}>
                AI Chat
              </Menu.Item>
              <Menu.Item key="market" icon={<LineChartOutlined />}>
                Market Analysis
              </Menu.Item>
              <Menu.Item key="settings" icon={<SettingOutlined />}>
                Settings
              </Menu.Item>
            </Menu>
          </Sider>
          <Layout style={{ padding: '0' }}>
            <Content style={{ margin: 0, minHeight: 280 }}>
              {renderContent()}
            </Content>
          </Layout>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}

export default App;