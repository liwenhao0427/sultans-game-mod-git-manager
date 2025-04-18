#!/bin/bash

# 苏丹的游戏 MOD 管理器 - Mac 启动脚本

# 检查 Python 环境
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "错误: 未找到 Python。请安装 Python 3.x 后再试。"
    exit 1
fi

# 检查必要的依赖
echo "检查依赖..."
$PYTHON_CMD -c "import tkinter" 2>/dev/null || {
    echo "警告: 未找到 tkinter 模块。"
    echo "请安装 tkinter: brew install python-tk"
    exit 1
}

# 启动 MOD 管理器
echo "启动苏丹的游戏 MOD 管理器..."
$PYTHON_CMD "mod_installer_gui.py"