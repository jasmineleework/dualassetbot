import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Switch,
  Button,
  Form,
  InputNumber,
  Select,
  Alert,
  message,
  Typography,
  Divider,
  Table,
  Tag,
  Modal,
  Space,
  Spin,
  Statistic,
  Progress,
  Tabs,
  List,
  Tooltip,
  Popconfirm,
  Badge
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  SettingOutlined,
  ThunderboltOutlined,
  RocketOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  StopOutlined,
  EyeOutlined,
  FireOutlined,
  DollarOutlined
} from '@ant-design/icons';
import {
  apiService,
  TradingSettings,
  ActiveTask,
  AIRecommendation,
  TaskStatus
} from '../services/api';
import './AutoTrading.css';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

const AutoTrading: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState<TradingSettings | null>(null);
  const [activeTasks, setActiveTasks] = useState<ActiveTask[]>([]);
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([]);
  const [settingsModalVisible, setSettingsModalVisible] = useState(false);
  const [executingRecommendation, setExecutingRecommendation] = useState<string>('');
  const [triggeringTask, setTriggeringTask] = useState<string>('');
  const [form] = Form.useForm();

  const fetchData = async () => {
    try {
      setLoading(true);
      const [settingsRes, tasksRes, btcRecs, ethRecs] = await Promise.all([
        apiService.getTradingSettings(),
        apiService.getActiveTasks(),
        apiService.getAIRecommendations('BTCUSDT', 5),
        apiService.getAIRecommendations('ETHUSDT', 5)
      ]);

      setSettings(settingsRes);
      setActiveTasks(tasksRes.active_tasks);
      setRecommendations([...btcRecs.recommendations, ...ethRecs.recommendations]);

      // Update form with current settings
      form.setFieldsValue(settingsRes);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to load data';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-refresh every 15 seconds
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleAutoTrading = async (enabled: boolean) => {
    try {
      if (enabled) {
        Modal.confirm({
          title: 'Enable Automated Trading',
          icon: <ExclamationCircleOutlined />,
          content: (
            <div>
              <Paragraph>
                This will enable fully automated trading based on AI recommendations. 
                The system will automatically execute investments when confidence thresholds are met.
              </Paragraph>
              <Alert
                message="Risk Warning"
                description="Automated trading involves financial risk. Please ensure you understand the risks before proceeding."
                type="warning"
                showIcon
                style={{ marginTop: 16 }}
              />
            </div>
          ),
          okText: 'Enable',
          cancelText: 'Cancel',
          onOk: async () => {
            await updateSettings({ automated_trading_enabled: enabled });
          }
        });
      } else {
        await updateSettings({ automated_trading_enabled: enabled });
      }
    } catch (error) {
      message.error('Failed to toggle automated trading');
    }
  };

  const updateSettings = async (updates: Partial<TradingSettings>) => {
    try {
      const result = await apiService.updateTradingSettings(updates);
      message.success('Settings updated successfully');
      setSettings(prev => prev ? { ...prev, ...updates } : null);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to update settings';
      message.error(errorMsg);
    }
  };

  const handleSaveSettings = async (values: any) => {
    try {
      await updateSettings(values);
      setSettingsModalVisible(false);
      message.success('Trading parameters updated successfully');
    } catch (error) {
      message.error('Failed to update settings');
    }
  };

  const handleTriggerAutoExecution = async () => {
    try {
      setTriggeringTask('auto-execute');
      const result = await apiService.triggerAutoExecution();
      message.success(`Auto-execution triggered. Task ID: ${result.task_id}`);
      setTimeout(fetchData, 2000); // Refresh data to show new task
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to trigger auto-execution';
      message.error(errorMsg);
    } finally {
      setTriggeringTask('');
    }
  };

  const handleExecuteRecommendation = async (recommendation: AIRecommendation) => {
    try {
      setExecutingRecommendation(recommendation.product_id);
      const result = await apiService.executeInvestment(
        recommendation.product_id,
        recommendation.amount
      );
      message.success(`Investment execution started. Task ID: ${result.task_id}`);
      setTimeout(fetchData, 2000);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to execute investment';
      message.error(errorMsg);
    } finally {
      setExecutingRecommendation('');
    }
  };

  const handleTriggerMarketUpdate = async () => {
    try {
      setTriggeringTask('market-update');
      const result = await apiService.triggerMarketDataUpdate(['BTCUSDT', 'ETHUSDT']);
      message.success(`Market data update triggered. Task ID: ${result.task_id}`);
      setTimeout(fetchData, 2000);
    } catch (error) {
      message.error('Failed to trigger market update');
    } finally {
      setTriggeringTask('');
    }
  };

  const handleTriggerAIRecommendations = async () => {
    try {
      setTriggeringTask('ai-recommendations');
      const result = await apiService.triggerAIRecommendations(['BTCUSDT', 'ETHUSDT']);
      message.success(`AI recommendations generation triggered. Task ID: ${result.task_id}`);
      setTimeout(fetchData, 2000);
    } catch (error) {
      message.error('Failed to trigger AI recommendations');
    } finally {
      setTriggeringTask('');
    }
  };

  const getRecommendationColor = (recommendation: string) => {
    const colors: Record<string, string> = {
      'STRONG_BUY': 'success',
      'BUY': 'processing',
      'CONSIDER': 'warning',
      'WEAK_BUY': 'default',
      'SKIP': 'error'
    };
    return colors[recommendation] || 'default';
  };

  const getTaskIcon = (taskName: string) => {
    if (taskName.includes('market')) return <SyncOutlined spin />;
    if (taskName.includes('ai') || taskName.includes('recommendation')) return <ThunderboltOutlined />;
    if (taskName.includes('trading') || taskName.includes('execute')) return <RocketOutlined />;
    return <FireOutlined />;
  };

  const recommendationColumns = [
    {
      title: 'Product',
      dataIndex: 'product_id',
      key: 'product_id',
      render: (text: string) => <Text code style={{ fontSize: '11px' }}>{text}</Text>,
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
            strokeColor={score >= 0.7 ? '#52c41a' : score >= 0.5 ? '#faad14' : '#f5222d'}
          />
          <Text style={{ fontSize: '12px' }}>{(score * 100).toFixed(1)}%</Text>
        </div>
      ),
      sorter: (a: AIRecommendation, b: AIRecommendation) => a.ai_score - b.ai_score,
    },
    {
      title: 'Recommendation',
      dataIndex: 'recommendation',
      key: 'recommendation',
      render: (rec: string) => (
        <Tag color={getRecommendationColor(rec)} style={{ fontSize: '11px' }}>
          {rec}
        </Tag>
      ),
    },
    {
      title: 'Amount',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => <Text strong>${amount.toFixed(0)}</Text>,
    },
    {
      title: 'Expected Return',
      dataIndex: 'expected_return',
      key: 'expected_return',
      render: (returnRate: number) => (
        <Text type="success">+{(returnRate * 100).toFixed(2)}%</Text>
      ),
    },
    {
      title: 'Action',
      key: 'action',
      render: (_: any, record: AIRecommendation) => (
        <Space size="small">
          <Button
            type="primary"
            size="small"
            icon={<RocketOutlined />}
            loading={executingRecommendation === record.product_id}
            onClick={() => handleExecuteRecommendation(record)}
            disabled={!record.should_invest}
          >
            Execute
          </Button>
        </Space>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', marginTop: 100 }}>
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>Loading auto-trading dashboard...</p>
      </div>
    );
  }

  const highConfidenceRecs = recommendations.filter(r => r.should_invest && r.ai_score >= 0.65);
  const autoTradingEnabled = settings?.automated_trading_enabled || false;

  return (
    <div className="auto-trading-container">
      <div className="auto-trading-header">
        <Title level={2}>
          <PlayCircleOutlined style={{ color: autoTradingEnabled ? '#52c41a' : '#d9d9d9', marginRight: 8 }} />
          Automated Trading Control
        </Title>
        <Space>
          <Button icon={<SyncOutlined />} onClick={fetchData}>
            Refresh
          </Button>
          <Button
            icon={<SettingOutlined />}
            onClick={() => setSettingsModalVisible(true)}
          >
            Settings
          </Button>
        </Space>
      </div>

      {/* Main Control Panel */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={4}>Automated Trading</Title>
              <Switch
                size="large"
                checked={autoTradingEnabled}
                onChange={handleToggleAutoTrading}
                checkedChildren={<CheckCircleOutlined />}
                unCheckedChildren={<StopOutlined />}
              />
              <div style={{ marginTop: 12 }}>
                <Text type={autoTradingEnabled ? 'success' : 'secondary'}>
                  {autoTradingEnabled ? 'ENABLED' : 'DISABLED'}
                </Text>
              </div>
            </div>
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="High Confidence Recommendations"
              value={highConfidenceRecs.length}
              suffix="Ready"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: highConfidenceRecs.length > 0 ? '#52c41a' : '#d9d9d9' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Active Tasks"
              value={activeTasks.length}
              suffix="Running"
              prefix={<FireOutlined />}
              valueStyle={{ color: activeTasks.length > 0 ? '#1890ff' : '#d9d9d9' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Card title="Quick Actions" style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Button
              type="primary"
              size="large"
              icon={<RocketOutlined />}
              onClick={handleTriggerAutoExecution}
              loading={triggeringTask === 'auto-execute'}
              disabled={!autoTradingEnabled}
              block
            >
              Trigger Auto-Execution
            </Button>
            <Text type="secondary" style={{ fontSize: '12px', display: 'block', textAlign: 'center', marginTop: 8 }}>
              Execute high-confidence AI recommendations
            </Text>
          </Col>
          <Col span={8}>
            <Button
              type="default"
              size="large"
              icon={<SyncOutlined />}
              onClick={handleTriggerMarketUpdate}
              loading={triggeringTask === 'market-update'}
              block
            >
              Update Market Data
            </Button>
            <Text type="secondary" style={{ fontSize: '12px', display: 'block', textAlign: 'center', marginTop: 8 }}>
              Refresh market data from Binance
            </Text>
          </Col>
          <Col span={8}>
            <Button
              type="default"
              size="large"
              icon={<ThunderboltOutlined />}
              onClick={handleTriggerAIRecommendations}
              loading={triggeringTask === 'ai-recommendations'}
              block
            >
              Generate AI Recommendations
            </Button>
            <Text type="secondary" style={{ fontSize: '12px', display: 'block', textAlign: 'center', marginTop: 8 }}>
              Run AI analysis for new recommendations
            </Text>
          </Col>
        </Row>
      </Card>

      {/* Tabs for different views */}
      <Tabs defaultActiveKey="recommendations">
        <TabPane tab={`AI Recommendations (${recommendations.length})`} key="recommendations">
          <Card>
            <Table
              columns={recommendationColumns}
              dataSource={recommendations}
              rowKey="product_id"
              size="small"
              pagination={{ pageSize: 10, showSizeChanger: true }}
              scroll={{ x: true }}
            />
          </Card>
        </TabPane>

        <TabPane 
          tab={
            <Badge count={activeTasks.length} size="small">
              <span>Active Tasks</span>
            </Badge>
          } 
          key="tasks"
        >
          <Card>
            <List
              dataSource={activeTasks}
              renderItem={(task) => (
                <List.Item
                  actions={[
                    <Tooltip title="Task is running">
                      <Tag color="processing">Running</Tag>
                    </Tooltip>
                  ]}
                >
                  <List.Item.Meta
                    avatar={getTaskIcon(task.name)}
                    title={<Text code>{task.task_id}</Text>}
                    description={
                      <div>
                        <Text strong>{task.name}</Text>
                        <br />
                        <Text type="secondary">Worker: {task.worker}</Text>
                        {task.time_start && (
                          <>
                            <br />
                            <Text type="secondary">Started: {new Date(task.time_start).toLocaleTimeString()}</Text>
                          </>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              )}
              locale={{
                emptyText: (
                  <div style={{ textAlign: 'center', padding: 32 }}>
                    <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
                    <div style={{ marginTop: 16 }}>
                      <Text>No active tasks</Text>
                    </div>
                  </div>
                )
              }}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* Settings Modal */}
      <Modal
        title="Trading Parameters"
        visible={settingsModalVisible}
        onCancel={() => setSettingsModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveSettings}
          initialValues={settings || {}}
        >
          <Alert
            message="Risk Warning"
            description="Modifying these parameters will affect automated trading behavior. Please understand the implications before making changes."
            type="warning"
            showIcon
            style={{ marginBottom: 24 }}
          />

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="max_concurrent_trades"
                label="Max Concurrent Trades"
                rules={[{ required: true, type: 'number', min: 1, max: 20 }]}
              >
                <InputNumber min={1} max={20} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="trading_cooldown_minutes"
                label="Trading Cooldown (minutes)"
                rules={[{ required: true, type: 'number', min: 1, max: 120 }]}
              >
                <InputNumber min={1} max={120} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="default_investment_amount"
                label="Default Investment Amount ($)"
                rules={[{ required: true, type: 'number', min: 10, max: 10000 }]}
              >
                <InputNumber min={10} max={10000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="min_apr_threshold"
                label="Minimum APR Threshold"
                rules={[{ required: true, type: 'number', min: 0, max: 1 }]}
              >
                <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="max_single_investment_ratio"
                label="Max Single Investment Ratio"
                rules={[{ required: true, type: 'number', min: 0.01, max: 1 }]}
              >
                <InputNumber min={0.01} max={1} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="risk_level"
                label="Risk Level"
                rules={[{ required: true, type: 'number', min: 1, max: 10 }]}
              >
                <Select style={{ width: '100%' }}>
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(level => (
                    <Option key={level} value={level}>
                      Level {level} {level <= 3 ? '(Conservative)' : level <= 7 ? '(Moderate)' : '(Aggressive)'}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                Save Settings
              </Button>
              <Button onClick={() => setSettingsModalVisible(false)}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AutoTrading;