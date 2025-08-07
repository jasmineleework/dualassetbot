import React, { useState } from 'react';
import { ConfigProvider, Layout, Typography, Menu } from 'antd';
import { 
  DashboardOutlined, 
  LineChartOutlined, 
  SettingOutlined,
  RobotOutlined,
  ThunderboltOutlined,
  WalletOutlined,
  PlayCircleOutlined,
  MonitorOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import AIRecommendations from './pages/AIRecommendations';
import Portfolio from './pages/Portfolio';
import AutoTrading from './pages/AutoTrading';
import SystemMonitor from './pages/SystemMonitor';
import Reports from './pages/Reports';
import './App.css';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

function App() {
  const [selectedKey, setSelectedKey] = useState('dashboard');

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
      case 'market':
        return <div style={{ padding: 24 }}>市场分析功能开发中...</div>;
      case 'settings':
        return <div style={{ padding: 24 }}>设置功能开发中...</div>;
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