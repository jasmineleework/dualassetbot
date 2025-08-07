#!/bin/bash

echo "⏰ 启动 Celery Beat (定时任务调度器)..."
echo "================================================"

# 确保在正确的目录
if [ ! -d "src/main/python" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

# 检查 Redis 是否运行
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis 服务未运行，请先启动 Redis"
    echo "   启动命令: redis-server"
    exit 1
fi

cd src/main/python
source ../../../venv/bin/activate

echo "✅ 激活虚拟环境"
echo "⏰ 启动 Celery Beat 调度器..."

# 创建日志目录
mkdir -p ../../../logs

# 启动 Celery Beat 进程
celery -A celery_app beat \
    --loglevel=info \
    --pidfile=/tmp/celerybeat.pid \
    --logfile=../../../logs/celery_beat.log \
    --schedule=/tmp/celerybeat-schedule

echo "================================================"
echo "⏰ Celery Beat 已停止"