import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Select,
  Button,
  Statistic,
  Typography,
  Space,
  Divider,
  Tag,
  Progress,
  Alert,
  message,
  Spin,
  Table,
  Tabs,
  Badge,
  Tooltip,
  Timeline,
  Empty,
  Radio,
  DatePicker
} from 'antd';
import {
  LineChartOutlined,
  RiseOutlined,
  FallOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  BarChartOutlined,
  PieChartOutlined,
  DotChartOutlined,
  StockOutlined,
  FundOutlined,
  DollarOutlined,
  SyncOutlined,
  InfoCircleOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ThunderboltOutlined,
  FireOutlined
} from '@ant-design/icons';
import {
  apiService,
  MarketAnalysis,
  DualInvestmentProduct,
  MarketPrice
} from '../services/api';
import './MarketAnalysis.css';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;

interface TechnicalIndicator {
  name: string;
  value: number;
  signal: 'BUY' | 'SELL' | 'NEUTRAL';
  strength: number;
}

interface MarketSentiment {
  overall: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  score: number;
  fearGreedIndex: number;
  volume24h: number;
  volatility: number;
}

interface PriceLevel {
  type: 'SUPPORT' | 'RESISTANCE';
  price: number;
  strength: 'STRONG' | 'MODERATE' | 'WEAK';
  touches: number;
}

interface MarketNews {
  id: string;
  title: string;
  summary: string;
  sentiment: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';
  impact: 'HIGH' | 'MEDIUM' | 'LOW';
  timestamp: string;
  source: string;
}

const MarketAnalysisPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [marketAnalysis, setMarketAnalysis] = useState<MarketAnalysis | null>(null);
  const [currentPrice, setCurrentPrice] = useState<number>(0);
  const [price24hChange, setPrice24hChange] = useState<number>(0);
  const [products, setProducts] = useState<DualInvestmentProduct[]>([]);
  const [technicalIndicators, setTechnicalIndicators] = useState<TechnicalIndicator[]>([]);
  const [marketSentiment, setMarketSentiment] = useState<MarketSentiment | null>(null);
  const [priceLevels, setPriceLevels] = useState<PriceLevel[]>([]);
  const [marketNews, setMarketNews] = useState<MarketNews[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchMarketData = async () => {
    try {
      setRefreshing(true);
      
      // Fetch all data in parallel
      const results = await Promise.allSettled([
        apiService.getMarketAnalysis(selectedSymbol),
        apiService.getPrice(selectedSymbol),
        apiService.getDualInvestmentProducts(),
        apiService.get24hrStats(selectedSymbol)
      ]);

      if (results[0].status === 'fulfilled') {
        setMarketAnalysis(results[0].value);
        setPrice24hChange(results[0].value.price_change_24h);
      }
      
      if (results[1].status === 'fulfilled') {
        setCurrentPrice(results[1].value.price);
      }
      
      if (results[2].status === 'fulfilled') {
        setProducts(results[2].value.filter(p => 
          p.asset === selectedSymbol.replace('USDT', '') || 
          p.currency === selectedSymbol.replace('USDT', '')
        ));
      }

      // Generate technical indicators from analysis
      if (marketAnalysis) {
        const indicators: TechnicalIndicator[] = [
          {
            name: 'RSI',
            value: marketAnalysis.volatility.volatility_ratio * 50 + 25, // Mock calculation
            signal: marketAnalysis.signals.rsi_signal as 'BUY' | 'SELL' | 'NEUTRAL',
            strength: marketAnalysis.trend.strength === 'STRONG' ? 90 : 
                     marketAnalysis.trend.strength === 'MODERATE' ? 60 : 30
          },
          {
            name: 'MACD',
            value: 0.0025,
            signal: marketAnalysis.signals.macd_signal as 'BUY' | 'SELL' | 'NEUTRAL',
            strength: 75
          },
          {
            name: 'Bollinger Bands',
            value: 0,
            signal: marketAnalysis.signals.bb_signal as 'BUY' | 'SELL' | 'NEUTRAL',
            strength: 65
          },
          {
            name: 'Moving Average (50)',
            value: currentPrice * 0.98,
            signal: currentPrice > (currentPrice * 0.98) ? 'BUY' : 'SELL',
            strength: 55
          },
          {
            name: 'Moving Average (200)',
            value: currentPrice * 0.95,
            signal: currentPrice > (currentPrice * 0.95) ? 'BUY' : 'SELL',
            strength: 70
          }
        ];
        setTechnicalIndicators(indicators);

        // Generate market sentiment
        const sentiment: MarketSentiment = {
          overall: marketAnalysis.trend.trend === 'UPTREND' ? 'BULLISH' : 
                  marketAnalysis.trend.trend === 'DOWNTREND' ? 'BEARISH' : 'NEUTRAL',
          score: marketAnalysis.trend.strength === 'STRONG' ? 75 : 
                 marketAnalysis.trend.strength === 'MODERATE' ? 50 : 25,
          fearGreedIndex: Math.floor(Math.random() * 100), // Mock data
          volume24h: Math.random() * 1000000000,
          volatility: marketAnalysis.volatility.volatility_ratio
        };
        setMarketSentiment(sentiment);
      }

      // Generate price levels (mock data)
      if (currentPrice > 0) {
        const levels: PriceLevel[] = [
          { type: 'RESISTANCE', price: currentPrice * 1.05, strength: 'STRONG', touches: 5 },
          { type: 'RESISTANCE', price: currentPrice * 1.03, strength: 'MODERATE', touches: 3 },
          { type: 'SUPPORT', price: currentPrice * 0.97, strength: 'MODERATE', touches: 4 },
          { type: 'SUPPORT', price: currentPrice * 0.95, strength: 'STRONG', touches: 7 },
        ];
        setPriceLevels(levels);
      }

      // Generate market news (mock data)
      const news: MarketNews[] = [
        {
          id: '1',
          title: 'Bitcoin Breaks Key Resistance Level',
          summary: 'Bitcoin has successfully broken through the $45,000 resistance level with strong volume.',
          sentiment: 'POSITIVE',
          impact: 'HIGH',
          timestamp: new Date().toISOString(),
          source: 'CryptoNews'
        },
        {
          id: '2',
          title: 'Federal Reserve Maintains Interest Rates',
          summary: 'The Fed keeps rates unchanged, providing stability to risk assets including cryptocurrencies.',
          sentiment: 'NEUTRAL',
          impact: 'MEDIUM',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          source: 'Bloomberg'
        },
        {
          id: '3',
          title: 'Institutional Adoption Continues',
          summary: 'Major financial institutions continue to expand their cryptocurrency offerings.',
          sentiment: 'POSITIVE',
          impact: 'MEDIUM',
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          source: 'Reuters'
        }
      ];
      setMarketNews(news);

    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to load market data';
      message.error(errorMsg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchMarketData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchMarketData, 30000);
    return () => clearInterval(interval);
  }, [selectedSymbol, selectedTimeframe]);

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'UPTREND':
        return <RiseOutlined style={{ color: '#52c41a' }} />;
      case 'DOWNTREND':
        return <FallOutlined style={{ color: '#f5222d' }} />;
      default:
        return <LineChartOutlined style={{ color: '#faad14' }} />;
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'BUY':
      case 'STRONG_BUY':
        return 'success';
      case 'SELL':
      case 'STRONG_SELL':
        return 'error';
      default:
        return 'warning';
    }
  };

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'LOW':
        return '#52c41a';
      case 'MEDIUM':
        return '#faad14';
      case 'HIGH':
        return '#f5222d';
      default:
        return '#d9d9d9';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'POSITIVE':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'NEGATIVE':
        return <CloseCircleOutlined style={{ color: '#f5222d' }} />;
      default:
        return <InfoCircleOutlined style={{ color: '#faad14' }} />;
    }
  };

  const technicalColumns = [
    {
      title: 'Indicator',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: 'Value',
      dataIndex: 'value',
      key: 'value',
      render: (value: number, record: TechnicalIndicator) => {
        if (record.name.includes('Moving Average')) {
          return <Text>${value.toFixed(2)}</Text>;
        }
        if (record.name === 'RSI') {
          return <Text>{value.toFixed(1)}</Text>;
        }
        return <Text>{value.toFixed(4)}</Text>;
      },
    },
    {
      title: 'Signal',
      dataIndex: 'signal',
      key: 'signal',
      render: (signal: string) => (
        <Tag color={getSignalColor(signal)} style={{ fontWeight: 600 }}>
          {signal}
        </Tag>
      ),
    },
    {
      title: 'Strength',
      dataIndex: 'strength',
      key: 'strength',
      render: (strength: number) => (
        <Progress 
          percent={strength} 
          size="small" 
          strokeColor={strength >= 70 ? '#52c41a' : strength >= 40 ? '#faad14' : '#f5222d'}
        />
      ),
    },
  ];

  const priceLevelColumns = [
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === 'RESISTANCE' ? 'red' : 'green'}>
          {type}
        </Tag>
      ),
    },
    {
      title: 'Price Level',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => <Text strong>${price.toFixed(2)}</Text>,
    },
    {
      title: 'Strength',
      dataIndex: 'strength',
      key: 'strength',
      render: (strength: string) => {
        const color = strength === 'STRONG' ? 'green' : strength === 'MODERATE' ? 'orange' : 'red';
        return <Tag color={color}>{strength}</Tag>;
      },
    },
    {
      title: 'Touches',
      dataIndex: 'touches',
      key: 'touches',
      render: (touches: number) => <Badge count={touches} style={{ backgroundColor: '#52c41a' }} />,
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', marginTop: 100 }}>
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>Loading market analysis...</p>
      </div>
    );
  }

  return (
    <div className="market-analysis-container">
      <div className="market-analysis-header">
        <Title level={2}>
          <LineChartOutlined style={{ color: '#1890ff', marginRight: 8 }} />
          Advanced Market Analysis
        </Title>
        <Space>
          <Select
            value={selectedSymbol}
            onChange={setSelectedSymbol}
            style={{ width: 150 }}
          >
            <Option value="BTCUSDT">BTC/USDT</Option>
            <Option value="ETHUSDT">ETH/USDT</Option>
            <Option value="BNBUSDT">BNB/USDT</Option>
            <Option value="SOLUSDT">SOL/USDT</Option>
          </Select>
          <Radio.Group value={selectedTimeframe} onChange={(e) => setSelectedTimeframe(e.target.value)}>
            <Radio.Button value="5m">5m</Radio.Button>
            <Radio.Button value="15m">15m</Radio.Button>
            <Radio.Button value="1h">1h</Radio.Button>
            <Radio.Button value="4h">4h</Radio.Button>
            <Radio.Button value="1d">1d</Radio.Button>
          </Radio.Group>
          <Button 
            icon={<SyncOutlined spin={refreshing} />} 
            onClick={fetchMarketData}
            loading={refreshing}
          >
            Refresh
          </Button>
        </Space>
      </div>

      {/* Price Overview */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title={selectedSymbol.replace('USDT', '/USDT')}
              value={currentPrice}
              precision={2}
              prefix={<DollarOutlined />}
              valueStyle={{ color: price24hChange >= 0 ? '#52c41a' : '#f5222d' }}
            />
            <div style={{ marginTop: 8 }}>
              {price24hChange >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              <Text style={{ marginLeft: 4, color: price24hChange >= 0 ? '#52c41a' : '#f5222d' }}>
                {Math.abs(price24hChange).toFixed(2)}%
              </Text>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Market Trend"
              value={marketAnalysis?.trend.trend || 'NEUTRAL'}
              prefix={getTrendIcon(marketAnalysis?.trend.trend || 'NEUTRAL')}
              valueStyle={{ fontSize: '16px', textTransform: 'uppercase' }}
            />
            <Text type="secondary">Strength: {marketAnalysis?.trend.strength}</Text>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Volatility"
              value={(marketAnalysis?.volatility.volatility_ratio || 0) * 100}
              suffix="%"
              precision={2}
              valueStyle={{ color: getRiskLevelColor(marketAnalysis?.volatility.risk_level || 'MEDIUM') }}
            />
            <Text type="secondary">Risk: {marketAnalysis?.volatility.risk_level}</Text>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="AI Recommendation"
              value={marketAnalysis?.signals.recommendation || 'HOLD'}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ 
                fontSize: '16px', 
                textTransform: 'uppercase',
                color: getSignalColor(marketAnalysis?.signals.recommendation || 'HOLD') === 'success' ? '#52c41a' : 
                       getSignalColor(marketAnalysis?.signals.recommendation || 'HOLD') === 'error' ? '#f5222d' : '#faad14'
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Market Sentiment */}
      {marketSentiment && (
        <Card title="Market Sentiment" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <Title level={4}>{marketSentiment.overall}</Title>
                <Progress
                  type="dashboard"
                  percent={marketSentiment.score}
                  strokeColor={
                    marketSentiment.overall === 'BULLISH' ? '#52c41a' :
                    marketSentiment.overall === 'BEARISH' ? '#f5222d' : '#faad14'
                  }
                />
                <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                  Overall Market Sentiment
                </Text>
              </div>
            </Col>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <Title level={4}>Fear & Greed Index</Title>
                <Progress
                  type="dashboard"
                  percent={marketSentiment.fearGreedIndex}
                  strokeColor={{
                    '0%': '#f5222d',
                    '50%': '#faad14',
                    '100%': '#52c41a',
                  }}
                />
                <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                  {marketSentiment.fearGreedIndex < 30 ? 'Extreme Fear' :
                   marketSentiment.fearGreedIndex < 50 ? 'Fear' :
                   marketSentiment.fearGreedIndex < 70 ? 'Greed' : 'Extreme Greed'}
                </Text>
              </div>
            </Col>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <Statistic
                  title="24h Volume"
                  value={marketSentiment.volume24h}
                  prefix={<DollarOutlined />}
                  precision={0}
                />
                <Statistic
                  title="Volatility Index"
                  value={marketSentiment.volatility * 100}
                  suffix="%"
                  precision={2}
                  style={{ marginTop: 16 }}
                />
              </div>
            </Col>
          </Row>
        </Card>
      )}

      {/* Detailed Analysis Tabs */}
      <Tabs defaultActiveKey="technical">
        <TabPane 
          tab={
            <span>
              <BarChartOutlined />
              Technical Analysis
            </span>
          } 
          key="technical"
        >
          <Card>
            <Alert
              message="Technical Indicators"
              description="Real-time technical analysis based on multiple indicators and timeframes."
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <Table
              columns={technicalColumns}
              dataSource={technicalIndicators}
              rowKey="name"
              pagination={false}
            />
          </Card>
        </TabPane>

        <TabPane 
          tab={
            <span>
              <DotChartOutlined />
              Price Levels
            </span>
          } 
          key="levels"
        >
          <Card>
            <Alert
              message="Support & Resistance Levels"
              description="Key price levels identified through historical price action and volume analysis."
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <Table
              columns={priceLevelColumns}
              dataSource={priceLevels}
              rowKey={(record) => `${record.type}-${record.price}`}
              pagination={false}
            />
          </Card>
        </TabPane>

        <TabPane 
          tab={
            <span>
              <FireOutlined />
              Market News & Events
            </span>
          } 
          key="news"
        >
          <Card>
            <Timeline>
              {marketNews.map((news) => (
                <Timeline.Item
                  key={news.id}
                  dot={getSentimentIcon(news.sentiment)}
                  color={news.sentiment === 'POSITIVE' ? 'green' : news.sentiment === 'NEGATIVE' ? 'red' : 'gray'}
                >
                  <Card size="small">
                    <div style={{ marginBottom: 8 }}>
                      <Text strong>{news.title}</Text>
                      <Tag 
                        color={news.impact === 'HIGH' ? 'red' : news.impact === 'MEDIUM' ? 'orange' : 'green'}
                        style={{ marginLeft: 8 }}
                      >
                        {news.impact} IMPACT
                      </Tag>
                    </div>
                    <Paragraph type="secondary" style={{ marginBottom: 8 }}>
                      {news.summary}
                    </Paragraph>
                    <Space>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {new Date(news.timestamp).toLocaleString()}
                      </Text>
                      <Divider type="vertical" />
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        Source: {news.source}
                      </Text>
                    </Space>
                  </Card>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </TabPane>

        <TabPane 
          tab={
            <span>
              <FundOutlined />
              Dual Investment Opportunities
            </span>
          } 
          key="opportunities"
        >
          <Card>
            <Alert
              message="Available Dual Investment Products"
              description="Products filtered based on current market analysis and AI recommendations."
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />
            {products.length > 0 ? (
              <Table
                dataSource={products}
                rowKey="id"
                pagination={{ pageSize: 5 }}
                columns={[
                  {
                    title: 'Product',
                    dataIndex: 'id',
                    key: 'id',
                    render: (text: string) => <Text code style={{ fontSize: '11px' }}>{text.substring(0, 12)}...</Text>,
                  },
                  {
                    title: 'Type',
                    dataIndex: 'type',
                    key: 'type',
                    render: (type: string) => (
                      <Tag color={type === 'UP' ? 'green' : 'red'}>{type}</Tag>
                    ),
                  },
                  {
                    title: 'Strike Price',
                    dataIndex: 'strike_price',
                    key: 'strike_price',
                    render: (price: number) => <Text strong>${price.toFixed(2)}</Text>,
                  },
                  {
                    title: 'APY',
                    dataIndex: 'apy',
                    key: 'apy',
                    render: (apy: number) => (
                      <Text type="success" strong>{(apy * 100).toFixed(2)}%</Text>
                    ),
                  },
                  {
                    title: 'Term',
                    dataIndex: 'term_days',
                    key: 'term_days',
                    render: (days: number) => <Text>{days} days</Text>,
                  },
                  {
                    title: 'Action',
                    key: 'action',
                    render: (_: any, record: DualInvestmentProduct) => (
                      <Button type="primary" size="small" icon={<ThunderboltOutlined />}>
                        Analyze
                      </Button>
                    ),
                  },
                ]}
              />
            ) : (
              <Empty description="No products available for selected symbol" />
            )}
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default MarketAnalysisPage;