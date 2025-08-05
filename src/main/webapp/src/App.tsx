import React from 'react';
import { ConfigProvider, Layout, Typography, Menu } from 'antd';
import { 
  DashboardOutlined, 
  LineChartOutlined, 
  SettingOutlined,
  RobotOutlined 
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import './App.css';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

function App() {
  return (
    <ConfigProvider>
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{ display: 'flex', alignItems: 'center', background: '#001529' }}>
          <RobotOutlined style={{ fontSize: 32, color: 'white', marginRight: 16 }} />
          <Title level={3} style={{ color: 'white', margin: 0 }}>
            Dual Asset Bot - 币安双币赢自动交易机器人
          </Title>
        </Header>
        <Layout>
          <Sider width={200} style={{ background: '#fff' }}>
            <Menu
              mode="inline"
              defaultSelectedKeys={['dashboard']}
              style={{ height: '100%', borderRight: 0 }}
            >
              <Menu.Item key="dashboard" icon={<DashboardOutlined />}>
                Dashboard
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
              <Dashboard />
            </Content>
          </Layout>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}

export default App;