# DualAsset Bot - Frontend

## 功能特性

### 已完成功能

#### Phase 1: 前端核心页面 ✅
- **Dashboard** - 实时交易仪表板，显示价格、市场分析、机器人状态
- **Portfolio** - 投资组合管理，查看所有投资状态和收益
- **Auto Trading** - 自动交易控制面板，AI推荐和安全控制
- **System Monitor** - 系统监控，Celery任务、健康检查、性能指标
- **Reports** - 投资历史报告，分析和导出功能
- **Settings** - 完整的系统配置管理
- **Market Analysis** - 高级市场分析，技术指标和新闻情绪

#### Phase 2: AI功能 ✅
- **AI Chat** - 自然语言对话界面，策略讨论和参数调整
- **Market Report** - 自动生成的市场分析报告，包含投资逻辑解释

#### Phase 3.1: 实时数据 ✅
- **WebSocket** - 实时价格更新、交易执行、系统警报
- **Connection Indicator** - 连接状态指示器
- **Real-time Updates** - 所有页面支持实时数据更新

## 安装和运行

### 前置要求
- Node.js 16+
- npm 或 yarn

### 安装依赖
```bash
cd src/main/webapp
npm install
```

### 开发环境运行
```bash
npm start
```
应用将在 http://localhost:3010 启动

### 生产构建
```bash
npm run build
```

### 环境变量配置
创建 `.env` 文件：
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=localhost:8000
REACT_APP_AUTO_CONNECT_WS=true
```

## 技术栈
- React 18 + TypeScript
- Ant Design 5 组件库
- WebSocket 实时通信
- Recharts 数据可视化

## 项目结构
```
src/
├── components/      # 可复用组件
│   ├── ConnectionIndicator  # WebSocket连接指示器
│   └── MarketReport         # 市场报告组件
├── hooks/          # 自定义React Hooks
│   └── useWebSocket.ts      # WebSocket hooks
├── pages/          # 页面组件
│   ├── Dashboard.tsx        # 仪表板
│   ├── Portfolio.tsx        # 投资组合
│   ├── AutoTrading.tsx      # 自动交易
│   ├── SystemMonitor.tsx    # 系统监控
│   ├── Reports.tsx          # 报告分析
│   ├── Settings.tsx         # 系统设置
│   ├── MarketAnalysis.tsx   # 市场分析
│   ├── AIChat.tsx           # AI对话
│   └── AIRecommendations.tsx # AI推荐
├── services/       # API服务
│   ├── api.ts              # REST API
│   └── websocket.ts        # WebSocket服务
└── App.tsx         # 主应用组件
```

## 核心功能说明

### AI自然语言调试区
- 支持中文对话
- 策略参数自然语言调整
- AI评分系统解释
- 投资决策逻辑查询

### 市场分析报告
- 每次交易前自动生成
- 包含K线分析、技术指标
- 市场新闻情绪分析
- 投资逻辑详细解释
- 支持PDF/HTML导出

### WebSocket实时数据
- 价格实时更新
- 交易执行通知
- 系统警报推送
- 投资组合变化
- AI推荐更新

## 后续开发计划
- [ ] Phase 3.2: 移动端响应式优化
- [ ] Phase 3.3: 高级数据可视化图表
- [ ] 暗黑模式支持
- [ ] 多语言国际化

## 联系方式
如有问题请提交Issue或联系开发团队。