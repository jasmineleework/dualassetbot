#!/bin/bash

# DualAsset Bot 服务停止脚本

echo "🛑 停止 DualAsset Bot 服务"
echo "================================"

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 读取PID文件
if [ -f "$PROJECT_ROOT/logs/backend.pid" ]; then
    BACKEND_PID=$(cat "$PROJECT_ROOT/logs/backend.pid")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID
        echo -e "${GREEN}✅ 后端服务已停止 (PID: $BACKEND_PID)${NC}"
    fi
    rm "$PROJECT_ROOT/logs/backend.pid"
fi

if [ -f "$PROJECT_ROOT/logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$PROJECT_ROOT/logs/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID
        echo -e "${GREEN}✅ 前端服务已停止 (PID: $FRONTEND_PID)${NC}"
    fi
    rm "$PROJECT_ROOT/logs/frontend.pid"
fi

# 强制终止相关进程
echo -e "${YELLOW}清理残留进程...${NC}"
pkill -f "uvicorn api.main:app" 2>/dev/null
pkill -f "npm start" 2>/dev/null
lsof -ti:8081 | xargs kill -9 2>/dev/null
lsof -ti:3010 | xargs kill -9 2>/dev/null

echo -e "${GREEN}✅ 所有服务已停止${NC}"