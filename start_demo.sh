#!/bin/bash

echo "🚀 启动 DualAssetBot 演示环境..."
echo "================================================"

# 确保数据库已初始化
echo "📊 初始化数据库..."
cd src/main/python && source ../../../venv/bin/activate && python init_db.py
cd ../../..

# 启动后端API服务器
echo "🔧 启动后端API服务器..."
cd src/main/python
source ../../../venv/bin/activate
uvicorn api.main:app --reload --port 8081 --host 0.0.0.0 &
BACKEND_PID=$!
cd ../../..

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 5

# 启动前端开发服务器
echo "🎨 启动前端开发服务器..."
cd src/main/webapp
npm start &
FRONTEND_PID=$!
cd ../../..

echo "================================================"
echo "✅ DualAssetBot 演示环境启动成功！"
echo ""
echo "🌐 前端地址: http://localhost:3010"
echo "🔧 后端API: http://localhost:8081"
echo "📚 API文档: http://localhost:8081/docs"
echo ""
echo "主要功能："
echo "  🤖 AI推荐页面: http://localhost:3010 (点击 AI Recommendations)"
echo "  📊 市场数据: http://localhost:8081/api/v1/market/price/BTCUSDT"
echo "  🎯 AI推荐API: http://localhost:8081/api/v1/dual-investment/ai-recommendations/BTCUSDT"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "================================================"

# 等待用户中断
trap "echo ''; echo '🛑 正在停止所有服务...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" INT
wait