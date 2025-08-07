import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Table, 
  Tag, 
  Button, 
  Modal, 
  message, 
  Spin, 
  Alert,
  Typography,
  Space,
  Tabs,
  Progress,
  Tooltip,
  Popconfirm
} from 'antd';
import { 
  DollarOutlined,
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
  SyncOutlined,
  StopOutlined,
  EyeOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { apiService, PortfolioSummary, Investment } from '../services/api';
import './Portfolio.css';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const Portfolio: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [portfolioSummary, setPortfolioSummary] = useState<PortfolioSummary | null>(null);
  const [allInvestments, setAllInvestments] = useState<Investment[]>([]);
  const [error, setError] = useState<string>('');
  const [selectedInvestment, setSelectedInvestment] = useState<Investment | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [cancellingId, setCancellingId] = useState<string>('');

  const fetchData = async () => {
    try {
      setRefreshing(true);
      setError('');

      // Fetch portfolio summary and recent investments using allSettled
      const results = await Promise.allSettled([
        apiService.getPortfolioSummary(),
        apiService.getInvestments(undefined, 50, 0)
      ]);

      if (results[0].status === 'fulfilled') {
        setPortfolioSummary(results[0].value);
      }
      
      if (results[1].status === 'fulfilled') {
        setAllInvestments(results[1].value.investments);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load portfolio data';
      setError(errorMsg);
      message.error(errorMsg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleCancelInvestment = async (investmentId: string) => {
    try {
      setCancellingId(investmentId);
      const result = await apiService.cancelInvestment(investmentId, 'User requested cancellation');
      message.success(`Investment cancellation initiated. Task ID: ${result.task_id}`);
      // Refresh data after a short delay to see the updated status
      setTimeout(fetchData, 2000);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to cancel investment';
      message.error(errorMsg);
    } finally {
      setCancellingId('');
    }
  };

  const showInvestmentDetail = (investment: Investment) => {
    setSelectedInvestment(investment);
    setDetailModalVisible(true);
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'PENDING': 'processing',
      'ACTIVE': 'success',
      'COMPLETED': 'default',
      'FAILED': 'error',
      'CANCELLED': 'warning'
    };
    return colors[status] || 'default';
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      'PENDING': '待处理',
      'ACTIVE': '活跃',
      'COMPLETED': '已完成',
      'FAILED': '失败',
      'CANCELLED': '已取消'
    };
    return texts[status] || status;
  };

  const getReturnColor = (returnValue: number | undefined) => {
    if (!returnValue) return '#666';
    return returnValue > 0 ? '#52c41a' : '#f5222d';
  };

  const investmentColumns = [
    {
      title: 'Product ID',
      dataIndex: 'product_id',
      key: 'product_id',
      render: (text: string) => (
        <Text code style={{ fontSize: '12px' }}>{text}</Text>
      ),
      width: 200,
    },
    {
      title: 'Amount',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => (
        <Text strong>${amount.toFixed(2)}</Text>
      ),
      sorter: (a: Investment, b: Investment) => a.amount - b.amount,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      ),
      filters: [
        { text: '待处理', value: 'PENDING' },
        { text: '活跃', value: 'ACTIVE' },
        { text: '已完成', value: 'COMPLETED' },
        { text: '失败', value: 'FAILED' },
        { text: '已取消', value: 'CANCELLED' },
      ],
      onFilter: (value: any, record: Investment) => record.status === value,
    },
    {
      title: 'Expected Return',
      dataIndex: 'expected_return',
      key: 'expected_return',
      render: (returnRate: number | undefined) => 
        returnRate ? (
          <Text style={{ color: getReturnColor(returnRate) }}>
            {(returnRate * 100).toFixed(2)}%
          </Text>
        ) : <Text type="secondary">-</Text>,
    },
    {
      title: 'Actual Return',
      dataIndex: 'actual_return',
      key: 'actual_return',
      render: (returnValue: number | undefined, record: Investment) => {
        if (returnValue !== undefined) {
          const percentage = (returnValue / record.amount) * 100;
          return (
            <Text style={{ color: getReturnColor(returnValue) }}>
              ${returnValue.toFixed(2)} ({percentage.toFixed(2)}%)
            </Text>
          );
        }
        return <Text type="secondary">-</Text>;
      },
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => (
        <Text>{new Date(date).toLocaleString()}</Text>
      ),
      sorter: (a: Investment, b: Investment) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      defaultSortOrder: 'descend' as const,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Investment) => (
        <Space size="small">
          <Button 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => showInvestmentDetail(record)}
          >
            Details
          </Button>
          {record.status === 'ACTIVE' && (
            <Popconfirm
              title="Are you sure you want to cancel this investment?"
              onConfirm={() => handleCancelInvestment(record.id)}
              okText="Yes"
              cancelText="No"
            >
              <Button 
                size="small" 
                danger
                icon={<StopOutlined />}
                loading={cancellingId === record.id}
              >
                Cancel
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
      width: 150,
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', marginTop: 100 }}>
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>Loading portfolio...</p>
      </div>
    );
  }

  if (error && !portfolioSummary) {
    return (
      <Alert
        message="Error Loading Portfolio"
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

  const summary = portfolioSummary?.summary;
  const statusBreakdown = portfolioSummary?.status_breakdown;

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>
          <TrophyOutlined style={{ color: '#faad14', marginRight: 8 }} />
          Investment Portfolio
        </Title>
        <Button 
          icon={<SyncOutlined spin={refreshing} />} 
          onClick={fetchData}
          loading={refreshing}
        >
          Refresh
        </Button>
      </div>

      {/* Portfolio Summary Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Invested"
              value={summary?.total_invested || 0}
              prefix="$"
              precision={2}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Current Value"
              value={summary?.current_value || 0}
              prefix="$"
              precision={2}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Returns"
              value={summary?.total_returns || 0}
              prefix="$"
              precision={2}
              valueStyle={{ 
                color: (summary?.total_returns || 0) >= 0 ? '#52c41a' : '#f5222d' 
              }}
              suffix={
                (summary?.total_returns || 0) >= 0 ? 
                <RiseOutlined /> : <FallOutlined />
              }
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="ROI"
              value={summary?.roi_percentage || 0}
              precision={2}
              suffix="%"
              valueStyle={{ 
                color: (summary?.roi_percentage || 0) >= 0 ? '#52c41a' : '#f5222d' 
              }}
              prefix={<DollarOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Status Breakdown */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="Investment Status Overview">
            <Row gutter={16}>
              <Col span={4}>
                <Statistic
                  title="Total Investments"
                  value={(statusBreakdown?.active || 0) + (statusBreakdown?.completed || 0) + (statusBreakdown?.pending || 0) + (statusBreakdown?.failed || 0) + (statusBreakdown?.cancelled || 0)}
                  valueStyle={{ fontSize: '24px' }}
                />
              </Col>
              <Col span={4}>
                <Statistic
                  title="Active"
                  value={statusBreakdown?.active || 0}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col span={4}>
                <Statistic
                  title="Completed"
                  value={statusBreakdown?.completed || 0}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={4}>
                <Statistic
                  title="Pending"
                  value={statusBreakdown?.pending || 0}
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
              <Col span={4}>
                <Statistic
                  title="Failed"
                  value={statusBreakdown?.failed || 0}
                  valueStyle={{ color: '#f5222d' }}
                />
              </Col>
              <Col span={4}>
                <Statistic
                  title="Cancelled"
                  value={statusBreakdown?.cancelled || 0}
                  valueStyle={{ color: '#d9d9d9' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Investments Table */}
      <Card 
        title="Investment History" 
        extra={
          <Text type="secondary">
            Total: {allInvestments.length} investments
          </Text>
        }
      >
        <Table
          columns={investmentColumns}
          dataSource={allInvestments}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} investments`,
          }}
          scroll={{ x: true }}
        />
      </Card>

      {/* Investment Detail Modal */}
      <Modal
        title="Investment Details"
        visible={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            Close
          </Button>
        ]}
        width={600}
      >
        {selectedInvestment && (
          <div>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Text strong>Product ID:</Text>
                <br />
                <Text code>{selectedInvestment.product_id}</Text>
              </Col>
              <Col span={12}>
                <Text strong>Status:</Text>
                <br />
                <Tag color={getStatusColor(selectedInvestment.status)}>
                  {getStatusText(selectedInvestment.status)}
                </Tag>
              </Col>
            </Row>
            
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Text strong>Amount:</Text>
                <br />
                <Text>${selectedInvestment.amount.toFixed(2)}</Text>
              </Col>
              <Col span={12}>
                <Text strong>Expected Return:</Text>
                <br />
                <Text>
                  {selectedInvestment.expected_return ? 
                    `${(selectedInvestment.expected_return * 100).toFixed(2)}%` : 'N/A'}
                </Text>
              </Col>
            </Row>

            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Text strong>Created At:</Text>
                <br />
                <Text>{new Date(selectedInvestment.created_at).toLocaleString()}</Text>
              </Col>
              <Col span={12}>
                <Text strong>Executed At:</Text>
                <br />
                <Text>
                  {selectedInvestment.executed_at ? 
                    new Date(selectedInvestment.executed_at).toLocaleString() : 'Not executed'}
                </Text>
              </Col>
            </Row>

            {selectedInvestment.actual_return !== undefined && (
              <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={24}>
                  <Text strong>Actual Return:</Text>
                  <br />
                  <Text style={{ color: getReturnColor(selectedInvestment.actual_return), fontSize: '16px' }}>
                    ${selectedInvestment.actual_return.toFixed(2)} 
                    ({((selectedInvestment.actual_return / selectedInvestment.amount) * 100).toFixed(2)}%)
                  </Text>
                </Col>
              </Row>
            )}

            {selectedInvestment.binance_order_id && (
              <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={24}>
                  <Text strong>Binance Order ID:</Text>
                  <br />
                  <Text code>{selectedInvestment.binance_order_id}</Text>
                </Col>
              </Row>
            )}

            {selectedInvestment.error_message && (
              <Row gutter={16}>
                <Col span={24}>
                  <Text strong>Error Message:</Text>
                  <br />
                  <Text type="danger">{selectedInvestment.error_message}</Text>
                </Col>
              </Row>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Portfolio;