# Dual Asset Bot - 币安双币赢自动交易机器人

## 📋 项目简介

Dual Asset Bot 是一个专注于币安双币赢（Dual Investment）产品的自动化交易机器人。通过AI智能分析市场数据，自动判断最佳的申购时机和产品类型，无需人工配置复杂参数，实现稳定的投资收益。

## 🚀 核心功能

### 1. **AI智能决策**
- 自动分析K线形态、成交量、市场情绪
- 基于机器学习模型预测短期价格走势
- 智能选择低买（Buy Low）或高卖（Sell High）策略
- 自动确定最优行权价格和申购金额

### 2. **自动化执行**
- 每日定时分析市场并执行投资决策
- 自动申购双币赢产品
- 到期自动结算并重新投资
- 完全无需人工干预

### 3. **策略回测**
- 基于历史数据验证策略效果
- 计算历史收益率、胜率等指标
- 生成详细的回测报告

### 4. **实时监控**
- 实时查看账户资产和收益
- 监控运行中的双币赢产品
- 查看AI决策记录和分析报告

### 5. **风险控制**
- 智能仓位管理
- 动态风险评估
- 异常市场自动暂停

## 🛠️ 技术架构

- **后端**: Python 3.9+ (FastAPI + SQLAlchemy)
- **数据库**: PostgreSQL + Redis
- **任务调度**: Celery
- **AI/ML**: scikit-learn, LightGBM, pandas
- **API**: Binance API
- **前端**: React + TypeScript + Ant Design

## 📦 快速开始

### 环境要求
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/[your-username]/dual_asset_bot.git
cd dual_asset_bot
```

2. **设置Python虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装后端依赖**
```bash
cd src/main/python
pip install -r requirements.txt
```

4. **安装前端依赖**
```bash
cd src/main/webapp
npm install
```

5. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置信息
```

6. **初始化数据库**
```bash
alembic upgrade head
```

### 运行项目

> **重要**: 请查看 [PORT_CONFIG.md](PORT_CONFIG.md) 了解端口配置详情

1. **启动后端服务**
```bash
cd src/main/python
uvicorn api.main:app --reload --port 8000  # 固定使用端口8000
```

2. **启动Celery Worker（另开终端）**
```bash
celery -A src.main.python.tasks worker --loglevel=info
```

3. **启动Celery Beat（另开终端）**
```bash
celery -A src.main.python.tasks beat --loglevel=info
```

4. **启动前端（另开终端）**
```bash
cd src/main/webapp
npm start  # 将在端口3010运行（配置在.env中）
```

访问 http://localhost:3010 即可使用系统。

## 🔑 币安API配置

1. 登录[币安](https://www.binance.com/)
2. 进入API管理页面
3. 创建新的API密钥
4. 开启"Enable Spot & Margin Trading"权限
5. 将API Key和Secret Key配置到 `.env` 文件

⚠️ **安全提示**: 
- 不要将API密钥提交到Git仓库
- 建议使用IP白名单限制
- 定期更换API密钥

## 📊 双币赢产品说明

### 低买（Buy Low）
- 持有USDT，设定目标价格买入加密货币
- 到期时：
  - 如果市场价格 ≤ 目标价格：使用USDT买入加密货币
  - 如果市场价格 > 目标价格：保留USDT并获得利息

### 高卖（Sell High）
- 持有加密货币，设定目标价格卖出
- 到期时：
  - 如果市场价格 ≥ 目标价格：卖出加密货币获得USDT
  - 如果市场价格 < 目标价格：保留加密货币并获得利息

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

在提交代码前，请：
1. 阅读 `CLAUDE.md` 了解项目规范
2. 运行测试确保代码质量
3. 遵循现有的代码风格

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## ⚠️ 风险提示

- 加密货币投资存在风险，请谨慎投资
- 本软件仅供学习交流，使用者需自行承担投资风险
- 建议先使用小额资金测试策略效果

## 📞 联系方式

如有问题或建议，请提交 [Issue](https://github.com/[your-username]/dual_asset_bot/issues)。

---

**开发提示**: 
- 开发前请先阅读 `CLAUDE.md` 文件
- 遵循项目的目录结构规范
- 使用Task agents处理长时间运行的任务