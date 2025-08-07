import React, { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Table, Tag, Button, Space, Spin, Alert, Typography, Badge } from 'antd';
import { 
  DollarOutlined, 
  LineChartOutlined, 
  RobotOutlined,
  SyncOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined 
} from '@ant-design/icons';
import { apiService, BotStatus, DualInvestmentProduct, MarketAnalysis } from '../services/api';
import { usePriceUpdates, useSystemAlerts, usePortfolioUpdates } from '../hooks/useWebSocket';
import ConnectionIndicator from '../components/ConnectionIndicator';

const { Title } = Typography;

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [btcPrice, setBtcPrice] = useState<number | null>(null);
  const [marketAnalysis, setMarketAnalysis] = useState<MarketAnalysis | null>(null);
  const [products, setProducts] = useState<DualInvestmentProduct[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [stats24hr, setStats24hr] = useState<any>(null);
  
  // WebSocket hooks for real-time data
  const { prices: realtimePrices } = usePriceUpdates(['BTCUSDT', 'ETHUSDT']);
  const { alerts, unreadCount } = useSystemAlerts(5);
  const { portfolio } = usePortfolioUpdates();

  const fetchData = async () => {
    try {
      setRefreshing(true);
      setError(null);

      // First check status
      const statusRes = await apiService.getStatus();
      setBotStatus(statusRes);

      // If bot is not connected, show limited data
      if (!statusRes.binance_connected) {
        setError('Binance API not connected. Please check your API credentials.');
        setLoading(false);
        
        // Still try to get mock products
        try {
          const productsRes = await apiService.getDualInvestmentProducts();
          setProducts(productsRes);
        } catch (e) {
          // Ignore products error
        }
        return;
      }

      // Fetch all data in parallel if connected
      const [priceRes, analysisRes, productsRes, statsRes] = await Promise.all([
        apiService.getPrice('BTCUSDT'),
        apiService.getMarketAnalysis('BTCUSDT'),
        apiService.getDualInvestmentProducts(),
        apiService.get24hrStats('BTCUSDT')
      ]);

      setBtcPrice(priceRes.price);
      setMarketAnalysis(analysisRes);
      setProducts(productsRes);
      setStats24hr(statsRes);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
      setLoading(false);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getTrendIcon = (trend: string) => {
    return trend === 'BULLISH' ? 
      <ArrowUpOutlined style={{ color: '#52c41a' }} /> : 
      <ArrowDownOutlined style={{ color: '#f5222d' }} />;
  };

  const getSignalColor = (signal: string) => {
    const colors: Record<string, string> = {
      'BUY': 'green',
      'STRONG_BUY': 'success',
      'SELL': 'red',
      'STRONG_SELL': 'error',
      'HOLD': 'default',
      'NEUTRAL': 'default',
      'OVERSOLD': 'green',
      'OVERBOUGHT': 'red'
    };
    return colors[signal] || 'default';
  };

  const productColumns = [
    {
      title: 'Product ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === 'BUY_LOW' ? 'green' : 'blue'}>
          {type === 'BUY_LOW' ? '低买' : '高卖'}
        </Tag>
      ),
    },
    {
      title: 'Asset',
      dataIndex: 'asset',
      key: 'asset',
    },
    {
      title: 'Strike Price',
      dataIndex: 'strike_price',
      key: 'strike_price',
      render: (price: number) => `$${price.toLocaleString()}`,
    },
    {
      title: 'APY',
      dataIndex: 'apy',
      key: 'apy',
      render: (apy: number) => `${(apy * 100).toFixed(1)}%`,
    },
    {
      title: 'Term',
      dataIndex: 'term_days',
      key: 'term_days',
      render: (days: number) => `${days} days`,
    },
    {
      title: 'Action',
      key: 'action',
      render: (_: any, record: DualInvestmentProduct) => (
        <Button type="primary" size="small">
          Subscribe
        </Button>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', marginTop: 100 }}>
        <Spin size="large" />
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Error"
        description={error}
        type="error"
        showIcon
        action={
          <Button size="small" onClick={fetchData}>
            Retry
          </Button>
        }
      />
    );
  }

  // Use realtime price if available, otherwise use fetched price
  const displayBtcPrice = realtimePrices['BTCUSDT']?.price || btcPrice;
  const displayBtcChange = realtimePrices['BTCUSDT']?.change24h || marketAnalysis?.price_change_24h || 0;

  return (
    <div style={{ padding: 24 }}>
      <ConnectionIndicator />
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>Trading Dashboard</Title>
        <Space>
          {unreadCount > 0 && (
            <Badge count={unreadCount} overflowCount={9}>
              <Button icon={<RobotOutlined />}>
                Alerts
              </Button>
            </Badge>
          )}
          <Button 
            icon={<SyncOutlined spin={refreshing} />} 
            onClick={fetchData}
            loading={refreshing}
          >
            Refresh
          </Button>
        </Space>
      </div>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Bot Status"
              value={botStatus?.bot_running ? 'Running' : 'Stopped'}
              valueStyle={{ color: botStatus?.bot_running ? '#3f8600' : '#cf1322' }}
              prefix={<RobotOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="BTC Price"
              value={displayBtcPrice || 0}
              precision={2}
              prefix="$"
              suffix={
                <span style={{ fontSize: '14px' }}>
                  {realtimePrices['BTCUSDT'] && <Badge status="processing" style={{ marginRight: 8 }} />}
                  {marketAnalysis && getTrendIcon(marketAnalysis.trend.trend)}
                </span>
              }
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="24h Change"
              value={stats24hr?.price_change_percent || marketAnalysis?.price_change_24h || 0}
              precision={2}
              valueStyle={{ 
                color: (stats24hr?.price_change_percent || marketAnalysis?.price_change_24h || 0) > 0 ? '#3f8600' : '#cf1322' 
              }}
              prefix={<LineChartOutlined />}
              suffix="%"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Active Strategies"
              value={botStatus?.strategies_active || 0}
              prefix={<DollarOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {stats24hr && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={24}>
            <Card title="24 Hour Statistics">
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="24h High"
                    value={stats24hr.high_24h}
                    prefix="$"
                    precision={2}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="24h Low"
                    value={stats24hr.low_24h}
                    prefix="$"
                    precision={2}
                    valueStyle={{ color: '#f5222d' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="24h Volume"
                    value={stats24hr.volume}
                    suffix="BTC"
                    precision={2}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Price Change"
                    value={stats24hr.price_change}
                    prefix="$"
                    precision={2}
                    valueStyle={{ 
                      color: stats24hr.price_change > 0 ? '#3f8600' : '#cf1322' 
                    }}
                  />
                </Col>
              </Row>
            </Card>
          </Col>
        </Row>
      )}

      {marketAnalysis && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={12}>
            <Card title="Market Analysis">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <strong>Trend:</strong>{' '}
                  <Tag color={marketAnalysis.trend.trend === 'BULLISH' ? 'green' : 'red'}>
                    {marketAnalysis.trend.trend} ({marketAnalysis.trend.strength})
                  </Tag>
                </div>
                <div>
                  <strong>Volatility:</strong>{' '}
                  <Tag color={marketAnalysis.volatility.risk_level === 'HIGH' ? 'red' : 'blue'}>
                    {marketAnalysis.volatility.risk_level}
                  </Tag>
                </div>
                <div>
                  <strong>Overall Signal:</strong>{' '}
                  <Tag color={getSignalColor(marketAnalysis.signals.recommendation)}>
                    {marketAnalysis.signals.recommendation}
                  </Tag>
                </div>
              </Space>
            </Card>
          </Col>
          <Col span={12}>
            <Card title="Technical Indicators">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <strong>RSI:</strong>{' '}
                  <Tag color={getSignalColor(marketAnalysis.signals.rsi_signal)}>
                    {marketAnalysis.signals.rsi_signal}
                  </Tag>
                </div>
                <div>
                  <strong>MACD:</strong>{' '}
                  <Tag color={getSignalColor(marketAnalysis.signals.macd_signal)}>
                    {marketAnalysis.signals.macd_signal}
                  </Tag>
                </div>
                <div>
                  <strong>Bollinger Bands:</strong>{' '}
                  <Tag color={getSignalColor(marketAnalysis.signals.bb_signal)}>
                    {marketAnalysis.signals.bb_signal}
                  </Tag>
                </div>
              </Space>
            </Card>
          </Col>
        </Row>
      )}

      <Card title="Available Dual Investment Products">
        <Table
          columns={productColumns}
          dataSource={products}
          rowKey="id"
          pagination={false}
        />
      </Card>
    </div>
  );
};

export default Dashboard;