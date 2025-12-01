#!/bin/bash
# Agents4PLC Web UI 启动脚本

echo "=========================================="
echo "🤖 Agents4PLC - 智能PLC代码生成系统"
echo "=========================================="
echo ""

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python版本: $PYTHON_VERSION"

# 检查是否安装了依赖
echo ""
echo "📦 检查依赖..."

# 尝试导入必要的包
python3 -c "import gradio" 2>/dev/null || {
    echo "❌ 缺少gradio，正在安装..."
    pip install gradio>=4.0.0
}

python3 -c "import langchain_openai" 2>/dev/null || {
    echo "❌ 缺少langchain-openai，正在安装..."
    pip install langchain-openai>=1.0.1
}

python3 -c "import langchain_chroma" 2>/dev/null || {
    echo "⚠️ 缺少langchain-chroma（可选），跳过..."
}

echo ""
echo "✅ 依赖检查完成"
echo ""

# 检查配置
if [ ! -f "config.py" ]; then
    echo "❌ 错误: 未找到config.py配置文件"
    echo "   请复制config_template.py为config.py并填写API密钥"
    exit 1
fi

# 启动Web UI
echo "=========================================="
echo "🚀 启动Web UI..."
echo "=========================================="
echo ""
echo "📱 启动后请在浏览器打开:"
echo "   http://127.0.0.1:7860"
echo ""
echo "⌨️  按 Ctrl+C 停止服务器"
echo "=========================================="
echo ""

python3 web_ui.py

