# 🚀 Dual Asset Bot - 快速启动指南

## 端口配置
- **API 服务器**: 8080
- **前端应用**: 3001

## 一键启动

### 1️⃣ 启动 API 服务器（终端 1）
```bash
./start_api.sh
```

### 2️⃣ 启动前端应用（终端 2）
```bash
./start_frontend.sh
```

## 访问地址

- **前端界面**: http://localhost:3001
- **API 文档**: http://localhost:8080/docs
- **健康检查**: http://localhost:8080/health

## 手动启动方式

### API 服务器
```bash
source venv/bin/activate
cd src/main/python
uvicorn api.main:app --reload --port 8080
```

### 前端应用
```bash
cd src/main/webapp
PORT=3001 npm start
```

## 测试

### 测试 API
```bash
python quick_api_test.py
```

### 测试核心功能
```bash
python test_core_functions.py
```

## 常见问题

### Q: 端口被占用？
A: 修改 `.env` 文件中的 `API_PORT` 或前端的 `PORT` 设置

### Q: API 连接失败？
A: 确保 API 服务器正在运行，检查 http://localhost:8080/health

### Q: 前端无法获取数据？
A: 检查浏览器控制台，确保 API 服务器已启动

---

💡 **提示**: 保持两个终端窗口分别运行 API 和前端服务