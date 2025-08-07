import React, { useState, useEffect } from 'react';
import { ConfigProvider, Layout, Typography, Menu, notification, Button, Drawer } from 'antd';
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
  CommentOutlined,
  MenuOutlined
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
import './styles/responsive.css';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

function App() {
  const [selectedKey, setSelectedKey] = useState('dashboard');
  const [mobileMenuVisible, setMobileMenuVisible] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const { alerts } = useSystemAlerts(10);
  
  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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

  const menuItems = (
    <Menu
      mode="inline"
      selectedKeys={[selectedKey]}
      onSelect={({ key }) => {
        setSelectedKey(key);
        setMobileMenuVisible(false);
      }}
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
  );

  return (
    <ConfigProvider>
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{ display: 'flex', alignItems: 'center', background: '#001529', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            {isMobile && (
              <Button
                type="text"
                icon={<MenuOutlined />}
                onClick={() => setMobileMenuVisible(true)}
                style={{ color: 'white', marginRight: 16 }}
              />
            )}
            <RobotOutlined style={{ fontSize: isMobile ? 24 : 32, color: 'white', marginRight: 16 }} />
            <Title level={isMobile ? 4 : 3} style={{ color: 'white', margin: 0 }}>
              {isMobile ? 'Dual Asset Bot' : '🤖 Dual Asset Bot - AI双币赢交易机器人'}
            </Title>
          </div>
        </Header>
        <Layout>
          {!isMobile && (
            <Sider width={200} style={{ background: '#fff' }}>
              {menuItems}
            </Sider>
          )}
          <Layout style={{ padding: '0' }}>
            <Content style={{ margin: 0, minHeight: 280 }}>
              {renderContent()}
            </Content>
          </Layout>
        </Layout>
        
        {/* Mobile Menu Drawer */}
        <Drawer
          title="Navigation"
          placement="left"
          onClose={() => setMobileMenuVisible(false)}
          visible={mobileMenuVisible}
          width={250}
        >
          {menuItems}
        </Drawer>
      </Layout>
    </ConfigProvider>
  );
}

export default App;