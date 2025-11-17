#!/bin/bash
# 立即安装OpenPLC - 交互式脚本

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         OpenPLC 安装向导                                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 检查是否已安装
if [ -d "OpenPLC_v3" ]; then
    echo "⚠️  OpenPLC_v3 目录已存在！"
    echo ""
    ls -lh OpenPLC_v3/ | head -5
    echo ""
    read -p "是否重新安装？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 取消安装"
        exit 0
    fi
    echo "🗑️  删除旧版本..."
    rm -rf OpenPLC_v3
fi

echo "📦 开始安装OpenPLC..."
echo ""

# 步骤1: 检查依赖
echo "【步骤1/4】检查系统依赖"
echo "────────────────────────────────────────"

if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew未安装"
    echo "请先安装: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi
echo "✅ Homebrew 已安装"

if ! command -v node &> /dev/null; then
    echo "⚠️  Node.js未安装，正在安装..."
    brew install node
fi
echo "✅ Node.js $(node --version)"

if ! command -v git &> /dev/null; then
    echo "⚠️  Git未安装，正在安装..."
    brew install git
fi
echo "✅ Git $(git --version | head -1)"

echo "✅ 依赖检查完成"
echo ""

# 步骤2: 克隆仓库
echo "【步骤2/4】下载OpenPLC源码"
echo "────────────────────────────────────────"
echo "📥 正在从GitHub克隆..."
git clone https://github.com/thiagoralves/OpenPLC_v3.git

if [ $? -ne 0 ]; then
    echo "❌ 克隆失败"
    exit 1
fi
echo "✅ 下载完成"
echo ""

# 步骤3: 安装
echo "【步骤3/4】安装OpenPLC"
echo "────────────────────────────────────────"
cd OpenPLC_v3
./install.sh macos

if [ $? -ne 0 ]; then
    echo "❌ 安装失败"
    exit 1
fi
cd ..
echo "✅ 安装完成"
echo ""

# 步骤4: 验证
echo "【步骤4/4】验证安装"
echo "────────────────────────────────────────"

if [ -f "OpenPLC_v3/webserver/server.js" ]; then
    echo "✅ server.js 存在"
else
    echo "❌ server.js 未找到"
    exit 1
fi

if [ -d "OpenPLC_v3/runtime" ]; then
    echo "✅ runtime/ 目录存在"
else
    echo "❌ runtime/ 未找到"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🎉 OpenPLC 安装成功！                                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📂 安装位置:"
echo "   $(pwd)/OpenPLC_v3/"
echo ""
echo "🚀 启动OpenPLC:"
echo "   cd OpenPLC_v3/webserver"
echo "   sudo node server.js"
echo ""
echo "🌐 Web界面:"
echo "   http://localhost:8080"
echo "   用户名: openplc"
echo "   密码: openplc"
echo ""
echo "📝 下一步:"
echo "   1. 上传 openplc_temperature_control.st"
echo "   2. 编译程序"
echo "   3. 启动PLC"
echo "   4. 运行测试: python3 test_temperature_openplc.py"
echo ""

read -p "是否现在启动OpenPLC? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 正在启动OpenPLC..."
    echo "   (在新终端窗口中)"
    osascript <<APPLESCRIPT
tell application "Terminal"
    do script "cd '$(pwd)/OpenPLC_v3/webserver' && sudo node server.js"
    activate
end tell
APPLESCRIPT
    
    sleep 2
    echo "✅ OpenPLC已在新窗口中启动"
    echo ""
    read -p "按Enter打开浏览器访问Web界面..." 
    open http://localhost:8080
fi

echo ""
echo "✅ 完成！"
