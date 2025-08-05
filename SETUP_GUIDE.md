# 快速设置指南 - Dual Asset Bot

## Python 环境设置

### 1. 创建虚拟环境（推荐）

```bash
# 在项目根目录执行
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### 2. 安装 Python 依赖

```bash
# 确保在虚拟环境中
cd src/main/python
python3 -m pip install -r requirements.txt
```

### 3. 安装前端依赖

```bash
# 新开一个终端窗口
cd src/main/webapp
npm install
```

## 运行项目

### 启动后端服务

```bash
# 在虚拟环境中
cd src/main/python
python3 -m uvicorn api.main:app --reload --port 8000
```

### 启动前端服务

```bash
# 新终端窗口
cd src/main/webapp
npm start
```

## 常见问题

### 如果遇到 pip 命令找不到
使用 `python3 -m pip` 代替 `pip`

### 如果遇到权限问题
使用 `python3 -m pip install --user -r requirements.txt`

### 检查安装是否成功
```bash
python3 -m pip list
```