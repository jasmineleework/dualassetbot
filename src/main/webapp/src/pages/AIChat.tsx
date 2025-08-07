import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Row,
  Col,
  Input,
  Button,
  Typography,
  Space,
  Divider,
  Tag,
  Alert,
  message,
  Spin,
  Empty,
  Avatar,
  List,
  Tooltip,
  Modal,
  Select,
  Rate,
  Badge,
  Tabs,
  Collapse,
  Timeline
} from 'antd';
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  ClearOutlined,
  SaveOutlined,
  HistoryOutlined,
  QuestionCircleOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  SettingOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  EditOutlined,
  ExportOutlined,
  CopyOutlined,
  LikeOutlined,
  DislikeOutlined
} from '@ant-design/icons';
import { apiService } from '../services/api';
import './AIChat.css';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;
const { TabPane } = Tabs;
const { Panel } = Collapse;

interface ChatMessage {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: string;
  rating?: number;
  suggestions?: string[];
  relatedQuestions?: string[];
  strategyChanges?: StrategyChange[];
}

interface StrategyChange {
  parameter: string;
  oldValue: any;
  newValue: any;
  impact: 'HIGH' | 'MEDIUM' | 'LOW';
  approved?: boolean;
}

interface ChatSession {
  id: string;
  title: string;
  timestamp: string;
  messages: ChatMessage[];
  saved: boolean;
}

interface StrategyParameter {
  name: string;
  value: any;
  type: string;
  description: string;
  editable: boolean;
}

const AIChat: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [sending, setSending] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [strategyParameters, setStrategyParameters] = useState<StrategyParameter[]>([]);
  const [showStrategyModal, setShowStrategyModal] = useState(false);
  const [pendingChanges, setPendingChanges] = useState<StrategyChange[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Predefined quick questions
  const quickQuestions = [
    "解释一下当前的AI评分系统是如何工作的？",
    "为什么AI选择了这个特定的双币赢产品？",
    "当前市场环境下，我应该采用什么样的投资策略？",
    "如何调整风险参数以获得更稳健的收益？",
    "能否解释一下最近的投资决策逻辑？",
    "什么情况下AI会暂停自动交易？",
    "如何优化我的投资组合配置？",
    "当前的市场技术指标显示什么信号？"
  ];

  // Example prompts for different scenarios
  const examplePrompts = {
    strategy: [
      "我想采用更保守的投资策略",
      "增加BTC的投资比重",
      "降低单笔投资金额到1000美元"
    ],
    analysis: [
      "分析BTC最近的价格走势",
      "评估当前市场风险等级",
      "对比BTC和ETH的投资机会"
    ],
    adjustment: [
      "将风险等级调整到3",
      "设置最低APR阈值为15%",
      "限制每日最多3笔交易"
    ],
    learning: [
      "什么是双币赢产品？",
      "解释一下APR和APY的区别",
      "如何理解技术指标RSI？"
    ]
  };

  useEffect(() => {
    // Load initial strategy parameters
    loadStrategyParameters();
    // Load chat history from localStorage
    loadChatHistory();
    // Send welcome message
    sendWelcomeMessage();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadStrategyParameters = async () => {
    // Mock strategy parameters - in real implementation would fetch from backend
    const params: StrategyParameter[] = [
      { name: 'risk_level', value: 5, type: 'number', description: '风险等级 (1-10)', editable: true },
      { name: 'min_apr_threshold', value: 0.15, type: 'percentage', description: '最低APR阈值', editable: true },
      { name: 'max_concurrent_trades', value: 10, type: 'number', description: '最大并发交易数', editable: true },
      { name: 'default_investment_amount', value: 500, type: 'currency', description: '默认投资金额', editable: true },
      { name: 'auto_trading_enabled', value: true, type: 'boolean', description: '自动交易开关', editable: true },
      { name: 'ai_confidence_threshold', value: 0.65, type: 'percentage', description: 'AI置信度阈值', editable: true },
      { name: 'rebalance_frequency', value: 'daily', type: 'select', description: '再平衡频率', editable: true },
      { name: 'stop_loss_percentage', value: 0.10, type: 'percentage', description: '止损百分比', editable: true }
    ];
    setStrategyParameters(params);
  };

  const loadChatHistory = () => {
    const savedSessions = localStorage.getItem('ai_chat_sessions');
    if (savedSessions) {
      setSessions(JSON.parse(savedSessions));
    }
  };

  const saveChatHistory = () => {
    localStorage.setItem('ai_chat_sessions', JSON.stringify(sessions));
  };

  const sendWelcomeMessage = () => {
    const welcomeMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'ai',
      content: `👋 您好！我是您的AI投资策略助手。

我可以帮助您：
• 🎯 理解和调整投资策略参数
• 📊 解释AI评分和决策逻辑
• 💡 提供市场分析和投资建议
• ⚙️ 优化您的投资组合配置

请随时向我提问，或者选择下方的快速问题开始对话。`,
      timestamp: new Date().toISOString(),
      relatedQuestions: quickQuestions.slice(0, 3)
    };
    setMessages([welcomeMessage]);
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || sending) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setSending(true);

    try {
      // Simulate AI response - in real implementation would call backend API
      await new Promise(resolve => setTimeout(resolve, 1500));

      const aiResponse = await generateAIResponse(inputValue);
      setMessages(prev => [...prev, aiResponse]);

      // Check if the response contains strategy changes
      if (aiResponse.strategyChanges && aiResponse.strategyChanges.length > 0) {
        setPendingChanges(aiResponse.strategyChanges);
        setShowStrategyModal(true);
      }

    } catch (error) {
      message.error('Failed to get AI response');
    } finally {
      setSending(false);
    }
  };

  const generateAIResponse = async (userInput: string): Promise<ChatMessage> => {
    const input = userInput.toLowerCase();
    let content = '';
    let suggestions: string[] = [];
    let relatedQuestions: string[] = [];
    let strategyChanges: StrategyChange[] = [];

    // Analyze user intent and generate appropriate response
    if (input.includes('风险') || input.includes('risk')) {
      content = `📊 **关于风险管理的解答**

当前您的风险等级设置为 **${strategyParameters.find(p => p.name === 'risk_level')?.value}/10**。

**风险等级影响以下方面：**
1. **产品选择**：较低风险偏好稳定收益产品，较高风险追求高APR产品
2. **仓位控制**：风险等级决定单笔最大投资占比
3. **止损设置**：自动设置相应的止损阈值

**基于当前市场状况的建议：**
- 市场波动性：中等
- 建议风险等级：4-6
- 原因：当前市场相对稳定，适合平衡风险与收益

您可以说"将风险等级调整到4"来修改此参数。`;
      
      suggestions = ["调整风险等级", "查看历史风险收益比", "了解不同风险等级的区别"];
      relatedQuestions = ["如何评估我的风险承受能力？", "不同风险等级的预期收益是多少？"];

    } else if (input.includes('调整') || input.includes('设置') || input.includes('修改')) {
      // Parse adjustment request
      if (input.includes('风险等级')) {
        const match = input.match(/\d+/);
        if (match) {
          const newValue = parseInt(match[0]);
          strategyChanges = [{
            parameter: 'risk_level',
            oldValue: strategyParameters.find(p => p.name === 'risk_level')?.value,
            newValue: newValue,
            impact: Math.abs(newValue - 5) > 3 ? 'HIGH' : 'MEDIUM'
          }];
          
          content = `⚙️ **策略调整确认**

您希望将风险等级从 **${strategyChanges[0].oldValue}** 调整到 **${newValue}**。

**影响分析：**
${newValue < 4 ? '• 采用更保守的投资策略\n• 降低单笔投资金额\n• 优先选择低风险产品' : 
  newValue > 6 ? '• 采用更激进的投资策略\n• 增加高收益产品配置\n• 提高风险容忍度' :
  '• 平衡风险与收益\n• 适度分散投资\n• 动态调整仓位'}

请确认是否执行此调整。`;
        }
      }
      
    } else if (input.includes('ai评分') || input.includes('评分系统')) {
      content = `🤖 **AI评分系统详解**

我们的AI评分系统综合评估每个投资机会，评分范围0-100。

**评分维度（权重）：**
1. **技术分析 (30%)**
   - RSI、MACD、布林带等指标
   - 支撑位和阻力位分析
   - 成交量和动量指标

2. **市场情绪 (25%)**
   - 恐惧贪婪指数
   - 社交媒体情绪分析
   - 新闻事件影响评估

3. **产品特性 (25%)**
   - APR收益率
   - 行权价格合理性
   - 产品期限匹配度

4. **风险评估 (20%)**
   - 市场波动性
   - 流动性风险
   - 系统性风险因素

**决策阈值：**
- **>75分**：强烈推荐，自动执行
- **65-75分**：推荐，需确认
- **50-65分**：观察，人工决策
- **<50分**：不推荐，自动跳过

当前AI置信度阈值：**${(strategyParameters.find(p => p.name === 'ai_confidence_threshold')?.value * 100).toFixed(0)}%**`;

      suggestions = ["查看最近的AI评分记录", "调整AI置信度阈值", "了解具体产品的评分详情"];
      
    } else if (input.includes('策略') || input.includes('strategy')) {
      content = `📈 **当前投资策略概览**

**核心策略参数：**
${strategyParameters.map(p => `• **${p.description}**: ${
  p.type === 'percentage' ? `${(p.value * 100).toFixed(0)}%` :
  p.type === 'currency' ? `$${p.value}` :
  p.type === 'boolean' ? (p.value ? '开启' : '关闭') :
  p.value
}`).join('\n')}

**策略特点：**
- 风险偏好：${strategyParameters.find(p => p.name === 'risk_level')?.value <= 3 ? '保守型' : 
              strategyParameters.find(p => p.name === 'risk_level')?.value <= 7 ? '平衡型' : '激进型'}
- 投资风格：AI驱动的量化投资
- 再平衡：${strategyParameters.find(p => p.name === 'rebalance_frequency')?.value}

**近期表现：**
- 平均收益率：18.5% APR
- 胜率：73%
- 最大回撤：-5.2%

您可以通过自然语言调整任何参数，例如："将默认投资金额设置为1000美元"。`;

      relatedQuestions = ["如何优化我的策略参数？", "什么策略最适合当前市场？"];
      
    } else {
      // Default response for general questions
      content = `💡 我理解您的问题："${userInput}"

让我为您提供相关信息...

${input.includes('市场') ? '当前市场处于震荡整理阶段，建议采用网格策略或双币赢产品锁定收益。' :
  input.includes('收益') ? '您的累计收益为正，建议继续保持当前策略，适时调整风险敞口。' :
  '基于您的问题，我建议您查看相关的策略参数设置，或咨询具体的投资产品信息。'}

如需更详细的解答，请提供更多上下文信息。`;

      suggestions = quickQuestions.slice(3, 6);
    }

    return {
      id: (Date.now() + 1).toString(),
      type: 'ai',
      content,
      timestamp: new Date().toISOString(),
      suggestions,
      relatedQuestions,
      strategyChanges
    };
  };

  const handleQuickQuestion = (question: string) => {
    setInputValue(question);
    inputRef.current?.focus();
  };

  const handleRateMessage = (messageId: string, rating: number) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, rating } : msg
    ));
    message.success('感谢您的反馈！');
  };

  const handleApplyChanges = () => {
    // Apply the pending strategy changes
    pendingChanges.forEach(change => {
      setStrategyParameters(prev => prev.map(param =>
        param.name === change.parameter ? { ...param, value: change.newValue } : param
      ));
    });
    
    message.success('策略参数已更新');
    setShowStrategyModal(false);
    setPendingChanges([]);
  };

  const handleExportChat = () => {
    const chatContent = messages.map(msg => 
      `[${new Date(msg.timestamp).toLocaleString()}] ${msg.type === 'user' ? 'User' : 'AI'}: ${msg.content}`
    ).join('\n\n');
    
    const blob = new Blob([chatContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ai-chat-${new Date().toISOString().split('T')[0]}.txt`;
    link.click();
    URL.revokeObjectURL(url);
    
    message.success('对话已导出');
  };

  const handleClearChat = () => {
    Modal.confirm({
      title: '清空对话',
      content: '确定要清空当前对话吗？此操作不可恢复。',
      okText: '确定',
      cancelText: '取消',
      onOk: () => {
        setMessages([]);
        sendWelcomeMessage();
        message.success('对话已清空');
      }
    });
  };

  return (
    <div className="ai-chat-container">
      <Row gutter={16}>
        {/* Main Chat Area */}
        <Col span={18}>
          <Card className="ai-chat-main">
            <div className="ai-chat-header">
              <Space>
                <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff' }} />
                <div>
                  <Title level={4} style={{ margin: 0 }}>AI策略助手</Title>
                  <Text type="secondary">智能投资策略对话系统</Text>
                </div>
              </Space>
              <Space>
                <Tooltip title="导出对话">
                  <Button icon={<ExportOutlined />} onClick={handleExportChat} />
                </Tooltip>
                <Tooltip title="清空对话">
                  <Button icon={<ClearOutlined />} onClick={handleClearChat} />
                </Tooltip>
              </Space>
            </div>

            <Divider />

            <div className="ai-chat-messages">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`ai-chat-message ${message.type === 'user' ? 'user-message' : 'ai-message'}`}
                >
                  <Avatar
                    icon={message.type === 'user' ? <UserOutlined /> : <RobotOutlined />}
                    style={{
                      backgroundColor: message.type === 'user' ? '#87d068' : '#1890ff',
                      flexShrink: 0
                    }}
                  />
                  <div className="message-content">
                    <div className="message-bubble">
                      <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {message.content}
                      </Paragraph>
                      
                      {message.suggestions && message.suggestions.length > 0 && (
                        <div className="message-suggestions">
                          <Text type="secondary" style={{ fontSize: '12px' }}>建议操作：</Text>
                          <Space wrap style={{ marginTop: 8 }}>
                            {message.suggestions.map((suggestion, index) => (
                              <Tag
                                key={index}
                                color="blue"
                                style={{ cursor: 'pointer' }}
                                onClick={() => handleQuickQuestion(suggestion)}
                              >
                                {suggestion}
                              </Tag>
                            ))}
                          </Space>
                        </div>
                      )}
                      
                      {message.relatedQuestions && message.relatedQuestions.length > 0 && (
                        <div className="related-questions">
                          <Text type="secondary" style={{ fontSize: '12px' }}>相关问题：</Text>
                          {message.relatedQuestions.map((question, index) => (
                            <div
                              key={index}
                              className="related-question-item"
                              onClick={() => handleQuickQuestion(question)}
                            >
                              <QuestionCircleOutlined /> {question}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <div className="message-meta">
                      <Text type="secondary" style={{ fontSize: '11px' }}>
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </Text>
                      {message.type === 'ai' && (
                        <Space style={{ marginLeft: 16 }}>
                          <Tooltip title="有帮助">
                            <Button
                              type="text"
                              size="small"
                              icon={<LikeOutlined />}
                              onClick={() => handleRateMessage(message.id, 5)}
                              style={{
                                color: message.rating === 5 ? '#52c41a' : undefined
                              }}
                            />
                          </Tooltip>
                          <Tooltip title="没帮助">
                            <Button
                              type="text"
                              size="small"
                              icon={<DislikeOutlined />}
                              onClick={() => handleRateMessage(message.id, 1)}
                              style={{
                                color: message.rating === 1 ? '#f5222d' : undefined
                              }}
                            />
                          </Tooltip>
                          <Tooltip title="复制">
                            <Button
                              type="text"
                              size="small"
                              icon={<CopyOutlined />}
                              onClick={() => {
                                navigator.clipboard.writeText(message.content);
                                message.success('已复制到剪贴板');
                              }}
                            />
                          </Tooltip>
                        </Space>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              {sending && (
                <div className="ai-chat-message ai-message">
                  <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff' }} />
                  <div className="message-content">
                    <div className="message-bubble">
                      <Spin size="small" />
                      <Text style={{ marginLeft: 8 }}>AI正在思考...</Text>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            <div className="ai-chat-input">
              <TextArea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onPressEnter={(e) => {
                  if (!e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="输入您的问题或指令... (Shift+Enter换行)"
                autoSize={{ minRows: 2, maxRows: 4 }}
                disabled={sending}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSendMessage}
                loading={sending}
                disabled={!inputValue.trim()}
                style={{ marginTop: 8 }}
              >
                发送
              </Button>
            </div>
          </Card>
        </Col>

        {/* Side Panel */}
        <Col span={6}>
          <Card title="快速操作" size="small" style={{ marginBottom: 16 }}>
            <Collapse defaultActiveKey={['prompts']} ghost>
              <Panel header="示例提示" key="prompts">
                <Tabs defaultActiveKey="strategy" size="small">
                  <TabPane tab="策略" key="strategy">
                    <Space direction="vertical" style={{ width: '100%' }}>
                      {examplePrompts.strategy.map((prompt, index) => (
                        <Button
                          key={index}
                          size="small"
                          block
                          onClick={() => handleQuickQuestion(prompt)}
                        >
                          {prompt}
                        </Button>
                      ))}
                    </Space>
                  </TabPane>
                  <TabPane tab="分析" key="analysis">
                    <Space direction="vertical" style={{ width: '100%' }}>
                      {examplePrompts.analysis.map((prompt, index) => (
                        <Button
                          key={index}
                          size="small"
                          block
                          onClick={() => handleQuickQuestion(prompt)}
                        >
                          {prompt}
                        </Button>
                      ))}
                    </Space>
                  </TabPane>
                  <TabPane tab="调整" key="adjustment">
                    <Space direction="vertical" style={{ width: '100%' }}>
                      {examplePrompts.adjustment.map((prompt, index) => (
                        <Button
                          key={index}
                          size="small"
                          block
                          onClick={() => handleQuickQuestion(prompt)}
                        >
                          {prompt}
                        </Button>
                      ))}
                    </Space>
                  </TabPane>
                </Tabs>
              </Panel>
            </Collapse>
          </Card>

          <Card title="当前策略参数" size="small">
            <List
              size="small"
              dataSource={strategyParameters.slice(0, 5)}
              renderItem={(param) => (
                <List.Item>
                  <div style={{ width: '100%' }}>
                    <Text strong style={{ fontSize: '12px' }}>{param.description}</Text>
                    <div>
                      <Text type="secondary" style={{ fontSize: '11px' }}>
                        {param.type === 'percentage' ? `${(param.value * 100).toFixed(0)}%` :
                         param.type === 'currency' ? `$${param.value}` :
                         param.type === 'boolean' ? (param.value ? '开启' : '关闭') :
                         param.value}
                      </Text>
                      {param.editable && (
                        <EditOutlined
                          style={{ marginLeft: 8, fontSize: '11px', cursor: 'pointer', color: '#1890ff' }}
                          onClick={() => handleQuickQuestion(`调整${param.description}`)}
                        />
                      )}
                    </div>
                  </div>
                </List.Item>
              )}
            />
            <Button
              type="link"
              size="small"
              icon={<SettingOutlined />}
              onClick={() => handleQuickQuestion('查看所有策略参数')}
              style={{ marginTop: 8 }}
            >
              查看全部参数
            </Button>
          </Card>
        </Col>
      </Row>

      {/* Strategy Change Confirmation Modal */}
      <Modal
        title="策略调整确认"
        visible={showStrategyModal}
        onOk={handleApplyChanges}
        onCancel={() => {
          setShowStrategyModal(false);
          setPendingChanges([]);
        }}
        okText="确认调整"
        cancelText="取消"
      >
        <Alert
          message="以下策略参数将被修改"
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <List
          dataSource={pendingChanges}
          renderItem={(change) => (
            <List.Item>
              <div style={{ width: '100%' }}>
                <Text strong>{change.parameter}</Text>
                <div>
                  <Text type="secondary">原值: </Text>
                  <Text>{change.oldValue}</Text>
                  <Text type="secondary"> → </Text>
                  <Text type="success" strong>{change.newValue}</Text>
                </div>
                <Tag color={
                  change.impact === 'HIGH' ? 'red' :
                  change.impact === 'MEDIUM' ? 'orange' : 'green'
                }>
                  {change.impact} 影响
                </Tag>
              </div>
            </List.Item>
          )}
        />
      </Modal>
    </div>
  );
};

export default AIChat;