import React, { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Table, Tag, Button, Space, Spin, Alert, Typography, Badge, Select, Tooltip, Modal, Progress, Divider, Tabs, message, Descriptions } from 'antd';
import { 
  SyncOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  TrophyOutlined,
  InfoCircleOutlined,
  FileSearchOutlined,
  ThunderboltOutlined,
  ExclamationCircleOutlined,
  RobotOutlined
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
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [reportData, setReportData] = useState<any>(null);
  const [aiAnalysis, setAiAnalysis] = useState<any>(null);
  const [chartImage, setChartImage] = useState<string | null>(null);
  const [chartSource, setChartSource] = useState<string | null>(null);
  
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
    // Auto-generate analysis report on first load and pair change
    generateAnalysisReport();
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
        setAnalysisData(data.market_data);
        
        // Store structured report data for better display
        if (data.report_data) {
          setReportData(data.report_data);
        }
        
        // Store AI analysis if available
        if (data.ai_analysis) {
          setAiAnalysis(data.ai_analysis);
        }
        
        // Handle chart data if available
        if (data.chart && data.chart.image_base64) {
          setChartImage(data.chart.image_base64);
          setChartSource(data.chart.source);
        } else {
          setChartImage(null);
          setChartSource(null);
        }
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
      {/* Environment Indicator */}
      <div style={{ marginBottom: 16, padding: '8px 16px', background: '#f0f2f5', borderRadius: 8 }}>
        <Space>
          <Tag color={botStatus?.binance_connected ? 'green' : 'red'}>
            {botStatus?.binance_connected ? 'Connected' : 'Disconnected'}
          </Tag>
          <Tag color="blue">
            {process.env.REACT_APP_DEMO_MODE === 'true' ? 'Demo Mode' : 'Live Mode'}
          </Tag>
          <Tag color="orange">
            Production Data
          </Tag>
          {process.env.REACT_APP_DEMO_MODE === 'true' && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              Trading simulated - No real money involved
            </Text>
          )}
        </Space>
      </div>
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

      {/* Simplified price display card */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card>
            <Row align="middle">
              <Col span={8}>
                <div>
                  <Text type="secondary" style={{ fontSize: 14 }}>Current Price</Text>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
                    <Title level={2} style={{ margin: 0 }}>
                      ${displayPrice?.toLocaleString() || '0.00'}
                    </Title>
                    <Text 
                      style={{ 
                        fontSize: 18,
                        color: (stats24hr?.price_change_percent || marketAnalysis?.price_change_24h || 0) > 0 ? '#52c41a' : '#f5222d',
                        fontWeight: 500
                      }}
                    >
                      ({(stats24hr?.price_change_percent || marketAnalysis?.price_change_24h || 0) > 0 ? '+' : ''}
                      {(stats24hr?.price_change_percent || marketAnalysis?.price_change_24h || 0).toFixed(2)}%)
                    </Text>
                    {realtimePrices[selectedPair] && <Badge status="processing" text="Live" />}
                  </div>
                </div>
              </Col>
              <Col span={16}>
                <Space size="large" style={{ width: '100%', justifyContent: 'flex-end' }}>
                  <div>
                    <Text type="secondary">24h High</Text>
                    <div><Text strong style={{ fontSize: 16 }}>${stats24hr?.high_24h?.toLocaleString() || 'N/A'}</Text></div>
                  </div>
                  <div>
                    <Text type="secondary">24h Low</Text>
                    <div><Text strong style={{ fontSize: 16 }}>${stats24hr?.low_24h?.toLocaleString() || 'N/A'}</Text></div>
                  </div>
                  <div>
                    <Text type="secondary">24h Volume</Text>
                    <div><Text strong style={{ fontSize: 16 }}>{stats24hr?.volume?.toFixed(2) || 'N/A'} {currentPairInfo?.asset}</Text></div>
                  </div>
                </Space>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>


      {/* Market Intelligence & Predictions Card - Based on Analysis Report */}
      {analysisData && (
        <>
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={24}>
              <Card 
                title="Market Intelligence & Predictions" 
                extra={
                  <Text type="secondary">Based on Technical Analysis</Text>
                }
              >
                <Row gutter={16}>
                  <Col span={6}>
                    <Statistic
                      title="24h Price Prediction"
                      value={analysisData.price_prediction_24h?.direction || analysisData.trend?.trend || 'NEUTRAL'}
                      prefix={analysisData.price_prediction_24h?.direction === 'UP' || analysisData.trend?.trend === 'BULLISH' ? 
                        <ArrowUpOutlined style={{ color: '#52c41a' }} /> : 
                        analysisData.price_prediction_24h?.direction === 'DOWN' || analysisData.trend?.trend === 'BEARISH' ?
                        <ArrowDownOutlined style={{ color: '#f5222d' }} /> :
                        <InfoCircleOutlined style={{ color: '#1890ff' }} />
                      }
                      valueStyle={{ 
                        fontSize: 16,
                        color: analysisData.price_prediction_24h?.direction === 'UP' || analysisData.trend?.trend === 'BULLISH' ? '#52c41a' : 
                               analysisData.price_prediction_24h?.direction === 'DOWN' || analysisData.trend?.trend === 'BEARISH' ? '#f5222d' : '#1890ff'
                      }}
                    />
                    {analysisData.price_prediction_24h?.confidence && (
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Confidence: {(analysisData.price_prediction_24h.confidence * 100).toFixed(0)}%
                      </Text>
                    )}
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="24h Volatility Forecast"
                      value={analysisData.volatility_prediction?.level || analysisData.volatility?.risk_level || 'MEDIUM'}
                      valueStyle={{ 
                        fontSize: 16,
                        color: (analysisData.volatility_prediction?.level || analysisData.volatility?.risk_level) === 'HIGH' ? '#f5222d' : 
                               (analysisData.volatility_prediction?.level || analysisData.volatility?.risk_level) === 'LOW' ? '#52c41a' : '#faad14'
                      }}
                    />
                    {(analysisData.volatility_prediction?.value || analysisData.volatility?.volatility_ratio) && (
                      <Progress 
                        percent={Math.min((analysisData.volatility_prediction?.value || analysisData.volatility?.volatility_ratio) * 100, 100)} 
                        size="small"
                        strokeColor={(analysisData.volatility_prediction?.level || analysisData.volatility?.risk_level) === 'HIGH' ? '#f5222d' : 
                                    (analysisData.volatility_prediction?.level || analysisData.volatility?.risk_level) === 'LOW' ? '#52c41a' : '#faad14'}
                        showInfo={false}
                      />
                    )}
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="Support Level"
                      value={analysisData.support_resistance?.support || (displayPrice ? displayPrice * 0.95 : 0)}
                      prefix="$"
                      precision={2}
                      valueStyle={{ fontSize: 16, color: '#52c41a' }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="Resistance Level"
                      value={analysisData.support_resistance?.resistance || (displayPrice ? displayPrice * 1.05 : 0)}
                      prefix="$"
                      precision={2}
                      valueStyle={{ fontSize: 16, color: '#f5222d' }}
                    />
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
        </>
      )}
          
      {marketAnalysis && (
        <>
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
          {marketAnalysis && (
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
          )}
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
          <Tabs defaultActiveKey="chart">
            <Tabs.TabPane tab="K-Line Chart" key="chart">
              {chartImage ? (
                <div style={{ textAlign: 'center' }}>
                  <img 
                    src={`data:image/png;base64,${chartImage}`} 
                    alt="K-Line Chart" 
                    style={{ maxWidth: '100%', height: 'auto' }}
                  />
                  <div style={{ marginTop: 8, color: '#888', fontSize: 12 }}>
                    Source: {chartSource === 'binance_futures' ? 'Binance Futures Testnet' : 
                             chartSource === 'generated' ? 'Generated Chart' : chartSource}
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
                  <p>Chart not available</p>
                  <p style={{ fontSize: 12 }}>Unable to generate chart for this symbol</p>
                </div>
              )}
            </Tabs.TabPane>
            <Tabs.TabPane tab="Technical Analysis" key="analysis">
              {reportData ? (
                <div>
                  {/* Overview Section */}
                  <Card size="small" title="Market Overview" style={{ marginBottom: 16 }}>
                    <Descriptions column={2} size="small">
                      <Descriptions.Item label="Current Price">
                        <Text strong>${reportData.overview?.current_price?.toLocaleString() || '0.00'}</Text>
                      </Descriptions.Item>
                      <Descriptions.Item label="24h Change">
                        <Text style={{ color: reportData.overview?.price_change_24h > 0 ? '#52c41a' : '#f5222d' }}>
                          {reportData.overview?.price_change_24h?.toFixed(2) || '0.00'}%
                        </Text>
                      </Descriptions.Item>
                      <Descriptions.Item label="24h High">
                        ${reportData.overview?.high_24h?.toLocaleString() || '0.00'}
                      </Descriptions.Item>
                      <Descriptions.Item label="24h Low">
                        ${reportData.overview?.low_24h?.toLocaleString() || '0.00'}
                      </Descriptions.Item>
                      <Descriptions.Item label="24h Volume">
                        {reportData.overview?.volume_24h?.toLocaleString() || '0.00'}
                      </Descriptions.Item>
                      <Descriptions.Item label="Volume Trend">
                        <Tag color={reportData.overview?.volume_change === 'POSITIVE' ? 'green' : 'red'}>
                          {reportData.overview?.volume_change || 'NEUTRAL'}
                        </Tag>
                      </Descriptions.Item>
                    </Descriptions>
                  </Card>

                  {/* Technical Indicators */}
                  <Card size="small" title="Technical Indicators" style={{ marginBottom: 16 }}>
                    <Row gutter={16}>
                      <Col span={8}>
                        <Statistic
                          title="Trend"
                          value={reportData.technical_analysis?.trend?.direction || 'NEUTRAL'}
                          valueStyle={{ 
                            color: reportData.technical_analysis?.trend?.direction === 'BULLISH' ? '#52c41a' : 
                                   reportData.technical_analysis?.trend?.direction === 'BEARISH' ? '#f5222d' : '#666',
                            fontSize: 16
                          }}
                          suffix={
                            <Tag color="blue" style={{ marginLeft: 8 }}>
                              {reportData.technical_analysis?.trend?.strength || 'MODERATE'}
                            </Tag>
                          }
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="RSI"
                          value={reportData.technical_analysis?.indicators?.rsi?.value || 50}
                          suffix={
                            <Tag color={
                              reportData.technical_analysis?.indicators?.rsi?.value > 70 ? 'red' :
                              reportData.technical_analysis?.indicators?.rsi?.value < 30 ? 'green' : 'blue'
                            }>
                              {reportData.technical_analysis?.indicators?.rsi?.signal || 'NEUTRAL'}
                            </Tag>
                          }
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="Volatility"
                          value={reportData.technical_analysis?.volatility?.level || 'MEDIUM'}
                          valueStyle={{ fontSize: 16 }}
                          suffix={
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              ATR: {reportData.technical_analysis?.volatility?.atr?.toFixed(2) || '0.00'}
                            </Text>
                          }
                        />
                      </Col>
                    </Row>
                    <Divider style={{ margin: '12px 0' }} />
                    <Row gutter={16}>
                      <Col span={8}>
                        <Text type="secondary">Support Level</Text>
                        <div><Text strong>${reportData.technical_analysis?.support_resistance?.support?.toLocaleString() || '0.00'}</Text></div>
                      </Col>
                      <Col span={8}>
                        <Text type="secondary">Pivot Point</Text>
                        <div><Text strong>${reportData.technical_analysis?.support_resistance?.pivot?.toLocaleString() || '0.00'}</Text></div>
                      </Col>
                      <Col span={8}>
                        <Text type="secondary">Resistance Level</Text>
                        <div><Text strong>${reportData.technical_analysis?.support_resistance?.resistance?.toLocaleString() || '0.00'}</Text></div>
                      </Col>
                    </Row>
                  </Card>

                  {/* 24h Prediction */}
                  <Card size="small" title="24-Hour Forecast" style={{ marginBottom: 16 }}>
                    <Row gutter={16}>
                      <Col span={12}>
                        <div style={{ marginBottom: 8 }}>
                          <Text type="secondary">Price Direction</Text>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          {reportData.prediction?.['24h']?.direction === 'UP' ? 
                            <ArrowUpOutlined style={{ color: '#52c41a', fontSize: 24 }} /> :
                            reportData.prediction?.['24h']?.direction === 'DOWN' ?
                            <ArrowDownOutlined style={{ color: '#f5222d', fontSize: 24 }} /> :
                            <Text style={{ fontSize: 24 }}>→</Text>
                          }
                          <Text strong style={{ fontSize: 18 }}>
                            {reportData.prediction?.['24h']?.direction || 'SIDEWAYS'}
                          </Text>
                          <Progress 
                            percent={reportData.prediction?.['24h']?.confidence * 100 || 50} 
                            size="small" 
                            style={{ width: 100 }}
                            strokeColor="#1890ff"
                          />
                        </div>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          Confidence: {(reportData.prediction?.['24h']?.confidence * 100 || 50).toFixed(0)}%
                        </Text>
                      </Col>
                      <Col span={12}>
                        <div style={{ marginBottom: 8 }}>
                          <Text type="secondary">Target Range</Text>
                        </div>
                        <div>
                          <Text strong>
                            ${reportData.prediction?.['24h']?.target_range?.low?.toLocaleString() || '0.00'} - 
                            ${reportData.prediction?.['24h']?.target_range?.high?.toLocaleString() || '0.00'}
                          </Text>
                        </div>
                        <Tag color="orange" style={{ marginTop: 8 }}>
                          {reportData.prediction?.['24h']?.expected_volatility || 'MEDIUM'} Volatility
                        </Tag>
                      </Col>
                    </Row>
                  </Card>

                  {/* Trading Recommendation */}
                  <Alert
                    message="Trading Recommendation"
                    description={
                      <div>
                        <div style={{ marginBottom: 8 }}>
                          <Tag color={
                            reportData.recommendation?.signal === 'BUY' || reportData.recommendation?.signal === 'STRONG_BUY' ? 'green' :
                            reportData.recommendation?.signal === 'SELL' || reportData.recommendation?.signal === 'STRONG_SELL' ? 'red' : 'blue'
                          } style={{ marginRight: 8 }}>
                            {reportData.recommendation?.signal || 'HOLD'}
                          </Tag>
                          <Tag color="purple">
                            {reportData.recommendation?.strategy || 'WAIT'}
                          </Tag>
                        </div>
                        <Text>{reportData.recommendation?.description || 'No specific recommendation at this time'}</Text>
                        <div style={{ marginTop: 8 }}>
                          <Text type="secondary">Risk Level: {reportData.recommendation?.risk_level || 'MEDIUM'} | 
                            Suitable for: {reportData.recommendation?.suitability || 'Balanced portfolios'}</Text>
                        </div>
                      </div>
                    }
                    type={
                      reportData.recommendation?.signal === 'BUY' || reportData.recommendation?.signal === 'STRONG_BUY' ? 'success' :
                      reportData.recommendation?.signal === 'SELL' || reportData.recommendation?.signal === 'STRONG_SELL' ? 'warning' : 'info'
                    }
                    showIcon
                  />

                  {/* Summary Text */}
                  <div style={{ marginTop: 16, padding: 16, background: '#f5f5f5', borderRadius: 4 }}>
                    <Text type="secondary" style={{ whiteSpace: 'pre-wrap' }}>
                      {analysisReport}
                    </Text>
                  </div>
                </div>
              ) : (
                <div style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                  {analysisReport}
                </div>
              )}
            </Tabs.TabPane>
            {aiAnalysis && aiAnalysis.enabled && (
              <Tabs.TabPane tab="AI Analysis" key="ai">
                <div>
                  {/* AI Confidence Score */}
                  {aiAnalysis.confidence_score && (
                    <Card size="small" title="AI Confidence" style={{ marginBottom: 16 }}>
                      <Progress 
                        percent={Math.round(aiAnalysis.confidence_score * 100)} 
                        strokeColor={{
                          '0%': '#108ee9',
                          '100%': '#87d068',
                        }}
                      />
                      <Text type="secondary">Model: {aiAnalysis.model || 'Claude'}</Text>
                    </Card>
                  )}

                  {/* Market Overview from AI */}
                  {aiAnalysis.market_overview && (
                    <Card size="small" title="AI Market Overview" style={{ marginBottom: 16 }}>
                      <Text>{aiAnalysis.market_overview}</Text>
                    </Card>
                  )}

                  {/* Pattern Analysis */}
                  {aiAnalysis.pattern_analysis && (
                    <Card size="small" title="Pattern Analysis" style={{ marginBottom: 16 }}>
                      <Text>{aiAnalysis.pattern_analysis}</Text>
                    </Card>
                  )}

                  {/* Trading Strategy */}
                  {aiAnalysis.trading_strategy && (
                    <Card size="small" title="AI Trading Strategy" style={{ marginBottom: 16 }}>
                      <Alert
                        message="Dual Investment Strategy"
                        description={aiAnalysis.trading_strategy}
                        type="info"
                        showIcon
                      />
                    </Card>
                  )}

                  {/* Risk Assessment */}
                  {aiAnalysis.risk_assessment && (
                    <Card size="small" title="Risk Assessment" style={{ marginBottom: 16 }}>
                      <Text>{aiAnalysis.risk_assessment}</Text>
                    </Card>
                  )}

                  {/* Key Insights */}
                  {aiAnalysis.key_insights && aiAnalysis.key_insights.length > 0 && (
                    <Card size="small" title="Key AI Insights" style={{ marginBottom: 16 }}>
                      <ul style={{ paddingLeft: 20 }}>
                        {aiAnalysis.key_insights.map((insight: string, index: number) => (
                          <li key={index}>
                            <Text>{insight}</Text>
                          </li>
                        ))}
                      </ul>
                    </Card>
                  )}

                  {/* Warnings */}
                  {aiAnalysis.warnings && aiAnalysis.warnings.length > 0 && (
                    <Alert
                      message="Risk Warnings"
                      description={
                        <ul style={{ paddingLeft: 20, marginBottom: 0 }}>
                          {aiAnalysis.warnings.map((warning: string, index: number) => (
                            <li key={index}>{warning}</li>
                          ))}
                        </ul>
                      }
                      type="warning"
                      showIcon
                    />
                  )}
                </div>
              </Tabs.TabPane>
            )}
          </Tabs>
        )}
      </Modal>
    </div>
  );
};

export default Dashboard;