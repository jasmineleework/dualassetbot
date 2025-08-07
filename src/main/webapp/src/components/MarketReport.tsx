import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Space,
  Divider,
  Tag,
  Alert,
  Button,
  Timeline,
  Statistic,
  Progress,
  Badge,
  Descriptions,
  Table,
  List
} from 'antd';
import {
  FileTextOutlined,
  DownloadOutlined,
  PrinterOutlined,
  ShareAltOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  RiseOutlined,
  FallOutlined,
  LineChartOutlined,
  BarChartOutlined,
  DollarOutlined,
  ThunderboltOutlined,
  SafetyCertificateOutlined,
  BulbOutlined
} from '@ant-design/icons';
import { MarketAnalysis, DualInvestmentProduct } from '../services/api';
import './MarketReport.css';

const { Title, Text, Paragraph } = Typography;

export interface MarketReportData {
  timestamp: string;
  symbol: string;
  currentPrice: number;
  priceChange24h: number;
  marketAnalysis: MarketAnalysis;
  investmentDecision?: {
    shouldInvest: boolean;
    product?: DualInvestmentProduct;
    amount?: number;
    reasons: string[];
    risks: string[];
  };
  technicalAnalysis: {
    trend: string;
    strength: string;
    signals: {
      rsi: string;
      macd: string;
      bollinger: string;
    };
    keyLevels: {
      support: number[];
      resistance: number[];
    };
  };
  marketNews?: Array<{
    title: string;
    impact: string;
    sentiment: string;
  }>;
  aiInsights: {
    summary: string;
    keyPoints: string[];
    recommendations: string[];
    riskAssessment: string;
  };
}

interface MarketReportProps {
  data: MarketReportData;
  onExport?: (format: 'pdf' | 'html' | 'json') => void;
  onShare?: () => void;
}

const MarketReport: React.FC<MarketReportProps> = ({ data, onExport, onShare }) => {
  const [expanded, setExpanded] = useState(false);

  const getTrendIcon = (trend: string) => {
    if (trend === 'UPTREND') return <RiseOutlined style={{ color: '#52c41a' }} />;
    if (trend === 'DOWNTREND') return <FallOutlined style={{ color: '#f5222d' }} />;
    return <LineChartOutlined style={{ color: '#faad14' }} />;
  };

  const getSignalColor = (signal: string) => {
    if (signal === 'BUY' || signal === 'STRONG_BUY') return 'success';
    if (signal === 'SELL' || signal === 'STRONG_SELL') return 'error';
    return 'warning';
  };

  const getRiskLevel = (volatility: number): { level: string; color: string } => {
    if (volatility < 0.3) return { level: 'LOW', color: '#52c41a' };
    if (volatility < 0.6) return { level: 'MEDIUM', color: '#faad14' };
    return { level: 'HIGH', color: '#f5222d' };
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const riskLevel = getRiskLevel(data.marketAnalysis.volatility.volatility_ratio);

  return (
    <div className="market-report">
      {/* Report Header */}
      <Card className="report-header-card">
        <Row align="middle" justify="space-between">
          <Col>
            <Space>
              <FileTextOutlined style={{ fontSize: 24, color: '#1890ff' }} />
              <div>
                <Title level={4} style={{ margin: 0 }}>市场分析报告</Title>
                <Text type="secondary">{formatTime(data.timestamp)}</Text>
              </div>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button icon={<DownloadOutlined />} onClick={() => onExport?.('pdf')}>
                导出PDF
              </Button>
              <Button icon={<PrinterOutlined />} onClick={() => window.print()}>
                打印
              </Button>
              <Button icon={<ShareAltOutlined />} onClick={onShare}>
                分享
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Executive Summary */}
      <Card title="执行摘要" className="report-section">
        <Alert
          message={
            <Space>
              {getTrendIcon(data.technicalAnalysis.trend)}
              <Text strong>市场趋势: {data.technicalAnalysis.trend}</Text>
            </Space>
          }
          description={data.aiInsights.summary}
          type={data.investmentDecision?.shouldInvest ? 'success' : 'warning'}
          showIcon
        />
        
        <Row gutter={16} style={{ marginTop: 24 }}>
          <Col span={6}>
            <Statistic
              title={data.symbol}
              value={data.currentPrice}
              precision={2}
              prefix="$"
              valueStyle={{ 
                color: data.priceChange24h >= 0 ? '#52c41a' : '#f5222d' 
              }}
              suffix={
                <Text style={{ fontSize: 14, color: data.priceChange24h >= 0 ? '#52c41a' : '#f5222d' }}>
                  {data.priceChange24h >= 0 ? '+' : ''}{data.priceChange24h.toFixed(2)}%
                </Text>
              }
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="AI建议"
              value={data.marketAnalysis.signals.recommendation}
              valueStyle={{ 
                fontSize: 18,
                color: data.investmentDecision?.shouldInvest ? '#52c41a' : '#faad14'
              }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="风险等级"
              value={riskLevel.level}
              valueStyle={{ fontSize: 18, color: riskLevel.color }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="趋势强度"
              value={data.technicalAnalysis.strength}
              valueStyle={{ fontSize: 18 }}
            />
          </Col>
        </Row>
      </Card>

      {/* Investment Decision */}
      {data.investmentDecision && (
        <Card 
          title="投资决策" 
          className="report-section"
          extra={
            <Tag color={data.investmentDecision.shouldInvest ? 'success' : 'default'}>
              {data.investmentDecision.shouldInvest ? '建议投资' : '暂不投资'}
            </Tag>
          }
        >
          {data.investmentDecision.shouldInvest && data.investmentDecision.product && (
            <Descriptions bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="产品ID" span={3}>
                {data.investmentDecision.product.id}
              </Descriptions.Item>
              <Descriptions.Item label="产品类型">
                <Tag color={data.investmentDecision.product.type === 'UP' ? 'green' : 'red'}>
                  {data.investmentDecision.product.type}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="执行价格">
                ${data.investmentDecision.product.strike_price.toFixed(2)}
              </Descriptions.Item>
              <Descriptions.Item label="APY">
                <Text type="success">{(data.investmentDecision.product.apy * 100).toFixed(2)}%</Text>
              </Descriptions.Item>
              <Descriptions.Item label="建议金额" span={3}>
                <Text strong style={{ fontSize: 16 }}>
                  ${data.investmentDecision.amount?.toFixed(2) || '500.00'}
                </Text>
              </Descriptions.Item>
            </Descriptions>
          )}

          <Row gutter={16}>
            <Col span={12}>
              <Card type="inner" title={
                <Space>
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  投资理由
                </Space>
              }>
                <List
                  size="small"
                  dataSource={data.investmentDecision.reasons}
                  renderItem={(reason) => (
                    <List.Item>
                      <Text>• {reason}</Text>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
            <Col span={12}>
              <Card type="inner" title={
                <Space>
                  <ExclamationCircleOutlined style={{ color: '#faad14' }} />
                  风险提示
                </Space>
              }>
                <List
                  size="small"
                  dataSource={data.investmentDecision.risks}
                  renderItem={(risk) => (
                    <List.Item>
                      <Text type="warning">• {risk}</Text>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </Card>
      )}

      {/* Technical Analysis */}
      <Card title="技术分析" className="report-section">
        <Row gutter={16}>
          <Col span={12}>
            <Card type="inner" title="技术指标信号">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div className="indicator-item">
                  <Text strong>RSI:</Text>
                  <Tag color={getSignalColor(data.technicalAnalysis.signals.rsi)} style={{ float: 'right' }}>
                    {data.technicalAnalysis.signals.rsi}
                  </Tag>
                </div>
                <div className="indicator-item">
                  <Text strong>MACD:</Text>
                  <Tag color={getSignalColor(data.technicalAnalysis.signals.macd)} style={{ float: 'right' }}>
                    {data.technicalAnalysis.signals.macd}
                  </Tag>
                </div>
                <div className="indicator-item">
                  <Text strong>Bollinger Bands:</Text>
                  <Tag color={getSignalColor(data.technicalAnalysis.signals.bollinger)} style={{ float: 'right' }}>
                    {data.technicalAnalysis.signals.bollinger}
                  </Tag>
                </div>
              </Space>
            </Card>
          </Col>
          <Col span={12}>
            <Card type="inner" title="关键价位">
              <div style={{ marginBottom: 16 }}>
                <Text strong>阻力位:</Text>
                <div style={{ marginTop: 8 }}>
                  {data.technicalAnalysis.keyLevels.resistance.map((level, index) => (
                    <Tag key={index} color="red" style={{ marginRight: 8, marginBottom: 4 }}>
                      ${level.toFixed(2)}
                    </Tag>
                  ))}
                </div>
              </div>
              <div>
                <Text strong>支撑位:</Text>
                <div style={{ marginTop: 8 }}>
                  {data.technicalAnalysis.keyLevels.support.map((level, index) => (
                    <Tag key={index} color="green" style={{ marginRight: 8, marginBottom: 4 }}>
                      ${level.toFixed(2)}
                    </Tag>
                  ))}
                </div>
              </div>
            </Card>
          </Col>
        </Row>

        <Card type="inner" title="K线形态分析" style={{ marginTop: 16 }}>
          <Paragraph>
            当前市场呈现<Text strong>{data.technicalAnalysis.trend}</Text>趋势，
            强度为<Text strong>{data.technicalAnalysis.strength}</Text>。
            价格位于${data.currentPrice.toFixed(2)}，
            {data.currentPrice > data.technicalAnalysis.keyLevels.resistance[0] ? 
              '突破主要阻力位，上涨动能强劲' :
              data.currentPrice < data.technicalAnalysis.keyLevels.support[0] ?
              '跌破主要支撑位，需要谨慎观察' :
              '在支撑位和阻力位之间震荡'
            }。
          </Paragraph>
          <Paragraph>
            技术指标显示，RSI指标发出<Tag color={getSignalColor(data.technicalAnalysis.signals.rsi)} size="small">
              {data.technicalAnalysis.signals.rsi}
            </Tag>信号，
            MACD指标显示<Tag color={getSignalColor(data.technicalAnalysis.signals.macd)} size="small">
              {data.technicalAnalysis.signals.macd}
            </Tag>，
            布林带指标提示<Tag color={getSignalColor(data.technicalAnalysis.signals.bollinger)} size="small">
              {data.technicalAnalysis.signals.bollinger}
            </Tag>。
            综合来看，市场短期内
            {data.marketAnalysis.signals.recommendation === 'BUY' ? '有上涨潜力' :
             data.marketAnalysis.signals.recommendation === 'SELL' ? '可能面临调整压力' :
             '将维持震荡格局'}。
          </Paragraph>
        </Card>
      </Card>

      {/* Market News */}
      {data.marketNews && data.marketNews.length > 0 && (
        <Card title="市场新闻影响" className="report-section">
          <Timeline>
            {data.marketNews.map((news, index) => (
              <Timeline.Item
                key={index}
                color={
                  news.sentiment === 'POSITIVE' ? 'green' :
                  news.sentiment === 'NEGATIVE' ? 'red' : 'gray'
                }
                dot={
                  news.impact === 'HIGH' ? 
                    <ExclamationCircleOutlined style={{ fontSize: 16 }} /> : undefined
                }
              >
                <Space direction="vertical">
                  <Space>
                    <Text strong>{news.title}</Text>
                    <Tag color={
                      news.impact === 'HIGH' ? 'red' :
                      news.impact === 'MEDIUM' ? 'orange' : 'green'
                    } size="small">
                      {news.impact} 影响
                    </Tag>
                  </Space>
                  <Text type="secondary">
                    市场情绪: {news.sentiment === 'POSITIVE' ? '积极' :
                              news.sentiment === 'NEGATIVE' ? '消极' : '中性'}
                  </Text>
                </Space>
              </Timeline.Item>
            ))}
          </Timeline>
        </Card>
      )}

      {/* AI Insights */}
      <Card title={
        <Space>
          <BulbOutlined style={{ color: '#722ed1' }} />
          AI深度洞察
        </Space>
      } className="report-section">
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Title level={5}>关键要点</Title>
            <List
              dataSource={data.aiInsights.keyPoints}
              renderItem={(point) => (
                <List.Item>
                  <Space>
                    <CheckCircleOutlined style={{ color: '#1890ff' }} />
                    <Text>{point}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </div>

          <div>
            <Title level={5}>投资建议</Title>
            <List
              dataSource={data.aiInsights.recommendations}
              renderItem={(recommendation) => (
                <List.Item>
                  <Space>
                    <ThunderboltOutlined style={{ color: '#722ed1' }} />
                    <Text strong>{recommendation}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </div>

          <div>
            <Title level={5}>风险评估</Title>
            <Alert
              message="风险提示"
              description={data.aiInsights.riskAssessment}
              type="warning"
              showIcon
              icon={<SafetyCertificateOutlined />}
            />
          </div>
        </Space>
      </Card>

      {/* Report Footer */}
      <Card className="report-footer" size="small">
        <Row justify="space-between" align="middle">
          <Col>
            <Text type="secondary">
              本报告由AI自动生成，仅供参考，不构成投资建议
            </Text>
          </Col>
          <Col>
            <Text type="secondary">
              生成时间: {formatTime(data.timestamp)}
            </Text>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default MarketReport;