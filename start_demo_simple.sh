#!/bin/bash

echo "🚀 启动 DualAssetBot 简单演示..."
echo "================================================"

# 检查是否在正确目录
if [ ! -f "demo.html" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

# 确保数据库已初始化
echo "📊 初始化数据库..."
cd src/main/python
source ../../../venv/bin/activate
python init_db.py
echo "✅ 数据库初始化完成"

# 启动后端API服务器
echo "🔧 启动后端API服务器..."
python -m uvicorn api.main:app --reload --port 8081 --host 0.0.0.0 &
BACKEND_PID=$!
cd ../../..

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 8

# 测试后端连接
echo "🧪 测试后端连接..."
if curl -f -s http://localhost:8081/api/v1/market/price/BTCUSDT > /dev/null; then
    echo "✅ 后端API响应正常"
else
    echo "⚠️  后端API可能还在启动中..."
fi

# 打开演示页面
echo "🌐 打开演示页面..."
if command -v open &> /dev/null; then
    open demo.html
elif command -v xdg-open &> /dev/null; then
    xdg-open demo.html
else
    echo "请手动打开 demo.html 文件"
fi

echo "================================================"
echo "✅ DualAssetBot 演示环境启动成功！"
echo ""
echo "📱 演示页面: demo.html (应该已自动打开)"
echo "🔧 后端API: http://localhost:8081"
echo "📚 API文档: http://localhost:8081/docs"
echo ""
echo "主要测试功能："
echo "  🤖 AI推荐: 在演示页面点击'刷新推荐'"
echo "  📊 市场数据: http://localhost:8081/api/v1/market/price/BTCUSDT"
echo "  🎯 AI推荐API: http://localhost:8081/api/v1/dual-investment/ai-recommendations/BTCUSDT"
echo ""
echo "按 Ctrl+C 停止后端服务"
echo "================================================"

# 等待用户中断
trap "echo ''; echo '🛑 正在停止后端服务...'; kill $BACKEND_PID 2>/dev/null; echo '✅ 服务已停止'; exit 0" INT

# 保持脚本运行
wait $BACKEND_PID 2>/dev/null