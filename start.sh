#!/bin/bash
# 快速启动脚本 for Linux

echo "╔══════════════════════════════════════════╗"
echo "║        Boss Detect - 老板探测器          ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 检查配置文件
if [ ! -f "config.ini" ]; then
    echo "❌ 配置文件不存在！"
    echo "正在创建配置文件..."
    cp config.ini.example config.ini
    echo "✅ 已创建 config.ini，请编辑该文件并填写必要信息"
    echo ""
    echo "必填项："
    echo "  - boss_mac: 老板手机的MAC地址"
    echo "  - pushdeer_key: PushDeer推送Key (从 https://www.pushdeer.com 获取)"
    echo ""
    exit 1
fi

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
if ! python3 -c "import scapy" 2>/dev/null; then
    echo "⚠️  缺少依赖，正在安装..."
    pip3 install -r requirements.txt
fi

# 检查权限
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  建议使用root权限运行以获得更好的扫描效果"
    echo "使用命令: sudo $0"
    echo ""
    read -p "是否继续运行？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 运行程序
echo "🚀 启动Boss Detect..."
echo ""
python3 boss_detect.py
