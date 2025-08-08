#!/bin/bash

# 编译AppleScript为.app应用程序

echo "🔨 编译 DualAssetBot.app..."

# 编译AppleScript为应用程序
osacompile -o DualAssetBot.app DualAssetBot.applescript

if [ $? -eq 0 ]; then
    echo "✅ DualAssetBot.app 创建成功！"
    echo ""
    echo "使用方法："
    echo "1. 双击 DualAssetBot.app 启动服务"
    echo "2. 或双击 启动DualAssetBot.command 启动服务"
    echo "3. 双击 停止DualAssetBot.command 停止服务"
    
    # 设置应用图标（如果有的话）
    # 如果你有图标文件，可以取消下面的注释
    # cp icon.icns DualAssetBot.app/Contents/Resources/applet.icns
    
else
    echo "❌ 编译失败"
fi