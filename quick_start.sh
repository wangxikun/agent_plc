#!/bin/bash
# ============================================================
# OpenPLC + Agents4PLC 一键启动脚本
# ============================================================

set -e

echo "🚀 OpenPLC + Agents4PLC 一键启动"
echo "============================================================"
echo ""

# 检查当前目录
if [ ! -f "config.py" ]; then
    echo "❌ 错误: 请在Agents4PLC项目根目录运行此脚本"
    exit 1
fi

# 步骤1: 检查OpenPLC是否已安装
echo "【步骤1】检查OpenPLC安装状态"
echo "------------------------------------------------------------"

if [ ! -d "OpenPLC_v3" ]; then
    echo "⚠️  OpenPLC未安装"
    read -p "是否现在安装? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📥 开始安装OpenPLC..."
        ./setup_openplc.sh
        echo "✅ OpenPLC安装完成"
    else
        echo "❌ 跳过安装，退出"
        exit 1
    fi
else
    echo "✅ OpenPLC已安装"
fi

echo ""

# 步骤2: 检查Python依赖
echo "【步骤2】检查Python依赖"
echo "------------------------------------------------------------"

if python3 -c "import pyModbusTCP" 2>/dev/null; then
    echo "✅ pyModbusTCP已安装"
else
    echo "⚠️  pyModbusTCP未安装"
    read -p "是否现在安装? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip3 install pyModbusTCP
        echo "✅ pyModbusTCP安装完成"
    fi
fi

echo ""

# 步骤3: 生成测试代码
echo "【步骤3】生成ST代码"
echo "------------------------------------------------------------"
read -p "是否生成温度控制测试代码? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⏳ 正在生成..."
    python3 test_openplc_demo.py
    echo "✅ 代码生成完成"
else
    echo "⏭️  跳过代码生成"
fi

echo ""

# 步骤4: 启动OpenPLC
echo "【步骤4】启动OpenPLC服务"
echo "------------------------------------------------------------"
read -p "是否启动OpenPLC服务? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📝 OpenPLC将在新的终端窗口启动"
    echo "   - Web界面: http://localhost:8080"
    echo "   - 用户名: openplc"
    echo "   - 密码: openplc"
    echo ""

    # 在新的Terminal窗口启动OpenPLC
    osascript <<EOF
tell application "Terminal"
    do script "cd '$(pwd)/OpenPLC_v3/webserver' && sudo node server.js"
    activate
end tell
EOF

    echo "✅ OpenPLC服务正在启动..."
    echo "   请在新的终端窗口中查看启动状态"
    echo "   等待5秒后继续..."
    sleep 5
else
    echo "⏭️  跳过启动OpenPLC"
    echo "   你可以手动启动: cd OpenPLC_v3/webserver && sudo node server.js"
fi

echo ""

# 步骤5: 打开Web界面
echo "【步骤5】打开OpenPLC Web界面"
echo "------------------------------------------------------------"
read -p "是否在浏览器中打开OpenPLC? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open http://localhost:8080
    echo "✅ 已打开浏览器"
fi

echo ""

# 完成
echo "============================================================"
echo "🎉 设置完成！"
echo "============================================================"
echo ""
echo "📋 下一步操作:"
echo ""
echo "1️⃣  在浏览器中登录OpenPLC"
echo "   - 访问: http://localhost:8080"
echo "   - 用户名: openplc"
echo "   - 密码: openplc"
echo ""
echo "2️⃣  上传ST代码"
echo "   - 点击左侧 'Programs'"
echo "   - 上传文件: $(pwd)/openplc_temperature_control.st"
echo "   - 点击 'Compile'"
echo ""
echo "3️⃣  启动PLC"
echo "   - 返回 'Dashboard'"
echo "   - 点击 'Start PLC'"
echo ""
echo "4️⃣  运行Python测试"
echo "   - 新终端窗口运行: python3 monitor_openplc.py"
echo ""
echo "📖 详细文档: cat OPENPLC_QUICKSTART.md"
echo "============================================================"
