# 🚀 Dual Asset Bot - 运行指南

## 快速启动

### 1. 启动 API 服务器

**方法一：使用启动脚本（推荐）**
```bash
./start_api.sh
```

**方法二：手动启动**
```bash
source venv/bin/activate
cd src/main/python
uvicorn api.main:app --reload
```

服务器启动后会显示：
```
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

### 2. 启动前端应用

**方法一：使用启动脚本（推荐）**
```bash
./start_frontend.sh
```

**方法二：手动启动**
```bash
cd src/main/webapp
PORT=3001 npm start
```

前端将在 http://localhost:3001 运行

### 3. 验证服务器运行

打开新的终端窗口，运行：
```bash
python quick_api_test.py
```

或者在浏览器访问：
- API 文档：http://localhost:8080/docs
- 健康检查：http://localhost:8080/health

### 4. 测试核心功能

```bash
python test_core_functions.py
```

## 📊 主要功能测试

### 获取 BTC 价格
```bash
curl http://localhost:8080/api/v1/market/price/BTCUSDT
```

### 获取市场分析
```bash
curl http://localhost:8080/api/v1/market/analysis/BTCUSDT
```

### 获取双币赢产品
```bash
curl http://localhost:8080/api/v1/dual-investment/products
```

### 获取投资建议
```bash
curl http://localhost:8080/api/v1/dual-investment/analyze/BTCUSDT
```

## 🔧 故障排除

### 问题：Connection refused
**解决方案**：确保 API 服务器正在运行（执行 `./start_api.sh`）

### 问题：Binance API 错误
**解决方案**：
1. 检查 `.env` 文件中的 API 密钥是否正确
2. 确保 `BINANCE_TESTNET=True` 用于测试
3. 运行 `python check_config.py` 验证配置

### 问题：Module not found
**解决方案**：确保激活了虚拟环境 (`source venv/bin/activate`)

## 📝 开发模式

在开发时，API 服务器会自动重载代码更改。你可以：

1. 修改代码
2. 保存文件
3. 服务器会自动重启
4. 测试新功能

## 🎯 下一步

1. **查看 API 文档**：http://localhost:8080/docs
2. **开始前端开发**：`./start_frontend.sh` 或 `cd src/main/webapp && PORT=3001 npm start`
3. **配置数据库**：设置 PostgreSQL 和 Redis
4. **部署到生产**：使用 Docker 或云服务

---

**提示**：保持 API 服务器运行，在新的终端窗口中进行测试和开发。