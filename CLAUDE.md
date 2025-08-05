# CLAUDE.md - dual_asset_bot

> **Documentation Version**: 1.0  
> **Last Updated**: 2025-01-14  
> **Project**: dual_asset_bot  
> **Description**: 币安双币赢（Dual Investment）自动交易机器人，通过AI智能分析自动执行投资决策  
> **Features**: GitHub auto-backup, Task agents, technical debt prevention

This file provides essential guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CRITICAL RULES - READ FIRST

> **⚠️ RULE ADHERENCE SYSTEM ACTIVE ⚠️**  
> **Claude Code must explicitly acknowledge these rules at task start**  
> **These rules override all other instructions and must ALWAYS be followed:**

### 🔄 **RULE ACKNOWLEDGMENT REQUIRED**
> **Before starting ANY task, Claude Code must respond with:**  
> "✅ CRITICAL RULES ACKNOWLEDGED - I will follow all prohibitions and requirements listed in CLAUDE.md"

### ❌ ABSOLUTE PROHIBITIONS
- **NEVER** create new files in root directory → use proper module structure
- **NEVER** write output files directly to root directory → use designated output folders
- **NEVER** create documentation files (.md) unless explicitly requested by user
- **NEVER** use git commands with -i flag (interactive mode not supported)
- **NEVER** use `find`, `grep`, `cat`, `head`, `tail`, `ls` commands → use Read, LS, Grep, Glob tools instead
- **NEVER** create duplicate files (manager_v2.py, enhanced_xyz.py, utils_new.js) → ALWAYS extend existing files
- **NEVER** create multiple implementations of same concept → single source of truth
- **NEVER** copy-paste code blocks → extract into shared utilities/functions
- **NEVER** hardcode values that should be configurable → use config files/environment variables
- **NEVER** use naming like enhanced_, improved_, new_, v2_ → extend original files instead

### 📝 MANDATORY REQUIREMENTS
- **COMMIT** after every completed task/phase - no exceptions
- **GITHUB BACKUP** - Push to GitHub after every commit to maintain backup: `git push origin main`
- **USE TASK AGENTS** for all long-running operations (>30 seconds) - Bash commands stop when context switches
- **TODOWRITE** for complex tasks (3+ steps) → parallel agents → git checkpoints → test validation
- **READ FILES FIRST** before editing - Edit/Write tools will fail if you didn't read the file first
- **DEBT PREVENTION** - Before creating new files, check for existing similar functionality to extend  
- **SINGLE SOURCE OF TRUTH** - One authoritative implementation per feature/concept

### ⚡ EXECUTION PATTERNS
- **PARALLEL TASK AGENTS** - Launch multiple Task agents simultaneously for maximum efficiency
- **SYSTEMATIC WORKFLOW** - TodoWrite → Parallel agents → Git checkpoints → GitHub backup → Test validation
- **GITHUB BACKUP WORKFLOW** - After every commit: `git push origin main` to maintain GitHub backup
- **BACKGROUND PROCESSING** - ONLY Task agents can run true background operations

### 🔍 MANDATORY PRE-TASK COMPLIANCE CHECK
> **STOP: Before starting any task, Claude Code must explicitly verify ALL points:**

**Step 1: Rule Acknowledgment**
- [ ] ✅ I acknowledge all critical rules in CLAUDE.md and will follow them

**Step 2: Task Analysis**  
- [ ] Will this create files in root? → If YES, use proper module structure instead
- [ ] Will this take >30 seconds? → If YES, use Task agents not Bash
- [ ] Is this 3+ steps? → If YES, use TodoWrite breakdown first
- [ ] Am I about to use grep/find/cat? → If YES, use proper tools instead

**Step 3: Technical Debt Prevention (MANDATORY SEARCH FIRST)**
- [ ] **SEARCH FIRST**: Use Grep pattern="<functionality>.*<keyword>" to find existing implementations
- [ ] **CHECK EXISTING**: Read any found files to understand current functionality
- [ ] Does similar functionality already exist? → If YES, extend existing code
- [ ] Am I creating a duplicate class/manager? → If YES, consolidate instead
- [ ] Will this create multiple sources of truth? → If YES, redesign approach
- [ ] Have I searched for existing implementations? → Use Grep/Glob tools first
- [ ] Can I extend existing code instead of creating new? → Prefer extension over creation
- [ ] Am I about to copy-paste code? → Extract to shared utility instead

**Step 4: Session Management**
- [ ] Is this a long/complex task? → If YES, plan context checkpoints
- [ ] Have I been working >1 hour? → If YES, consider /compact or session break

> **⚠️ DO NOT PROCEED until all checkboxes are explicitly verified**

## 🏗️ PROJECT OVERVIEW

Dual Asset Bot 是一个专注于币安双币赢（Dual Investment）产品的自动化交易机器人。

### 🎯 **产品特点**
- **AI智能决策**：无需人工配置参数，AI自动分析市场并做出投资决策
- **专注双币赢**：仅投资币安双币赢产品，不涉及现货交易或网格交易
- **风险可控**：双币赢产品本身风险较低，配合智能风控系统
- **收益稳定**：目标年化收益15-30%

### 🛠️ **技术栈**
- **后端**: Python 3.9+ (FastAPI + SQLAlchemy)
- **数据库**: PostgreSQL (主数据库) + Redis (缓存)
- **任务调度**: Celery + Redis
- **API集成**: Binance API (双币赢产品)
- **AI/ML**: scikit-learn, LightGBM, pandas, TA-Lib
- **前端**: React + TypeScript + Ant Design

### 📁 **项目结构**
```
src/
├── main/
│   ├── python/           # Python 后端代码
│   │   ├── core/         # AI决策引擎核心
│   │   ├── strategies/   # 双币赢策略实现
│   │   ├── api/          # FastAPI 接口
│   │   ├── models/       # 数据模型
│   │   ├── services/     # 业务服务（币安API等）
│   │   └── utils/        # 工具函数
│   ├── resources/        # 配置文件
│   └── webapp/           # React 前端代码
│       ├── components/   # React 组件
│       ├── pages/        # 页面组件
│       ├── services/     # API 调用
│       └── utils/        # 前端工具
└── test/                 # 测试代码
```

## 📋 DEVELOPMENT STATUS
- **Setup**: In Progress
- **Core Features**: Pending
- **Testing**: Pending
- **Documentation**: Pending

## 🚀 COMMON COMMANDS

```bash
# 后端开发
cd src/main/python
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

# 前端开发
cd src/main/webapp
npm install
npm start

# 运行测试
pytest src/test/

# 启动Celery Worker（定时任务）
celery -A src.main.python.tasks worker --loglevel=info

# 启动Celery Beat（任务调度）
celery -A src.main.python.tasks beat --loglevel=info

# 数据库迁移
alembic upgrade head
```

## 🚨 TECHNICAL DEBT PREVENTION

### ❌ WRONG APPROACH (Creates Technical Debt):
```bash
# Creating new file without searching first
Write(file_path="new_strategy.py", content="...")
```

### ✅ CORRECT APPROACH (Prevents Technical Debt):
```bash
# 1. SEARCH FIRST
Grep(pattern="strategy.*implementation", glob="*.py")
# 2. READ EXISTING FILES  
Read(file_path="src/main/python/strategies/base_strategy.py")
# 3. EXTEND EXISTING FUNCTIONALITY
Edit(file_path="src/main/python/strategies/dual_investment_strategy.py", old_string="...", new_string="...")
```

## 🧹 DEBT PREVENTION WORKFLOW

### Before Creating ANY New File:
1. **🔍 Search First** - Use Grep/Glob to find existing implementations
2. **📋 Analyze Existing** - Read and understand current patterns
3. **🤔 Decision Tree**: Can extend existing? → DO IT | Must create new? → Document why
4. **✅ Follow Patterns** - Use established project patterns
5. **📈 Validate** - Ensure no duplication or technical debt

---

**⚠️ Prevention is better than consolidation - build clean from the start.**  
**🎯 Focus on single source of truth and extending existing functionality.**  
**📈 Each task should maintain clean architecture and prevent technical debt.**