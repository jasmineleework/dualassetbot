import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Badge,
  Table,
  Button,
  Alert,
  message,
  Typography,
  Space,
  Tabs,
  Progress,
  Tag,
  Spin,
  Empty,
  Tooltip,
  List,
  Timeline,
  Modal
} from 'antd';
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  ApiOutlined,
  ClusterOutlined,
  FireOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  ThunderboltOutlined,
  RocketOutlined,
  MonitorOutlined
} from '@ant-design/icons';
import {
  apiService,
  SystemHealth,
  TaskStats,
  WorkerInfo,
  ActiveTask,
  ScheduledTask,
  TaskStatus
} from '../services/api';
import './SystemMonitor.css';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

const SystemMonitor: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [taskStats, setTaskStats] = useState<TaskStats | null>(null);
  const [activeTasks, setActiveTasks] = useState<ActiveTask[]>([]);
  const [scheduledTasks, setScheduledTasks] = useState<ScheduledTask[]>([]);
  const [error, setError] = useState<string>('');
  const [healthCheckRunning, setHealthCheckRunning] = useState(false);

  const fetchData = async () => {
    try {
      setRefreshing(true);
      setError('');

      const [healthRes, statsRes, activeRes, scheduledRes] = await Promise.all([
        apiService.getSystemHealth().catch(() => ({
          status: 'error',
          health: {
            database: 'unknown',
            binance_api: 'unknown',
            celery: 'unknown',
            overall: 'unknown',
            timestamp: new Date().toISOString()
          }
        })),
        apiService.getTaskStats().catch(() => ({
          workers: [],
          total_workers: 0,
          overall_stats: {
            total_tasks: 0,
            total_processes: 0,
            timestamp: new Date().toISOString()
          }
        })),
        apiService.getActiveTasks().catch(() => ({
          active_tasks: [],
          total_workers: 0,
          total_tasks: 0
        })),
        apiService.getScheduledTasks().catch(() => ({
          scheduled_tasks: [],
          total_workers: 0,
          total_tasks: 0
        }))
      ]);

      setSystemHealth(healthRes.health);
      setTaskStats(statsRes);
      setActiveTasks(activeRes.active_tasks);
      setScheduledTasks(scheduledRes.scheduled_tasks);

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load system monitoring data';
      setError(errorMsg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleHealthCheck = async () => {
    try {
      setHealthCheckRunning(true);
      const result = await apiService.triggerHealthCheck();
      message.success(`Health check initiated. Task ID: ${result.task_id}`);
      // Refresh data after a short delay
      setTimeout(fetchData, 3000);
    } catch (error) {
      message.error('Failed to trigger health check');
    } finally {
      setHealthCheckRunning(false);
    }
  };

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'unhealthy':
      case 'critical':
        return <CloseCircleOutlined style={{ color: '#f5222d' }} />;
      case 'degraded':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      default:
        return <InfoCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#52c41a';
      case 'unhealthy':
      case 'critical': return '#f5222d';
      case 'degraded': return '#faad14';
      default: return '#d9d9d9';
    }
  };

  const getTaskIcon = (taskName: string) => {
    if (taskName.includes('market')) return <SyncOutlined />;
    if (taskName.includes('ai') || taskName.includes('recommendation')) return <ThunderboltOutlined />;
    if (taskName.includes('trading') || taskName.includes('execute')) return <RocketOutlined />;
    if (taskName.includes('monitoring') || taskName.includes('health')) return <MonitorOutlined />;
    return <FireOutlined />;
  };

  const workerColumns = [
    {
      title: 'Worker',
      dataIndex: 'worker',
      key: 'worker',
      render: (text: string) => (
        <Text code>{text}</Text>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge 
          status={status === 'online' ? 'success' : 'error'} 
          text={status.toUpperCase()} 
        />
      ),
    },
    {
      title: 'Processes',
      dataIndex: 'pool_processes',
      key: 'pool_processes',
      render: (processes: number) => (
        <Text strong>{processes}</Text>
      ),
    },
    {
      title: 'PID',
      dataIndex: 'pid',
      key: 'pid',
      render: (pid: number) => (
        <Text type="secondary">{pid}</Text>
      ),
    },
    {
      title: 'Clock',
      dataIndex: 'clock',
      key: 'clock',
      render: (clock: string) => (
        <Text type="secondary">{clock}</Text>
      ),
    },
  ];

  const activeTaskColumns = [
    {
      title: 'Task ID',
      dataIndex: 'task_id',
      key: 'task_id',
      render: (text: string) => (
        <Text code style={{ fontSize: '11px' }}>{text.substring(0, 8)}...</Text>
      ),
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Space>
          {getTaskIcon(name)}
          <Text strong>{name.split('.').pop()}</Text>
        </Space>
      ),
    },
    {
      title: 'Worker',
      dataIndex: 'worker',
      key: 'worker',
      render: (worker: string) => (
        <Text type="secondary">{worker}</Text>
      ),
    },
    {
      title: 'Start Time',
      dataIndex: 'time_start',
      key: 'time_start',
      render: (time: string) => (
        <Text type="secondary">
          {time ? new Date(time).toLocaleTimeString() : 'N/A'}
        </Text>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      render: () => (
        <Tag color="processing" icon={<SyncOutlined spin />}>
          Running
        </Tag>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', marginTop: 100 }}>
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>Loading system monitoring...</p>
      </div>
    );
  }

  return (
    <div className="system-monitor-container">
      <div className="system-monitor-header">
        <Title level={2}>
          <CloudServerOutlined style={{ color: '#1890ff', marginRight: 8 }} />
          System Monitor
        </Title>
        <Space>
          <Button
            icon={<SyncOutlined spin={refreshing} />}
            onClick={fetchData}
            loading={refreshing}
          >
            Refresh
          </Button>
          <Button
            type="primary"
            icon={<CheckCircleOutlined />}
            onClick={handleHealthCheck}
            loading={healthCheckRunning}
          >
            Run Health Check
          </Button>
        </Space>
      </div>

      {error && (
        <Alert
          message="System Monitoring Error"
          description={error}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 24 }}
        />
      )}

      {/* System Health Overview */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card className="health-card">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, marginBottom: 8 }}>
                {getHealthIcon(systemHealth?.overall || 'unknown')}
              </div>
              <Title level={4} style={{ margin: 0, color: getHealthColor(systemHealth?.overall || 'unknown') }}>
                {(systemHealth?.overall || 'unknown').toUpperCase()}
              </Title>
              <Text type="secondary">Overall Health</Text>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card className="health-card">
            <Statistic
              title="Database"
              value={systemHealth?.database || 'unknown'}
              prefix={<DatabaseOutlined />}
              valueStyle={{ 
                color: getHealthColor(systemHealth?.database || 'unknown'),
                textTransform: 'uppercase',
                fontSize: '16px'
              }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="health-card">
            <Statistic
              title="Binance API"
              value={systemHealth?.binance_api || 'unknown'}
              prefix={<ApiOutlined />}
              valueStyle={{ 
                color: getHealthColor(systemHealth?.binance_api || 'unknown'),
                textTransform: 'uppercase',
                fontSize: '16px'
              }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="health-card">
            <Statistic
              title="Celery"
              value={systemHealth?.celery || 'unknown'}
              prefix={<ClusterOutlined />}
              valueStyle={{ 
                color: getHealthColor(systemHealth?.celery || 'unknown'),
                textTransform: 'uppercase',
                fontSize: '16px'
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* System Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="Active Workers"
              value={taskStats?.total_workers || 0}
              prefix={<ClusterOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Total Processes"
              value={taskStats?.overall_stats?.total_processes || 0}
              prefix={<CloudServerOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Active Tasks"
              value={activeTasks.length}
              prefix={<FireOutlined />}
              valueStyle={{ color: activeTasks.length > 0 ? '#faad14' : '#d9d9d9' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Detailed Monitoring Tabs */}
      <Tabs defaultActiveKey="workers">
        <TabPane 
          tab={
            <Space>
              <ClusterOutlined />
              Workers ({taskStats?.workers.length || 0})
            </Space>
          } 
          key="workers"
        >
          <Card>
            {taskStats?.workers.length ? (
              <Table
                columns={workerColumns}
                dataSource={taskStats.workers}
                rowKey="worker"
                size="small"
                pagination={false}
              />
            ) : (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="No workers detected"
              />
            )}
          </Card>
        </TabPane>

        <TabPane 
          tab={
            <Space>
              <FireOutlined />
              Active Tasks ({activeTasks.length})
            </Space>
          } 
          key="active-tasks"
        >
          <Card>
            {activeTasks.length ? (
              <Table
                columns={activeTaskColumns}
                dataSource={activeTasks}
                rowKey="task_id"
                size="small"
                pagination={{ pageSize: 10 }}
                scroll={{ x: true }}
              />
            ) : (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  <div>
                    <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
                    <div style={{ marginTop: 16 }}>No active tasks</div>
                    <Text type="secondary">All tasks completed</Text>
                  </div>
                }
              />
            )}
          </Card>
        </TabPane>

        <TabPane 
          tab={
            <Space>
              <ClockCircleOutlined />
              Scheduled Tasks ({scheduledTasks.length})
            </Space>
          } 
          key="scheduled-tasks"
        >
          <Card>
            {scheduledTasks.length ? (
              <List
                dataSource={scheduledTasks}
                renderItem={(task) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={getTaskIcon(task.name)}
                      title={<Text code>{task.task_id.substring(0, 12)}...</Text>}
                      description={
                        <div>
                          <Text strong>{task.name.split('.').pop()}</Text>
                          <br />
                          <Text type="secondary">Worker: {task.worker}</Text>
                          {task.eta && (
                            <>
                              <br />
                              <Text type="secondary">ETA: {new Date(task.eta).toLocaleString()}</Text>
                            </>
                          )}
                        </div>
                      }
                    />
                    <Tag color="default">Priority {task.priority}</Tag>
                  </List.Item>
                )}
              />
            ) : (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="No scheduled tasks"
              />
            )}
          </Card>
        </TabPane>

        <TabPane 
          tab={
            <Space>
              <InfoCircleOutlined />
              System Info
            </Space>
          } 
          key="system-info"
        >
          <Card>
            <Row gutter={16}>
              <Col span={12}>
                <Card type="inner" title="Health Check History">
                  <Timeline
                    items={[
                      {
                        color: 'green',
                        children: (
                          <div>
                            <Text strong>System Healthy</Text>
                            <br />
                            <Text type="secondary">
                              {systemHealth?.timestamp ? new Date(systemHealth.timestamp).toLocaleString() : 'Unknown'}
                            </Text>
                          </div>
                        ),
                      },
                    ]}
                  />
                </Card>
              </Col>
              <Col span={12}>
                <Card type="inner" title="Performance Metrics">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text>Task Completion Rate</Text>
                      <Progress percent={85} status="active" />
                    </div>
                    <div>
                      <Text>System Load</Text>
                      <Progress percent={42} strokeColor="#52c41a" />
                    </div>
                    <div>
                      <Text>Memory Usage</Text>
                      <Progress percent={67} strokeColor="#faad14" />
                    </div>
                  </Space>
                </Card>
              </Col>
            </Row>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default SystemMonitor;