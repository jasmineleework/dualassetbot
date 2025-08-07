import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  DatePicker,
  Select,
  Button,
  Table,
  Statistic,
  Typography,
  Space,
  Divider,
  Tag,
  Progress,
  Alert,
  message,
  Spin,
  Empty,
  Tooltip,
  Modal,
  Timeline,
  Tabs,
  Badge
} from 'antd';
import {
  FileTextOutlined,
  DownloadOutlined,
  EyeOutlined,
  CalendarOutlined,
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  LineChartOutlined,
  BarChartOutlined,
  PieChartOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import {
  apiService,
  Investment,
  PortfolioSummary
} from '../services/api';
import './Reports.css';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;
const { TabPane } = Tabs;

interface ReportData {
  summary: {
    total_investments: number;
    total_amount: number;
    total_returns: number;
    success_rate: number;
    average_return: number;
    best_performing: Investment | null;
    worst_performing: Investment | null;
  };
  performance_by_month: Array<{
    month: string;
    investments: number;
    returns: number;
    success_rate: number;
  }>;
  performance_by_asset: Array<{
    asset: string;
    investments: number;
    total_amount: number;
    returns: number;
    roi: number;
  }>;
  recent_activities: Investment[];
}

const Reports: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [reportLoading, setReportLoading] = useState(false);
  const [investments, setInvestments] = useState<Investment[]>([]);
  const [portfolioSummary, setPortfolioSummary] = useState<PortfolioSummary | null>(null);
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [selectedDateRange, setSelectedDateRange] = useState<[Date, Date] | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [reportModalVisible, setReportModalVisible] = useState(false);
  const [selectedInvestment, setSelectedInvestment] = useState<Investment | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const results = await Promise.allSettled([
        apiService.getInvestments(undefined, 100, 0),
        apiService.getPortfolioSummary()
      ]);

      let investments = [];
      if (results[0].status === 'fulfilled') {
        investments = results[0].value.investments;
        setInvestments(investments);
      }
      
      if (results[1].status === 'fulfilled') {
        setPortfolioSummary(results[1].value);
      }
      
      generateReportData(investments);

    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to load reports data';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const generateReportData = (investmentData: Investment[]) => {
    const completedInvestments = investmentData.filter(inv => inv.status === 'COMPLETED');
    
    // Summary calculations
    const totalAmount = completedInvestments.reduce((sum, inv) => sum + inv.amount, 0);
    const totalReturns = completedInvestments.reduce((sum, inv) => sum + (inv.actual_return || 0), 0);
    const successRate = completedInvestments.length > 0 ? 
      (completedInvestments.filter(inv => (inv.actual_return || 0) > 0).length / completedInvestments.length) * 100 : 0;
    const averageReturn = completedInvestments.length > 0 ? totalReturns / completedInvestments.length : 0;
    
    const bestPerforming = completedInvestments.reduce((best, inv) => 
      (inv.actual_return || 0) > (best?.actual_return || -Infinity) ? inv : best, null as Investment | null);
    
    const worstPerforming = completedInvestments.reduce((worst, inv) => 
      (inv.actual_return || 0) < (worst?.actual_return || Infinity) ? inv : worst, null as Investment | null);

    // Performance by month (mock data for now)
    const performanceByMonth = [
      { month: '2024-01', investments: 12, returns: 2500, success_rate: 75 },
      { month: '2024-02', investments: 15, returns: 3200, success_rate: 80 },
      { month: '2024-03', investments: 18, returns: 3800, success_rate: 78 },
      { month: '2024-04', investments: 10, returns: 2100, success_rate: 70 },
    ];

    // Performance by asset
    const assetGroups = completedInvestments.reduce((groups, inv) => {
      const asset = inv.product_id.substring(0, 3); // Extract asset from product_id
      if (!groups[asset]) {
        groups[asset] = { investments: 0, total_amount: 0, returns: 0 };
      }
      groups[asset].investments += 1;
      groups[asset].total_amount += inv.amount;
      groups[asset].returns += (inv.actual_return || 0);
      return groups;
    }, {} as Record<string, { investments: number; total_amount: number; returns: number }>);

    const performanceByAsset = Object.entries(assetGroups).map(([asset, data]) => ({
      asset,
      investments: data.investments,
      total_amount: data.total_amount,
      returns: data.returns,
      roi: data.total_amount > 0 ? (data.returns / data.total_amount) * 100 : 0
    }));

    const report: ReportData = {
      summary: {
        total_investments: completedInvestments.length,
        total_amount: totalAmount,
        total_returns: totalReturns,
        success_rate: successRate,
        average_return: averageReturn,
        best_performing: bestPerforming,
        worst_performing: worstPerforming
      },
      performance_by_month: performanceByMonth,
      performance_by_asset: performanceByAsset,
      recent_activities: investmentData.slice(0, 10)
    };

    setReportData(report);
  };

  const handleGenerateReport = async () => {
    try {
      setReportLoading(true);
      // In a real implementation, this would call a backend API to generate a detailed report
      message.success('Report generated successfully');
      // Mock delay
      await new Promise(resolve => setTimeout(resolve, 2000));
    } catch (error) {
      message.error('Failed to generate report');
    } finally {
      setReportLoading(false);
    }
  };

  const handleExportReport = async (format: 'pdf' | 'excel') => {
    try {
      message.loading(`Exporting report as ${format.toUpperCase()}...`, 2);
      // In a real implementation, this would call a backend API to export the report
      await new Promise(resolve => setTimeout(resolve, 2000));
      message.success(`Report exported as ${format.toUpperCase()} successfully`);
    } catch (error) {
      message.error('Failed to export report');
    }
  };

  const getStatusIcon = (status: string) => {
    const icons = {
      'COMPLETED': <CheckCircleOutlined style={{ color: '#52c41a' }} />,
      'ACTIVE': <InfoCircleOutlined style={{ color: '#1890ff' }} />,
      'PENDING': <ExclamationCircleOutlined style={{ color: '#faad14' }} />,
      'FAILED': <CloseCircleOutlined style={{ color: '#f5222d' }} />,
      'CANCELLED': <CloseCircleOutlined style={{ color: '#d9d9d9' }} />
    };
    return icons[status as keyof typeof icons] || <InfoCircleOutlined />;
  };

  const getStatusColor = (status: string) => {
    const colors = {
      'COMPLETED': 'success',
      'ACTIVE': 'processing',
      'PENDING': 'warning',
      'FAILED': 'error',
      'CANCELLED': 'default'
    };
    return colors[status as keyof typeof colors] || 'default';
  };

  const investmentColumns = [
    {
      title: 'Investment ID',
      dataIndex: 'id',
      key: 'id',
      render: (text: string) => (
        <Text code style={{ fontSize: '11px' }}>{text.substring(0, 8)}...</Text>
      ),
    },
    {
      title: 'Product',
      dataIndex: 'product_id',
      key: 'product_id',
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: 'Amount',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => <Text strong>${amount.toFixed(2)}</Text>,
      sorter: (a: Investment, b: Investment) => a.amount - b.amount,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
          {status}
        </Tag>
      ),
      filters: [
        { text: 'COMPLETED', value: 'COMPLETED' },
        { text: 'ACTIVE', value: 'ACTIVE' },
        { text: 'PENDING', value: 'PENDING' },
        { text: 'FAILED', value: 'FAILED' },
        { text: 'CANCELLED', value: 'CANCELLED' },
      ],
      onFilter: (value: any, record: Investment) => record.status === value,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => (
        <Text type="secondary">{new Date(date).toLocaleDateString()}</Text>
      ),
      sorter: (a: Investment, b: Investment) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: 'Return',
      dataIndex: 'actual_return',
      key: 'actual_return',
      render: (returnAmount: number | undefined, record: Investment) => {
        if (record.status !== 'COMPLETED' || !returnAmount) {
          return <Text type="secondary">-</Text>;
        }
        const isPositive = returnAmount > 0;
        return (
          <Text type={isPositive ? 'success' : 'danger'}>
            {isPositive ? '+' : ''}${returnAmount.toFixed(2)}
          </Text>
        );
      },
      sorter: (a: Investment, b: Investment) => 
        (a.actual_return || 0) - (b.actual_return || 0),
    },
    {
      title: 'ROI',
      key: 'roi',
      render: (_: any, record: Investment) => {
        if (record.status !== 'COMPLETED' || !record.actual_return) {
          return <Text type="secondary">-</Text>;
        }
        const roi = (record.actual_return / record.amount) * 100;
        const isPositive = roi > 0;
        return (
          <Text type={isPositive ? 'success' : 'danger'}>
            {isPositive ? '+' : ''}{roi.toFixed(2)}%
          </Text>
        );
      },
    },
    {
      title: 'Action',
      key: 'action',
      render: (_: any, record: Investment) => (
        <Button
          type="link"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => {
            setSelectedInvestment(record);
            setReportModalVisible(true);
          }}
        >
          View
        </Button>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', marginTop: 100 }}>
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>Loading reports...</p>
      </div>
    );
  }

  return (
    <div className="reports-container">
      <div className="reports-header">
        <Title level={2}>
          <FileTextOutlined style={{ color: '#1890ff', marginRight: 8 }} />
          Investment Reports & Analytics
        </Title>
        <Space>
          <Button
            type="primary"
            icon={<LineChartOutlined />}
            loading={reportLoading}
            onClick={handleGenerateReport}
          >
            Generate Report
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => handleExportReport('excel')}
          >
            Export Excel
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => handleExportReport('pdf')}
          >
            Export PDF
          </Button>
        </Space>
      </div>

      {/* Performance Overview */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Investments"
              value={reportData?.summary.total_investments || 0}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Invested"
              value={reportData?.summary.total_amount || 0}
              prefix={<DollarOutlined />}
              precision={2}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Returns"
              value={reportData?.summary.total_returns || 0}
              prefix={reportData && reportData.summary.total_returns >= 0 ? <RiseOutlined /> : <FallOutlined />}
              precision={2}
              valueStyle={{ 
                color: reportData && reportData.summary.total_returns >= 0 ? '#52c41a' : '#f5222d' 
              }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Success Rate"
              value={reportData?.summary.success_rate || 0}
              suffix="%"
              precision={1}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Best and Worst Performing */}
      {reportData?.summary.best_performing && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={12}>
            <Card title="Best Performing Investment" size="small">
              <Space>
                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                <Text code>{reportData.summary.best_performing.product_id}</Text>
                <Text type="success">
                  +${(reportData.summary.best_performing.actual_return || 0).toFixed(2)}
                </Text>
              </Space>
            </Card>
          </Col>
          <Col span={12}>
            <Card title="Worst Performing Investment" size="small">
              <Space>
                <ExclamationCircleOutlined style={{ color: '#f5222d' }} />
                <Text code>{reportData.summary.worst_performing?.product_id || 'N/A'}</Text>
                <Text type="danger">
                  ${(reportData.summary.worst_performing?.actual_return || 0).toFixed(2)}
                </Text>
              </Space>
            </Card>
          </Col>
        </Row>
      )}

      {/* Detailed Analytics */}
      <Tabs defaultActiveKey="investments">
        <TabPane tab={`Investment History (${investments.length})`} key="investments">
          <Card>
            <div style={{ marginBottom: 16 }}>
              <Space>
                <RangePicker
                  placeholder={['Start Date', 'End Date']}
                  onChange={(dates) => setSelectedDateRange(dates ? [dates[0]?.toDate() || new Date(), dates[1]?.toDate() || new Date()] : null)}
                />
                <Select
                  placeholder="Filter by Status"
                  style={{ width: 150 }}
                  value={selectedStatus}
                  onChange={setSelectedStatus}
                >
                  <Option value="all">All Status</Option>
                  <Option value="COMPLETED">Completed</Option>
                  <Option value="ACTIVE">Active</Option>
                  <Option value="PENDING">Pending</Option>
                  <Option value="FAILED">Failed</Option>
                  <Option value="CANCELLED">Cancelled</Option>
                </Select>
                <Button icon={<CalendarOutlined />}>
                  Apply Filters
                </Button>
              </Space>
            </div>
            <Table
              columns={investmentColumns}
              dataSource={investments}
              rowKey="id"
              size="small"
              pagination={{ 
                pageSize: 20, 
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => 
                  `${range[0]}-${range[1]} of ${total} investments`
              }}
              scroll={{ x: true }}
            />
          </Card>
        </TabPane>

        <TabPane tab="Performance by Asset" key="performance">
          <Card>
            {reportData?.performance_by_asset.length ? (
              <Table
                dataSource={reportData.performance_by_asset}
                rowKey="asset"
                size="small"
                pagination={false}
                columns={[
                  {
                    title: 'Asset',
                    dataIndex: 'asset',
                    key: 'asset',
                    render: (text: string) => <Text strong>{text}</Text>,
                  },
                  {
                    title: 'Investments',
                    dataIndex: 'investments',
                    key: 'investments',
                  },
                  {
                    title: 'Total Amount',
                    dataIndex: 'total_amount',
                    key: 'total_amount',
                    render: (amount: number) => <Text>${amount.toFixed(2)}</Text>,
                  },
                  {
                    title: 'Total Returns',
                    dataIndex: 'returns',
                    key: 'returns',
                    render: (returns: number) => (
                      <Text type={returns >= 0 ? 'success' : 'danger'}>
                        {returns >= 0 ? '+' : ''}${returns.toFixed(2)}
                      </Text>
                    ),
                  },
                  {
                    title: 'ROI',
                    dataIndex: 'roi',
                    key: 'roi',
                    render: (roi: number) => (
                      <Text type={roi >= 0 ? 'success' : 'danger'}>
                        {roi >= 0 ? '+' : ''}{roi.toFixed(2)}%
                      </Text>
                    ),
                  },
                ]}
              />
            ) : (
              <Empty description="No performance data available" />
            )}
          </Card>
        </TabPane>

        <TabPane tab="Recent Activities" key="activities">
          <Card>
            <Timeline>
              {reportData?.recent_activities.map((activity, index) => (
                <Timeline.Item
                  key={activity.id}
                  color={getStatusColor(activity.status)}
                  dot={getStatusIcon(activity.status)}
                >
                  <div>
                    <Text strong>{activity.product_id}</Text>
                    <Tag 
                      color={getStatusColor(activity.status)} 
                      style={{ marginLeft: 8 }}
                    >
                      {activity.status}
                    </Tag>
                    <br />
                    <Text type="secondary">
                      Amount: ${activity.amount.toFixed(2)}
                    </Text>
                    <br />
                    <Text type="secondary">
                      {new Date(activity.created_at).toLocaleString()}
                    </Text>
                    {activity.actual_return && (
                      <>
                        <br />
                        <Text type={activity.actual_return >= 0 ? 'success' : 'danger'}>
                          Return: {activity.actual_return >= 0 ? '+' : ''}${activity.actual_return.toFixed(2)}
                        </Text>
                      </>
                    )}
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </TabPane>
      </Tabs>

      {/* Investment Detail Modal */}
      <Modal
        title="Investment Details"
        visible={reportModalVisible}
        onCancel={() => {
          setReportModalVisible(false);
          setSelectedInvestment(null);
        }}
        footer={null}
        width={600}
      >
        {selectedInvestment && (
          <div>
            <Row gutter={16}>
              <Col span={12}>
                <Card size="small" title="Basic Information">
                  <p><strong>ID:</strong> {selectedInvestment.id}</p>
                  <p><strong>Product:</strong> {selectedInvestment.product_id}</p>
                  <p><strong>Amount:</strong> ${selectedInvestment.amount.toFixed(2)}</p>
                  <p>
                    <strong>Status:</strong>{' '}
                    <Tag color={getStatusColor(selectedInvestment.status)}>
                      {selectedInvestment.status}
                    </Tag>
                  </p>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" title="Performance">
                  <p><strong>Expected Return:</strong> ${(selectedInvestment.expected_return || 0).toFixed(2)}</p>
                  <p><strong>Actual Return:</strong> ${(selectedInvestment.actual_return || 0).toFixed(2)}</p>
                  {selectedInvestment.actual_return && (
                    <p>
                      <strong>ROI:</strong>{' '}
                      <Text type={selectedInvestment.actual_return >= 0 ? 'success' : 'danger'}>
                        {((selectedInvestment.actual_return / selectedInvestment.amount) * 100).toFixed(2)}%
                      </Text>
                    </p>
                  )}
                </Card>
              </Col>
            </Row>
            <Card size="small" title="Timeline" style={{ marginTop: 16 }}>
              <Timeline>
                <Timeline.Item color="blue">
                  <strong>Created:</strong> {new Date(selectedInvestment.created_at).toLocaleString()}
                </Timeline.Item>
                {selectedInvestment.executed_at && (
                  <Timeline.Item color="green">
                    <strong>Executed:</strong> {new Date(selectedInvestment.executed_at).toLocaleString()}
                  </Timeline.Item>
                )}
                {selectedInvestment.completed_at && (
                  <Timeline.Item color="red">
                    <strong>Completed:</strong> {new Date(selectedInvestment.completed_at).toLocaleString()}
                  </Timeline.Item>
                )}
              </Timeline>
            </Card>
            {selectedInvestment.error_message && (
              <Alert
                message="Error Details"
                description={selectedInvestment.error_message}
                type="error"
                style={{ marginTop: 16 }}
              />
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Reports;