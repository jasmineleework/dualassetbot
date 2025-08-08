import React, { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Table, Tag, Button, Space, Spin, Alert, Typography, Badge, Select, Tooltip, Modal, Progress, Divider } from 'antd';
import { 
  DollarOutlined, 
  LineChartOutlined, 
  RobotOutlined,
  SyncOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  TrophyOutlined,
  InfoCircleOutlined,
  FileSearchOutlined,
  ThunderboltOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { apiService, BotStatus, DualInvestmentProduct, MarketAnalysis } from '../services/api';
import { usePriceUpdates, useSystemAlerts, usePortfolioUpdates } from '../hooks/useWebSocket';
import ConnectionIndicator from '../components/ConnectionIndicator';
import { SimpleBarChart, SimplePieChart, MiniSparkline, ProgressChart } from '../components/Charts/SimpleChart';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

// Supported trading pairs
const SUPPORTED_PAIRS = [
  { value: 'BTCUSDT', label: 'BTC/USDT', asset: 'BTC', quote: 'USDT' },
  { value: 'BTCUSDC', label: 'BTC/USDC', asset: 'BTC', quote: 'USDC' },
  { value: 'ETHUSDT', label: 'ETH/USDT', asset: 'ETH', quote: 'USDT' },
  { value: 'ETHUSDC', label: 'ETH/USDC', asset: 'ETH', quote: 'USDC' }
];

// AI Recommendation interface
interface AIRecommendation {
  product_id: string;
  should_invest: boolean;
  ai_score: number;
  expected_return: number;
  risk_score: number;
  recommendation: string;
  reasons: string[];
  warnings: string[];
}

// Enhanced Market Analysis interface
interface EnhancedMarketAnalysis extends MarketAnalysis {
  price_prediction_24h?: {
    direction: 'UP' | 'DOWN' | 'NEUTRAL';
    confidence: number;
    target_price?: number;
  };
  volatility_prediction?: {
    level: 'LOW' | 'MEDIUM' | 'HIGH';
    value: number;
  };
  support_resistance?: {
    support: number;
    resistance: number;
  };
  risk_level?: 'LOW' | 'MEDIUM' | 'HIGH';
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [marketAnalysis, setMarketAnalysis] = useState<EnhancedMarketAnalysis | null>(null);
  const [products, setProducts] = useState<DualInvestmentProduct[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [stats24hr, setStats24hr] = useState<any>(null);
  const [selectedPair, setSelectedPair] = useState<string>('BTCUSDT');
  const [aiRecommendations, setAiRecommendations] = useState<AIRecommendation[]>([]);
  const [analysisModalVisible, setAnalysisModalVisible] = useState(false);
  const [analysisReport, setAnalysisReport] = useState<string | null>(null);
  const [generatingReport, setGeneratingReport] = useState(false);
  
  // WebSocket hooks for real-time data
  const { prices: realtimePrices } = usePriceUpdates([selectedPair]);
  const { alerts, unreadCount } = useSystemAlerts(5);
  const { portfolio } = usePortfolioUpdates();
  
  // Get current pair info
  const currentPairInfo = SUPPORTED_PAIRS.find(p => p.value === selectedPair);

  const fetchData = async (symbol?: string) => {
    const targetSymbol = symbol || selectedPair;
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

      // Fetch all data using Promise.allSettled to handle partial failures
      const results = await Promise.allSettled([
        apiService.getPrice(targetSymbol),
        apiService.getMarketAnalysis(targetSymbol),
        apiService.getDualInvestmentProducts(),
        apiService.get24hrStats(targetSymbol),
        fetchAIRecommendations(targetSymbol)
      ]);

      // Process results even if some fail
      if (results[0].status === 'fulfilled') {
        setCurrentPrice(results[0].value.price);
      }
      
      if (results[1].status === 'fulfilled') {
        setMarketAnalysis(results[1].value);
      }
      
      if (results[2].status === 'fulfilled') {
        setProducts(results[2].value);
      }
      
      if (results[3].status === 'fulfilled') {
        setStats24hr(results[3].value);
      }
      
      if (results[4].status === 'fulfilled') {
        // AI recommendations handled in fetchAIRecommendations
      }
      
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
      setLoading(false);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData(selectedPair);
  }, [selectedPair]);
  
  useEffect(() => {
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => fetchData(), 30000);
    return () => clearInterval(interval);
  }, [selectedPair]);
  
  // Fetch AI recommendations
  const fetchAIRecommendations = async (symbol: string) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
    
    try {
      const response = await fetch(
        `http://localhost:8081/api/v1/dual-investment/ai-recommendations/${symbol}`,
        { signal: controller.signal }
      );
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        setAiRecommendations(data.recommendations || []);
        return data;
      }
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        console.error('AI recommendations request timeout');
      } else {
        console.error('Failed to fetch AI recommendations:', err);
      }
    }
    return null;
  };
  
  // Generate K-line analysis report
  const generateAnalysisReport = async () => {
    setGeneratingReport(true);
    setAnalysisModalVisible(true);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000); // 20 second timeout for analysis
    
    try {
      const response = await fetch(
        `http://localhost:8081/api/v1/market/kline-analysis/${selectedPair}`,
        { signal: controller.signal }
      );
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        setAnalysisReport(data.report);
      } else {
        // Fallback to basic report if API fails
        const fallbackReport = `
## ${currentPairInfo?.label} Market Analysis Report

### Current Market Status
- **Price**: $${currentPrice?.toLocaleString() || 'N/A'}
- **24h Change**: ${stats24hr?.price_change_percent || 0}%
- **Trend**: ${marketAnalysis?.trend?.trend || 'N/A'}
- **Volatility**: ${marketAnalysis?.volatility?.risk_level || 'N/A'}

### Technical Analysis
- **RSI Signal**: ${marketAnalysis?.signals?.rsi_signal || 'N/A'}
- **MACD Signal**: ${marketAnalysis?.signals?.macd_signal || 'N/A'}
- **Support Level**: $${marketAnalysis?.support_resistance?.support?.toLocaleString() || 'TBD'}
- **Resistance Level**: $${marketAnalysis?.support_resistance?.resistance?.toLocaleString() || 'TBD'}

### 24 Hour Prediction
- **Price Direction**: ${marketAnalysis?.price_prediction_24h?.direction || 'NEUTRAL'}
- **Volatility Expectation**: ${marketAnalysis?.volatility_prediction?.level || 'MEDIUM'}
- **Risk Level**: ${marketAnalysis?.risk_level || 'MEDIUM'}

### Investment Recommendation
Based on current market conditions, ${marketAnalysis?.signals?.recommendation === 'BUY' ? 'consider investing in dual investment products with strike prices below current market price' : 'exercise caution and wait for better entry points'}.
        `;
        setAnalysisReport(fallbackReport);
      }
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        setAnalysisReport('Analysis request timeout. Please try again.');
      } else {
        setAnalysisReport('Failed to generate analysis report. Please try again later.');
      }
    } finally {
      setGeneratingReport(false);
    }
  };
  
  // Handle pair selection change
  const handlePairChange = (value: string) => {
    setSelectedPair(value);
    setCurrentPrice(null);
    setMarketAnalysis(null);
    setStats24hr(null);
    setAiRecommendations([]);
  };
  
  // Get recommendation color
  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'STRONG_BUY': return '#52c41a';
      case 'BUY': return '#1890ff';
      case 'CONSIDER': return '#faad14';
      case 'WEAK_BUY': return '#fa8c16';
      case 'SKIP': return '#ff4d4f';
      default: return '#d9d9d9';
    }
  };

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

  // Enhanced product columns with AI recommendations
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
      render: (apy: number) => (
        <Text strong style={{ color: '#52c41a' }}>
          {(apy * 100).toFixed(1)}%
        </Text>
      ),
    },
    {
      title: 'Term',
      dataIndex: 'term_days',
      key: 'term_days',
      render: (days: number) => `${days} days`,
    },
    {
      title: 'AI Score',
      key: 'ai_score',
      render: (_: any, record: DualInvestmentProduct) => {
        const recommendation = aiRecommendations.find(r => r.product_id === record.id);
        if (!recommendation) return <Text type="secondary">-</Text>;
        
        return (
          <Tooltip 
            title={
              <div>
                <div><strong>Recommendation:</strong> {recommendation.recommendation}</div>
                <div><strong>Expected Return:</strong> {(recommendation.expected_return * 100).toFixed(2)}%</div>
                <div><strong>Risk Score:</strong> {(recommendation.risk_score * 100).toFixed(0)}%</div>
                <Divider style={{ margin: '8px 0' }} />
                <div><strong>Reasons:</strong></div>
                <ul style={{ paddingLeft: 16, margin: '4px 0' }}>
                  {recommendation.reasons.slice(0, 3).map((reason, idx) => (
                    <li key={idx} style={{ fontSize: 12 }}>{reason}</li>
                  ))}
                </ul>
                {recommendation.warnings.length > 0 && (
                  <>
                    <div><strong>Warnings:</strong></div>
                    <ul style={{ paddingLeft: 16, margin: '4px 0' }}>
                      {recommendation.warnings.slice(0, 2).map((warning, idx) => (
                        <li key={idx} style={{ fontSize: 12, color: '#ff4d4f' }}>{warning}</li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            }
            placement="left"
          >
            <div style={{ cursor: 'pointer' }}>
              <Progress 
                percent={Math.round(recommendation.ai_score * 100)} 
                size="small" 
                strokeColor={getRecommendationColor(recommendation.recommendation)}
                format={(percent) => `${percent}%`}
              />
              {recommendation.should_invest && (
                <TrophyOutlined style={{ color: '#faad14', marginLeft: 8 }} />
              )}
            </div>
          </Tooltip>
        );
      },
    },
    {
      title: 'Action',
      key: 'action',
      render: (_: any, record: DualInvestmentProduct) => {
        const recommendation = aiRecommendations.find(r => r.product_id === record.id);
        return (
          <Button 
            type={recommendation?.should_invest ? "primary" : "default"}
            size="small"
            icon={recommendation?.should_invest ? <ThunderboltOutlined /> : undefined}
          >
            {recommendation?.should_invest ? 'Invest' : 'Subscribe'}
          </Button>
        );
      },
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
          <Button size="small" onClick={() => fetchData()}>
            Retry
          </Button>
        }
      />
    );
  }

  // Use realtime price if available, otherwise use fetched price
  const displayPrice = realtimePrices[selectedPair]?.price || currentPrice;
  const displayChange = realtimePrices[selectedPair]?.change24h || marketAnalysis?.price_change_24h || 0;

  return (
    <div style={{ padding: 24 }}>
      <ConnectionIndicator />
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Title level={2} style={{ margin: 0 }}>Market Dashboard</Title>
          <Select
            value={selectedPair}
            onChange={handlePairChange}
            style={{ width: 150 }}
            size="large"
          >
            {SUPPORTED_PAIRS.map(pair => (
              <Option key={pair.value} value={pair.value}>
                {pair.label}
              </Option>
            ))}
          </Select>
        </Space>
        <Space>
          {unreadCount > 0 && (
            <Badge count={unreadCount} overflowCount={9}>
              <Button icon={<RobotOutlined />}>
                Alerts
              </Button>
            </Badge>
          )}
          <Button
            icon={<FileSearchOutlined />}
            onClick={generateAnalysisReport}
            type="default"
          >
            View Analysis Report
          </Button>
          <Button 
            icon={<SyncOutlined spin={refreshing} />} 
            onClick={() => fetchData()}
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
              title={`${currentPairInfo?.asset || ''} Price`}
              value={displayPrice || 0}
              precision={2}
              prefix="$"
              suffix={
                <span style={{ fontSize: '14px' }}>
                  {realtimePrices[selectedPair] && <Badge status="processing" style={{ marginRight: 8 }} />}
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
                    suffix={currentPairInfo?.asset || ''}
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

      {/* Enhanced Market Intelligence & Predictions Card */}
      {marketAnalysis && (
        <>
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={24}>
              <Card 
                title="Market Intelligence & Predictions" 
                extra={
                  <Space>
                    <Badge status="processing" text="Real-time" />
                    <Text type="secondary">Last updated: {new Date().toLocaleTimeString()}</Text>
                  </Space>
                }
              >
                <Row gutter={16}>
                  <Col span={4}>
                    <Statistic
                      title="Current Price"
                      value={displayPrice || 0}
                      prefix="$"
                      precision={2}
                      valueStyle={{ fontSize: 20 }}
                    />
                  </Col>
                  <Col span={4}>
                    <Statistic
                      title="24h Price Prediction"
                      value={marketAnalysis.price_prediction_24h?.direction || 'NEUTRAL'}
                      prefix={marketAnalysis.price_prediction_24h?.direction === 'UP' ? 
                        <ArrowUpOutlined style={{ color: '#52c41a' }} /> : 
                        marketAnalysis.price_prediction_24h?.direction === 'DOWN' ?
                        <ArrowDownOutlined style={{ color: '#f5222d' }} /> :
                        <InfoCircleOutlined style={{ color: '#1890ff' }} />
                      }
                      valueStyle={{ 
                        fontSize: 16,
                        color: marketAnalysis.price_prediction_24h?.direction === 'UP' ? '#52c41a' : 
                               marketAnalysis.price_prediction_24h?.direction === 'DOWN' ? '#f5222d' : '#1890ff'
                      }}
                    />
                    {marketAnalysis.price_prediction_24h?.confidence && (
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Confidence: {(marketAnalysis.price_prediction_24h.confidence * 100).toFixed(0)}%
                      </Text>
                    )}
                  </Col>
                  <Col span={4}>
                    <Statistic
                      title="24h Volatility Forecast"
                      value={marketAnalysis.volatility_prediction?.level || marketAnalysis.volatility.risk_level}
                      valueStyle={{ 
                        fontSize: 16,
                        color: (marketAnalysis.volatility_prediction?.level || marketAnalysis.volatility.risk_level) === 'HIGH' ? '#f5222d' : 
                               (marketAnalysis.volatility_prediction?.level || marketAnalysis.volatility.risk_level) === 'LOW' ? '#52c41a' : '#faad14'
                      }}
                    />
                    {marketAnalysis.volatility_prediction?.value && (
                      <Progress 
                        percent={Math.min(marketAnalysis.volatility_prediction.value * 100, 100)} 
                        size="small"
                        strokeColor={(marketAnalysis.volatility_prediction?.level || marketAnalysis.volatility.risk_level) === 'HIGH' ? '#f5222d' : 
                                    (marketAnalysis.volatility_prediction?.level || marketAnalysis.volatility.risk_level) === 'LOW' ? '#52c41a' : '#faad14'}
                        showInfo={false}
                      />
                    )}
                  </Col>
                  <Col span={4}>
                    <Statistic
                      title="Support Level"
                      value={marketAnalysis.support_resistance?.support || (displayPrice ? displayPrice * 0.95 : 0)}
                      prefix="$"
                      precision={2}
                      valueStyle={{ fontSize: 16, color: '#52c41a' }}
                    />
                  </Col>
                  <Col span={4}>
                    <Statistic
                      title="Resistance Level"
                      value={marketAnalysis.support_resistance?.resistance || (displayPrice ? displayPrice * 1.05 : 0)}
                      prefix="$"
                      precision={2}
                      valueStyle={{ fontSize: 16, color: '#f5222d' }}
                    />
                  </Col>
                  <Col span={4}>
                    <Statistic
                      title="24h Risk Level"
                      value={marketAnalysis.risk_level || 'MEDIUM'}
                      prefix={marketAnalysis.risk_level === 'HIGH' ? 
                        <ExclamationCircleOutlined style={{ color: '#f5222d' }} /> : 
                        marketAnalysis.risk_level === 'LOW' ?
                        <InfoCircleOutlined style={{ color: '#52c41a' }} /> :
                        <InfoCircleOutlined style={{ color: '#faad14' }} />
                      }
                      valueStyle={{ 
                        fontSize: 16,
                        color: marketAnalysis.risk_level === 'HIGH' ? '#f5222d' : 
                               marketAnalysis.risk_level === 'LOW' ? '#52c41a' : '#faad14'
                      }}
                    />
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
          
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

          {/* Data Visualization Charts */}
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={12}>
              <SimpleBarChart
                title="Signal Strength Analysis"
                data={[
                  { label: 'RSI', value: marketAnalysis.signals.rsi_signal === 'BUY' ? 75 : marketAnalysis.signals.rsi_signal === 'SELL' ? 25 : 50, color: '#1890ff' },
                  { label: 'MACD', value: marketAnalysis.signals.macd_signal === 'BUY' ? 80 : marketAnalysis.signals.macd_signal === 'SELL' ? 20 : 50, color: '#52c41a' },
                  { label: 'BB', value: marketAnalysis.signals.bb_signal === 'BUY' ? 70 : marketAnalysis.signals.bb_signal === 'SELL' ? 30 : 50, color: '#faad14' },
                  { label: 'Overall', value: marketAnalysis.signals.recommendation === 'BUY' ? 85 : marketAnalysis.signals.recommendation === 'SELL' ? 15 : 50, color: '#722ed1' }
                ]}
                height={200}
              />
            </Col>
            <Col span={12}>
              <SimplePieChart
                title="Risk Distribution"
                data={[
                  { label: 'Low Risk', value: marketAnalysis.volatility.risk_level === 'LOW' ? 60 : 20, color: '#52c41a' },
                  { label: 'Medium Risk', value: marketAnalysis.volatility.risk_level === 'MEDIUM' ? 60 : 30, color: '#faad14' },
                  { label: 'High Risk', value: marketAnalysis.volatility.risk_level === 'HIGH' ? 60 : 10, color: '#f5222d' }
                ]}
              />
            </Col>
          </Row>
        </>
      )}

      <Card title="Available Dual Investment Products">
        <Table
          columns={productColumns}
          dataSource={products}
          rowKey="id"
          pagination={false}
        />
      </Card>
      
      {/* Analysis Report Modal */}
      <Modal
        title={
          <Space>
            <FileSearchOutlined />
            <span>Professional Market Analysis Report</span>
          </Space>
        }
        visible={analysisModalVisible}
        onCancel={() => setAnalysisModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setAnalysisModalVisible(false)}>
            Close
          </Button>,
          <Button key="regenerate" type="primary" onClick={generateAnalysisReport} loading={generatingReport}>
            Regenerate Report
          </Button>
        ]}
      >
        {generatingReport ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
            <p style={{ marginTop: 16 }}>Generating professional analysis report...</p>
          </div>
        ) : (
          <div style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
            {analysisReport}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Dashboard;