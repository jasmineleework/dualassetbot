#!/bin/bash

echo "🚀 启动 DualAssetBot 完整系统..."
echo "================================================"

# 确保在正确的目录
if [ ! -d "src/main/python" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

# 检查 Redis 是否运行
if ! redis-cli ping > /dev/null 2>&1; then
    echo "🔄 启动 Redis 服务..."
    redis-server --daemonize yes --port 6379 --logfile logs/redis.log
    sleep 2
    
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis 服务启动成功"
    else
        echo "❌ Redis 服务启动失败"
        exit 1
    fi
else
    echo "✅ Redis 服务已在运行"
fi

# 创建必要的目录
mkdir -p logs reports /tmp

# 确保数据库已初始化
echo "📊 初始化数据库..."
cd src/main/python && source ../../../venv/bin/activate && python init_db.py
cd ../../..

echo "🔧 启动后端API服务器 (端口 8081)..."
cd src/main/python
source ../../../venv/bin/activate
uvicorn api.main:app --reload --port 8081 --host 0.0.0.0 &
API_PID=$!
cd ../../..

echo "⏳ 等待API服务启动..."
sleep 5

echo "🔄 启动 Celery Worker (后台任务处理)..."
cd src/main/python
source ../../../venv/bin/activate
celery -A celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=trading,analysis,monitoring,celery \
    --hostname=worker1@%h \
    --pidfile=/tmp/celeryworker.pid \
    --logfile=../../../logs/celery_worker.log &
WORKER_PID=$!
cd ../../..

echo "⏰ 启动 Celery Beat (定时任务调度)..."
cd src/main/python  
source ../../../venv/bin/activate
celery -A celery_app beat \
    --loglevel=info \
    --pidfile=/tmp/celerybeat.pid \
    --logfile=../../../logs/celery_beat.log \
    --schedule=/tmp/celerybeat-schedule &
BEAT_PID=$!
cd ../../..

echo "⏳ 等待Celery服务启动..."
sleep 5

echo "🎨 启动前端开发服务器 (端口 3010)..."
cd src/main/webapp
npm start &
FRONTEND_PID=$!
cd ../../..

echo "================================================"
echo "✅ DualAssetBot 完整系统启动成功！"
echo ""
echo "📱 服务地址："
echo "  🌐 前端界面: http://localhost:3010"
echo "  🔧 后端API: http://localhost:8081"
echo "  📚 API文档: http://localhost:8081/docs"
echo ""
echo "🤖 主要功能："
echo "  📊 AI投资推荐: http://localhost:3010 (点击 AI Recommendations)" 
echo "  🔄 自动交易: 通过API /api/v1/trading/auto-execute 触发"
echo "  📈 任务监控: http://localhost:8081/api/v1/tasks/active"
echo "  💼 投资组合: http://localhost:8081/api/v1/trading/portfolio/summary"
echo ""
echo "⚙️  系统组件："
echo "  🔧 FastAPI Server: PID $API_PID (端口 8081)"
echo "  🔄 Celery Worker: PID $WORKER_PID (后台任务)"
echo "  ⏰ Celery Beat: PID $BEAT_PID (定时任务)"
echo "  🎨 React Frontend: PID $FRONTEND_PID (端口 3010)"
echo "  💾 Redis: $(redis-cli ping 2>/dev/null && echo '运行中' || echo '未运行')"
echo ""
echo "📋 日志文件："
echo "  📊 Celery Worker: logs/celery_worker.log"
echo "  ⏰ Celery Beat: logs/celery_beat.log"
echo "  💾 Redis: logs/redis.log"
echo ""
echo "⚠️  注意: 自动交易默认关闭，需要通过API手动启用"
echo "   启用命令: curl -X POST http://localhost:8081/api/v1/trading/settings -d '{\"enable_automated_trading\": true}' -H 'Content-Type: application/json'"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "================================================"

# 等待用户中断
trap "echo ''; echo '🛑 正在停止所有服务...'; \
      kill $API_PID $WORKER_PID $BEAT_PID $FRONTEND_PID 2>/dev/null; \
      redis-cli shutdown 2>/dev/null; \
      echo '✅ 所有服务已停止'; \
      exit 0" INT

# 保持脚本运行
wait $API_PID 2>/dev/null