#!/bin/bash

# DeepSeek 谄媚效应实验启动脚本

echo "🌍 DeepSeek 谄媚效应实验"
echo "========================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3，请先安装"
    exit 1
fi

# 检查requests库
python3 -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 正在安装依赖..."
    pip install requests
fi

echo ""
echo "选择实验版本："
echo "1. 简单版 (simple_debate.py) - 推荐 ⭐"
echo "2. 高级版 (advanced_debate.py) - 高级选项"
echo "3. 专题版 (flat_earth_debate.py) - 深度分析"
echo ""

read -p "请选择 [1-3] (默认1): " choice
choice=${choice:-1}

# 检查API密钥
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo ""
    read -sp "请输入DeepSeek API密钥: " api_key
    echo ""
    export DEEPSEEK_API_KEY="$api_key"
fi

case $choice in
    1)
        echo "启动简单版..."
        python3 simple_debate.py
        ;;
    2)
        echo "启动高级版..."
        python3 advanced_debate.py
        ;;
    3)
        echo "启动专题版..."
        python3 flat_earth_debate.py
        ;;
    *)
        echo "❌ 选择无效"
        exit 1
        ;;
esac

echo ""
echo "✅ 实验完成！"
echo "检查 *.json 文件查看完整结果"
