import React, { useState, useEffect } from 'react';
import { Card, Button, Select, Table, Badge, Spin, Alert, Typography, Row, Col, Statistic, Progress } from 'antd';
import { ReloadOutlined, TrophyOutlined, DollarOutlined, RiseOutlined, FallOutlined } from '@ant-design/icons';
import './AIRecommendations.css';

const { Title, Text } = Typography;
const { Option } = Select;

interface Recommendation {
  product_id: string;
  should_invest: boolean;
  amount: number;
  ai_score: number;
  expected_return: number;
  risk_score: number;
  recommendation: string;
  reasons: string[];
  warnings: string[];
  metadata: any;
}

interface MarketData {
  current_price: number;
  trend: {
    trend: string;
    strength: number;
  };
  volatility: {
    risk_level: string;
    volatility_ratio: number;
  };
  signals: {
    recommendation: string;
    current_rsi: number;
    macd_signal: string;
  };
}

const AIRecommendations: React.FC = () => {
  const [symbol, setSymbol] = useState<string>('BTCUSDT');
  const [loading, setLoading] = useState<boolean>(false);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [error, setError] = useState<string>('');
  const [totalRecommendations, setTotalRecommendations] = useState<number>(0);

  const fetchRecommendations = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`http://localhost:8081/api/v1/dual-investment/ai-recommendations/${symbol}`);
      if (!response.ok) {
        throw new Error('Failed to fetch recommendations');
      }
      
      const data = await response.json();
      setRecommendations(data.recommendations || []);
      setTotalRecommendations(data.total_recommendations || 0);
      
      // Extract market data from first recommendation
      if (data.recommendations && data.recommendations.length > 0) {
        setMarketData(data.recommendations[0].market_analysis);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [symbol]);

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

  const getRiskColor = (riskScore: number) => {
    if (riskScore <= 0.3) return '#52c41a';
    if (riskScore <= 0.6) return '#faad14';
    return '#ff4d4f';
  };

  const columns = [
    {
      title: 'Product ID',
      dataIndex: 'product_id',
      key: 'product_id',
      render: (text: string) => (
        <Text code style={{ fontSize: '12px' }}>{text}</Text>
      ),
    },
    {
      title: 'Recommendation',
      dataIndex: 'recommendation',
      key: 'recommendation',
      render: (recommendation: string) => (
        <Badge 
          color={getRecommendationColor(recommendation)}
          text={recommendation}
        />
      ),
    },
    {
      title: 'AI Score',
      dataIndex: 'ai_score',
      key: 'ai_score',
      render: (score: number) => (
        <div>
          <Progress 
            percent={Math.round(score * 100)} 
            size="small" 
            strokeColor={score >= 0.7 ? '#52c41a' : score >= 0.5 ? '#faad14' : '#ff4d4f'}
          />
          <Text style={{ fontSize: '12px' }}>{(score * 100).toFixed(1)}%</Text>
        </div>
      ),
    },
    {
      title: 'Expected Return',
      dataIndex: 'expected_return',
      key: 'expected_return',
      render: (returnRate: number) => (
        <Text type={returnRate > 0 ? 'success' : 'danger'}>
          {(returnRate * 100).toFixed(2)}%
        </Text>
      ),
    },
    {
      title: 'Risk Score',
      dataIndex: 'risk_score',
      key: 'risk_score',
      render: (risk: number) => (
        <Badge 
          color={getRiskColor(risk)}
          text={`${(risk * 100).toFixed(0)}%`}
        />
      ),
    },
    {
      title: 'Amount',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => (
        <Text strong>${amount.toFixed(2)}</Text>
      ),
    },
    {
      title: 'Should Invest',
      dataIndex: 'should_invest',
      key: 'should_invest',
      render: (shouldInvest: boolean) => (
        <Badge 
          status={shouldInvest ? 'success' : 'error'}
          text={shouldInvest ? 'Yes' : 'No'}
        />
      ),
    },
  ];

  const expandedRowRender = (record: Recommendation) => {
    return (
      <div style={{ padding: '16px' }}>
        <Row gutter={16}>
          <Col span={12}>
            <Title level={5}>Reasons</Title>
            <ul>
              {record.reasons.map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>
          </Col>
          <Col span={12}>
            {record.warnings.length > 0 && (
              <>
                <Title level={5}>Warnings</Title>
                <ul>
                  {record.warnings.map((warning, index) => (
                    <li key={index} style={{ color: '#ff4d4f' }}>{warning}</li>
                  ))}
                </ul>
              </>
            )}
          </Col>
        </Row>
      </div>
    );
  };

  return (
    <div className="ai-recommendations">
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={24}>
          <Card>
            <Row gutter={16} align="middle">
              <Col>
                <Title level={2} style={{ margin: 0 }}>
                  <TrophyOutlined style={{ color: '#faad14' }} /> AI Investment Recommendations
                </Title>
              </Col>
              <Col>
                <Select
                  value={symbol}
                  onChange={setSymbol}
                  style={{ width: 120 }}
                >
                  <Option value="BTCUSDT">BTC/USDT</Option>
                  <Option value="ETHUSDT">ETH/USDT</Option>
                </Select>
              </Col>
              <Col>
                <Button 
                  icon={<ReloadOutlined />} 
                  onClick={fetchRecommendations}
                  loading={loading}
                  type="primary"
                >
                  Refresh
                </Button>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {marketData && (
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="Current Price"
                value={marketData.current_price}
                prefix={<DollarOutlined />}
                precision={2}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Market Trend"
                value={marketData.trend.trend}
                prefix={
                  marketData.trend.trend === 'BULLISH' ? 
                  <RiseOutlined style={{ color: '#52c41a' }} /> : 
                  <FallOutlined style={{ color: '#ff4d4f' }} />
                }
                valueStyle={{ 
                  color: marketData.trend.trend === 'BULLISH' ? '#52c41a' : '#ff4d4f' 
                }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Risk Level"
                value={marketData.volatility.risk_level}
                valueStyle={{ 
                  color: getRiskColor(marketData.volatility.volatility_ratio) 
                }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="RSI"
                value={marketData.signals.current_rsi?.toFixed(1) || 'N/A'}
                suffix="%"
                valueStyle={{ 
                  color: marketData.signals.current_rsi < 30 ? '#52c41a' : 
                        marketData.signals.current_rsi > 70 ? '#ff4d4f' : '#1890ff'
                }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {error && (
        <Alert
          message="Error"
          description={error}
          type="error"
          closable
          style={{ marginBottom: '16px' }}
        />
      )}

      <Card 
        title={
          <span>
            AI Recommendations ({totalRecommendations} found)
          </span>
        }
        extra={
          <Badge 
            count={recommendations.filter(r => r.should_invest).length}
            showZero
            style={{ backgroundColor: '#52c41a' }}
          />
        }
      >
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={recommendations}
            rowKey="product_id"
            expandable={{
              expandedRowRender,
              rowExpandable: (record) => record.reasons.length > 0 || record.warnings.length > 0,
            }}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
            }}
          />
        </Spin>
      </Card>
    </div>
  );
};

export default AIRecommendations;