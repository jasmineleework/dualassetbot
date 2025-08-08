#!/bin/bash

# DualAsset Bot 一键启动脚本
# 启动后端和前端服务，并自动打开浏览器

echo "🚀 DualAsset Bot 启动器"
echo "================================"

# 设置项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Python环境
echo -e "${YELLOW}检查 Python 环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python3 已安装${NC}"

# 检查Node.js环境
echo -e "${YELLOW}检查 Node.js 环境...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js 已安装${NC}"

# 创建日志目录
mkdir -p "$PROJECT_ROOT/logs"

# 终止已存在的服务
echo -e "${YELLOW}停止已运行的服务...${NC}"
pkill -f "uvicorn api.main:app" 2>/dev/null
pkill -f "npm start" 2>/dev/null
lsof -ti:8081 | xargs kill -9 2>/dev/null
lsof -ti:3010 | xargs kill -9 2>/dev/null
sleep 2

# 启动后端服务
echo -e "${YELLOW}启动后端服务 (端口 8081)...${NC}"
cd "$PROJECT_ROOT/src/main/python"

# 安装Python依赖（如果需要）
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements-minimal.txt
else
    source venv/bin/activate
fi

# 启动FastAPI
nohup uvicorn api.main:app --reload --port 8081 > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ 后端服务已启动 (PID: $BACKEND_PID)${NC}"

# 等待后端启动
echo -e "${YELLOW}等待后端服务就绪...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8081/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 后端服务就绪${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ 后端服务启动超时${NC}"
        exit 1
    fi
done

# 启动前端服务
echo -e "${YELLOW}启动前端服务 (端口 3010)...${NC}"
cd "$PROJECT_ROOT/src/main/webapp"

# 安装前端依赖（如果需要）
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

# 启动React应用
nohup npm start > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"

# 保存PID到文件
echo "$BACKEND_PID" > "$PROJECT_ROOT/logs/backend.pid"
echo "$FRONTEND_PID" > "$PROJECT_ROOT/logs/frontend.pid"

# 等待前端启动
echo -e "${YELLOW}等待前端服务就绪...${NC}"
for i in {1..60}; do
    if curl -s http://localhost:3010 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 前端服务就绪${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 60 ]; then
        echo -e "${RED}❌ 前端服务启动超时${NC}"
        exit 1
    fi
done

# 打开浏览器
echo -e "${YELLOW}打开浏览器...${NC}"
sleep 2
open http://localhost:3010

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}🎉 DualAsset Bot 已成功启动！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "访问地址："
echo "  前端界面: http://localhost:3010"
echo "  后端API: http://localhost:8081"
echo "  API文档: http://localhost:8081/docs"
echo ""
echo "查看日志："
echo "  后端日志: tail -f $PROJECT_ROOT/logs/backend.log"
echo "  前端日志: tail -f $PROJECT_ROOT/logs/frontend.log"
echo ""
echo "停止服务："
echo "  运行: $PROJECT_ROOT/stop_services.sh"
echo ""
echo -e "${YELLOW}按 Ctrl+C 退出（服务将继续在后台运行）${NC}"

# 保持脚本运行以查看输出
tail -f "$PROJECT_ROOT/logs/backend.log" "$PROJECT_ROOT/logs/frontend.log"