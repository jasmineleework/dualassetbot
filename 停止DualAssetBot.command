#!/bin/bash

# DualAsset Bot 停止器
# 双击停止所有服务

# 获取脚本所在目录
cd "$(dirname "$0")"

# 运行停止脚本
bash ./stop_services.sh

# 等待用户确认
echo ""
echo "按任意键关闭窗口..."
read -n 1