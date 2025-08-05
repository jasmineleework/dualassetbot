import React from 'react';
import { ConfigProvider, Layout, Typography } from 'antd';
import './App.css';

const { Header, Content } = Layout;
const { Title } = Typography;

function App() {
  return (
    <ConfigProvider>
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{ display: 'flex', alignItems: 'center' }}>
          <Title level={3} style={{ color: 'white', margin: 0 }}>
            Dual Asset Bot
          </Title>
        </Header>
        <Content style={{ padding: '24px' }}>
          <div style={{ background: '#fff', padding: 24, minHeight: 360 }}>
            <Title level={2}>Welcome to Dual Asset Bot</Title>
            <p>Binance Dual Investment Auto Trading Bot is initializing...</p>
          </div>
        </Content>
      </Layout>
    </ConfigProvider>
  );
}

export default App;