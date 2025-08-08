#!/usr/bin/osascript

-- DualAsset Bot 启动器 AppleScript
-- 可编译为.app应用程序

on run
    set projectPath to POSIX path of ((path to me as text) & "::")
    
    -- 如果是.app运行，获取实际项目路径
    if projectPath contains ".app/Contents/" then
        set projectPath to text 1 thru ((offset of ".app/Contents/" in projectPath) - 1) of projectPath
        set projectPath to POSIX path of (POSIX file projectPath as alias)
        set projectPath to text 1 thru -2 of projectPath -- 移除末尾的/
    end if
    
    set scriptPath to projectPath & "/start_services.sh"
    
    -- 创建启动命令
    set startCommand to "cd " & quoted form of projectPath & " && bash " & quoted form of scriptPath
    
    -- 在新的Terminal窗口中运行
    tell application "Terminal"
        activate
        
        -- 创建新窗口
        do script startCommand
        
        -- 设置窗口标题
        set currentTab to selected tab of front window
        set custom title of currentTab to "DualAsset Bot Server"
        
        -- 调整窗口大小
        set bounds of front window to {100, 100, 1000, 700}
    end tell
    
    -- 显示通知
    display notification "服务正在启动，请稍候..." with title "DualAsset Bot" subtitle "AI智能双币投资机器人"
    
end run