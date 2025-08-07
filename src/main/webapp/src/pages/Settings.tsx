import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Form,
  InputNumber,
  Select,
  Switch,
  Button,
  Typography,
  Space,
  Divider,
  Alert,
  message,
  Modal,
  Input,
  Tabs,
  Table,
  Tag,
  Tooltip,
  Upload,
  Progress,
  Spin
} from 'antd';
import {
  SettingOutlined,
  SaveOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  KeyOutlined,
  ApiOutlined,
  DatabaseOutlined,
  BellOutlined,
  SecurityScanOutlined,
  UploadOutlined,
  DownloadOutlined,
  ClearOutlined,
  LockOutlined,
  UnlockOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import {
  apiService,
  TradingSettings
} from '../services/api';
import './Settings.css';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;
const { TextArea } = Input;

interface APISettings {
  binance_api_key: string;
  binance_secret_key: string;
  testnet_enabled: boolean;
  rate_limit: number;
  timeout_seconds: number;
  max_retries: number;
}

interface NotificationSettings {
  email_enabled: boolean;
  email_address: string;
  webhook_enabled: boolean;
  webhook_url: string;
  notification_types: string[];
  daily_summary: boolean;
}

interface SecuritySettings {
  require_confirmation: boolean;
  auto_logout_minutes: number;
  ip_whitelist_enabled: boolean;
  ip_whitelist: string[];
  max_concurrent_sessions: number;
  audit_log_enabled: boolean;
}

interface SystemSettings {
  log_level: string;
  max_log_files: number;
  database_backup_enabled: boolean;
  backup_frequency_hours: number;
  cleanup_days: number;
  debug_mode: boolean;
}

const Settings: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [tradingSettings, setTradingSettings] = useState<TradingSettings | null>(null);
  const [apiSettings, setApiSettings] = useState<APISettings>({
    binance_api_key: '',
    binance_secret_key: '',
    testnet_enabled: true,
    rate_limit: 1200,
    timeout_seconds: 30,
    max_retries: 3
  });
  const [notificationSettings, setNotificationSettings] = useState<NotificationSettings>({
    email_enabled: false,
    email_address: '',
    webhook_enabled: false,
    webhook_url: '',
    notification_types: ['trade_execution', 'system_alerts'],
    daily_summary: true
  });
  const [securitySettings, setSecuritySettings] = useState<SecuritySettings>({
    require_confirmation: true,
    auto_logout_minutes: 60,
    ip_whitelist_enabled: false,
    ip_whitelist: [],
    max_concurrent_sessions: 3,
    audit_log_enabled: true
  });
  const [systemSettings, setSystemSettings] = useState<SystemSettings>({
    log_level: 'INFO',
    max_log_files: 10,
    database_backup_enabled: true,
    backup_frequency_hours: 24,
    cleanup_days: 30,
    debug_mode: false
  });
  const [resetModalVisible, setResetModalVisible] = useState(false);
  const [testConnectionLoading, setTestConnectionLoading] = useState(false);
  const [form] = Form.useForm();

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const tradingRes = await apiService.getTradingSettings();
      setTradingSettings(tradingRes);
      form.setFieldsValue(tradingRes);

      // In a real implementation, these would be separate API calls
      // For now, using mock data
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to load settings';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSaveTradingSettings = async (values: Partial<TradingSettings>) => {
    try {
      setSaving(true);
      const result = await apiService.updateTradingSettings(values);
      setTradingSettings(prev => prev ? { ...prev, ...values } : null);
      message.success('Trading settings saved successfully');
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to save trading settings';
      message.error(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAPISettings = async () => {
    try {
      setSaving(true);
      // Mock API call - in real implementation would call backend
      await new Promise(resolve => setTimeout(resolve, 1000));
      message.success('API settings saved successfully');
    } catch (error) {
      message.error('Failed to save API settings');
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      setTestConnectionLoading(true);
      // Mock API test - in real implementation would test Binance API connection
      await new Promise(resolve => setTimeout(resolve, 2000));
      const success = Math.random() > 0.3; // Mock success/failure
      
      if (success) {
        message.success('API connection test successful');
      } else {
        message.error('API connection test failed - please check your credentials');
      }
    } catch (error) {
      message.error('Failed to test API connection');
    } finally {
      setTestConnectionLoading(false);
    }
  };

  const handleResetToDefaults = () => {
    Modal.confirm({
      title: 'Reset to Default Settings',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <Paragraph>
            This will reset all settings to their default values. This action cannot be undone.
          </Paragraph>
          <Alert
            message="Warning"
            description="Your current configuration will be lost. Make sure to backup any important settings before proceeding."
            type="warning"
            showIcon
            style={{ marginTop: 16 }}
          />
        </div>
      ),
      okText: 'Reset',
      okType: 'danger',
      cancelText: 'Cancel',
      onOk: async () => {
        try {
          setSaving(true);
          // Mock reset - in real implementation would call backend
          await new Promise(resolve => setTimeout(resolve, 1000));
          message.success('Settings reset to defaults successfully');
          await fetchSettings();
        } catch (error) {
          message.error('Failed to reset settings');
        } finally {
          setSaving(false);
        }
      }
    });
  };

  const handleExportSettings = () => {
    const settings = {
      trading: tradingSettings,
      api: apiSettings,
      notifications: notificationSettings,
      security: securitySettings,
      system: systemSettings
    };
    
    const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `dualasset-settings-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
    message.success('Settings exported successfully');
  };

  const handleImportSettings = (file: File) => {
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const settings = JSON.parse(e.target?.result as string);
        
        // Validate and apply settings
        if (settings.trading) {
          setTradingSettings(settings.trading);
          form.setFieldsValue(settings.trading);
        }
        if (settings.api) setApiSettings(settings.api);
        if (settings.notifications) setNotificationSettings(settings.notifications);
        if (settings.security) setSecuritySettings(settings.security);
        if (settings.system) setSystemSettings(settings.system);
        
        message.success('Settings imported successfully');
      } catch (error) {
        message.error('Failed to import settings - invalid file format');
      }
    };
    reader.readAsText(file);
    return false; // Prevent upload
  };

  const notificationTypeOptions = [
    { label: 'Trade Execution', value: 'trade_execution' },
    { label: 'System Alerts', value: 'system_alerts' },
    { label: 'Error Notifications', value: 'error_notifications' },
    { label: 'Performance Reports', value: 'performance_reports' },
    { label: 'Security Events', value: 'security_events' },
  ];

  const auditLogColumns = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text: string) => new Date(text).toLocaleString(),
    },
    {
      title: 'Action',
      dataIndex: 'action',
      key: 'action',
      render: (text: string) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: 'User',
      dataIndex: 'user',
      key: 'user',
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: 'Details',
      dataIndex: 'details',
      key: 'details',
      render: (text: string) => <Text type="secondary">{text}</Text>,
    },
  ];

  // Mock audit log data
  const auditLogData = [
    {
      key: '1',
      timestamp: new Date().toISOString(),
      action: 'SETTINGS_UPDATE',
      user: 'admin',
      details: 'Updated trading parameters'
    },
    {
      key: '2',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      action: 'API_KEY_UPDATE',
      user: 'admin',
      details: 'Updated Binance API credentials'
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', marginTop: 100 }}>
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>Loading settings...</p>
      </div>
    );
  }

  return (
    <div className="settings-container">
      <div className="settings-header">
        <Title level={2}>
          <SettingOutlined style={{ color: '#1890ff', marginRight: 8 }} />
          System Configuration
        </Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchSettings}>
            Reload
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleExportSettings}>
            Export
          </Button>
          <Upload beforeUpload={handleImportSettings} showUploadList={false}>
            <Button icon={<UploadOutlined />}>Import</Button>
          </Upload>
          <Button
            type="primary"
            danger
            icon={<ClearOutlined />}
            onClick={handleResetToDefaults}
          >
            Reset to Defaults
          </Button>
        </Space>
      </div>

      <Tabs defaultActiveKey="trading">
        {/* Trading Settings */}
        <TabPane tab={
          <span>
            <ApiOutlined />
            Trading Parameters
          </span>
        } key="trading">
          <Card>
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSaveTradingSettings}
              initialValues={tradingSettings || {}}
            >
              <Alert
                message="Trading Configuration"
                description="These settings control the automated trading behavior and risk management."
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    name="automated_trading_enabled"
                    label="Automated Trading"
                    valuePropName="checked"
                  >
                    <Switch
                      checkedChildren={<CheckCircleOutlined />}
                      unCheckedChildren={<ExclamationCircleOutlined />}
                    />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="max_concurrent_trades"
                    label="Max Concurrent Trades"
                    rules={[{ required: true, type: 'number', min: 1, max: 50 }]}
                  >
                    <InputNumber min={1} max={50} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="trading_cooldown_minutes"
                    label="Trading Cooldown (minutes)"
                    rules={[{ required: true, type: 'number', min: 1, max: 1440 }]}
                  >
                    <InputNumber min={1} max={1440} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    name="default_investment_amount"
                    label="Default Investment Amount ($)"
                    rules={[{ required: true, type: 'number', min: 10, max: 100000 }]}
                  >
                    <InputNumber min={10} max={100000} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="min_apr_threshold"
                    label="Minimum APR Threshold"
                    rules={[{ required: true, type: 'number', min: 0, max: 1 }]}
                  >
                    <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="max_single_investment_ratio"
                    label="Max Single Investment Ratio"
                    rules={[{ required: true, type: 'number', min: 0.01, max: 1 }]}
                  >
                    <InputNumber min={0.01} max={1} step={0.01} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="risk_level"
                    label="Risk Level"
                    rules={[{ required: true }]}
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
                  <Button type="primary" htmlType="submit" loading={saving} icon={<SaveOutlined />}>
                    Save Trading Settings
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* API Settings */}
        <TabPane tab={
          <span>
            <KeyOutlined />
            API Configuration
          </span>
        } key="api">
          <Card>
            <Alert
              message="Binance API Configuration"
              description="Configure your Binance API credentials and connection settings. Keep your API keys secure."
              type="warning"
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Row gutter={16}>
              <Col span={12}>
                <Card size="small" title="API Credentials">
                  <Form layout="vertical">
                    <Form.Item label="API Key">
                      <Input.Password
                        placeholder="Enter Binance API Key"
                        value={apiSettings.binance_api_key}
                        onChange={(e) => setApiSettings(prev => ({...prev, binance_api_key: e.target.value}))}
                      />
                    </Form.Item>
                    <Form.Item label="Secret Key">
                      <Input.Password
                        placeholder="Enter Binance Secret Key"
                        value={apiSettings.binance_secret_key}
                        onChange={(e) => setApiSettings(prev => ({...prev, binance_secret_key: e.target.value}))}
                      />
                    </Form.Item>
                    <Form.Item label="Testnet Mode">
                      <Switch
                        checked={apiSettings.testnet_enabled}
                        onChange={(checked) => setApiSettings(prev => ({...prev, testnet_enabled: checked}))}
                        checkedChildren="Testnet"
                        unCheckedChildren="Live"
                      />
                      <Text type="secondary" style={{ marginLeft: 8 }}>
                        Use testnet for safe testing
                      </Text>
                    </Form.Item>
                  </Form>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" title="Connection Settings">
                  <Form layout="vertical">
                    <Form.Item label="Rate Limit (requests/minute)">
                      <InputNumber
                        min={100}
                        max={2400}
                        value={apiSettings.rate_limit}
                        onChange={(value) => setApiSettings(prev => ({...prev, rate_limit: value || 1200}))}
                        style={{ width: '100%' }}
                      />
                    </Form.Item>
                    <Form.Item label="Timeout (seconds)">
                      <InputNumber
                        min={10}
                        max={120}
                        value={apiSettings.timeout_seconds}
                        onChange={(value) => setApiSettings(prev => ({...prev, timeout_seconds: value || 30}))}
                        style={{ width: '100%' }}
                      />
                    </Form.Item>
                    <Form.Item label="Max Retries">
                      <InputNumber
                        min={1}
                        max={10}
                        value={apiSettings.max_retries}
                        onChange={(value) => setApiSettings(prev => ({...prev, max_retries: value || 3}))}
                        style={{ width: '100%' }}
                      />
                    </Form.Item>
                  </Form>
                </Card>
              </Col>
            </Row>

            <Space style={{ marginTop: 16 }}>
              <Button
                type="default"
                icon={<ApiOutlined />}
                loading={testConnectionLoading}
                onClick={handleTestConnection}
              >
                Test Connection
              </Button>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                loading={saving}
                onClick={handleSaveAPISettings}
              >
                Save API Settings
              </Button>
            </Space>
          </Card>
        </TabPane>

        {/* Notification Settings */}
        <TabPane tab={
          <span>
            <BellOutlined />
            Notifications
          </span>
        } key="notifications">
          <Row gutter={16}>
            <Col span={12}>
              <Card title="Email Notifications">
                <Form layout="vertical">
                  <Form.Item>
                    <Switch
                      checked={notificationSettings.email_enabled}
                      onChange={(checked) => setNotificationSettings(prev => ({...prev, email_enabled: checked}))}
                      checkedChildren="Enabled"
                      unCheckedChildren="Disabled"
                    />
                    <Text style={{ marginLeft: 8 }}>Enable email notifications</Text>
                  </Form.Item>
                  <Form.Item label="Email Address">
                    <Input
                      type="email"
                      placeholder="your@email.com"
                      value={notificationSettings.email_address}
                      onChange={(e) => setNotificationSettings(prev => ({...prev, email_address: e.target.value}))}
                      disabled={!notificationSettings.email_enabled}
                    />
                  </Form.Item>
                  <Form.Item>
                    <Switch
                      checked={notificationSettings.daily_summary}
                      onChange={(checked) => setNotificationSettings(prev => ({...prev, daily_summary: checked}))}
                      checkedChildren="Daily Summary"
                      unCheckedChildren="No Summary"
                    />
                  </Form.Item>
                </Form>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="Webhook Notifications">
                <Form layout="vertical">
                  <Form.Item>
                    <Switch
                      checked={notificationSettings.webhook_enabled}
                      onChange={(checked) => setNotificationSettings(prev => ({...prev, webhook_enabled: checked}))}
                      checkedChildren="Enabled"
                      unCheckedChildren="Disabled"
                    />
                    <Text style={{ marginLeft: 8 }}>Enable webhook notifications</Text>
                  </Form.Item>
                  <Form.Item label="Webhook URL">
                    <Input
                      placeholder="https://your-webhook-url.com"
                      value={notificationSettings.webhook_url}
                      onChange={(e) => setNotificationSettings(prev => ({...prev, webhook_url: e.target.value}))}
                      disabled={!notificationSettings.webhook_enabled}
                    />
                  </Form.Item>
                </Form>
              </Card>
            </Col>
          </Row>

          <Card title="Notification Types" style={{ marginTop: 16 }}>
            <Select
              mode="multiple"
              placeholder="Select notification types"
              value={notificationSettings.notification_types}
              onChange={(values) => setNotificationSettings(prev => ({...prev, notification_types: values}))}
              options={notificationTypeOptions}
              style={{ width: '100%' }}
            />
          </Card>
        </TabPane>

        {/* Security Settings */}
        <TabPane tab={
          <span>
            <SecurityScanOutlined />
            Security
          </span>
        } key="security">
          <Row gutter={16}>
            <Col span={12}>
              <Card title="Access Control">
                <Form layout="vertical">
                  <Form.Item>
                    <Switch
                      checked={securitySettings.require_confirmation}
                      onChange={(checked) => setSecuritySettings(prev => ({...prev, require_confirmation: checked}))}
                      checkedChildren={<LockOutlined />}
                      unCheckedChildren={<UnlockOutlined />}
                    />
                    <Text style={{ marginLeft: 8 }}>Require confirmation for trades</Text>
                  </Form.Item>
                  <Form.Item label="Auto Logout (minutes)">
                    <InputNumber
                      min={5}
                      max={480}
                      value={securitySettings.auto_logout_minutes}
                      onChange={(value) => setSecuritySettings(prev => ({...prev, auto_logout_minutes: value || 60}))}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                  <Form.Item label="Max Concurrent Sessions">
                    <InputNumber
                      min={1}
                      max={10}
                      value={securitySettings.max_concurrent_sessions}
                      onChange={(value) => setSecuritySettings(prev => ({...prev, max_concurrent_sessions: value || 3}))}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Form>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="IP Whitelist">
                <Form layout="vertical">
                  <Form.Item>
                    <Switch
                      checked={securitySettings.ip_whitelist_enabled}
                      onChange={(checked) => setSecuritySettings(prev => ({...prev, ip_whitelist_enabled: checked}))}
                      checkedChildren="Enabled"
                      unCheckedChildren="Disabled"
                    />
                    <Text style={{ marginLeft: 8 }}>Enable IP whitelist</Text>
                  </Form.Item>
                  <Form.Item label="Allowed IP Addresses">
                    <TextArea
                      rows={4}
                      placeholder="192.168.1.1&#10;10.0.0.1&#10;..."
                      value={securitySettings.ip_whitelist.join('\n')}
                      onChange={(e) => setSecuritySettings(prev => ({
                        ...prev, 
                        ip_whitelist: e.target.value.split('\n').filter(ip => ip.trim())
                      }))}
                      disabled={!securitySettings.ip_whitelist_enabled}
                    />
                  </Form.Item>
                </Form>
              </Card>
            </Col>
          </Row>

          <Card title="Audit Log" style={{ marginTop: 16 }}>
            <div style={{ marginBottom: 16 }}>
              <Switch
                checked={securitySettings.audit_log_enabled}
                onChange={(checked) => setSecuritySettings(prev => ({...prev, audit_log_enabled: checked}))}
                checkedChildren="Enabled"
                unCheckedChildren="Disabled"
              />
              <Text style={{ marginLeft: 8 }}>Enable audit logging</Text>
            </div>
            <Table
              columns={auditLogColumns}
              dataSource={auditLogData}
              size="small"
              pagination={{ pageSize: 5 }}
            />
          </Card>
        </TabPane>

        {/* System Settings */}
        <TabPane tab={
          <span>
            <DatabaseOutlined />
            System
          </span>
        } key="system">
          <Row gutter={16}>
            <Col span={12}>
              <Card title="Logging Configuration">
                <Form layout="vertical">
                  <Form.Item label="Log Level">
                    <Select
                      value={systemSettings.log_level}
                      onChange={(value) => setSystemSettings(prev => ({...prev, log_level: value}))}
                      style={{ width: '100%' }}
                    >
                      <Option value="DEBUG">DEBUG</Option>
                      <Option value="INFO">INFO</Option>
                      <Option value="WARNING">WARNING</Option>
                      <Option value="ERROR">ERROR</Option>
                    </Select>
                  </Form.Item>
                  <Form.Item label="Max Log Files">
                    <InputNumber
                      min={5}
                      max={100}
                      value={systemSettings.max_log_files}
                      onChange={(value) => setSystemSettings(prev => ({...prev, max_log_files: value || 10}))}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                  <Form.Item>
                    <Switch
                      checked={systemSettings.debug_mode}
                      onChange={(checked) => setSystemSettings(prev => ({...prev, debug_mode: checked}))}
                      checkedChildren="Debug On"
                      unCheckedChildren="Debug Off"
                    />
                    <Text style={{ marginLeft: 8 }}>Enable debug mode</Text>
                  </Form.Item>
                </Form>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="Database Backup">
                <Form layout="vertical">
                  <Form.Item>
                    <Switch
                      checked={systemSettings.database_backup_enabled}
                      onChange={(checked) => setSystemSettings(prev => ({...prev, database_backup_enabled: checked}))}
                      checkedChildren="Enabled"
                      unCheckedChildren="Disabled"
                    />
                    <Text style={{ marginLeft: 8 }}>Enable automatic backup</Text>
                  </Form.Item>
                  <Form.Item label="Backup Frequency (hours)">
                    <InputNumber
                      min={1}
                      max={168}
                      value={systemSettings.backup_frequency_hours}
                      onChange={(value) => setSystemSettings(prev => ({...prev, backup_frequency_hours: value || 24}))}
                      style={{ width: '100%' }}
                      disabled={!systemSettings.database_backup_enabled}
                    />
                  </Form.Item>
                  <Form.Item label="Cleanup After (days)">
                    <InputNumber
                      min={1}
                      max={365}
                      value={systemSettings.cleanup_days}
                      onChange={(value) => setSystemSettings(prev => ({...prev, cleanup_days: value || 30}))}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Form>
              </Card>
            </Col>
          </Row>

          <Card title="System Health" style={{ marginTop: 16 }}>
            <Row gutter={16}>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <Progress
                    type="circle"
                    percent={85}
                    format={() => 'CPU'}
                    width={80}
                  />
                  <Text style={{ display: 'block', marginTop: 8 }}>CPU Usage</Text>
                </div>
              </Col>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <Progress
                    type="circle"
                    percent={67}
                    format={() => 'MEM'}
                    width={80}
                    strokeColor="#faad14"
                  />
                  <Text style={{ display: 'block', marginTop: 8 }}>Memory Usage</Text>
                </div>
              </Col>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <Progress
                    type="circle"
                    percent={45}
                    format={() => 'DISK'}
                    width={80}
                    strokeColor="#52c41a"
                  />
                  <Text style={{ display: 'block', marginTop: 8 }}>Disk Usage</Text>
                </div>
              </Col>
            </Row>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default Settings;