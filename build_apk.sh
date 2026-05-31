#!/bin/bash
# 综合政务管理 APP - APK 构建脚本 (Linux/WSL)
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "==> 1/4 — 安装系统依赖"
sudo apt update -qq
sudo apt install -y python3-pip python3-setuptools python3-dev \
    git zip unzip build-essential ccache autoconf libtool \
    pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev \
    libtinfo5 cmake libffi-dev libssl-dev 2>&1 | tail -1
echo "  [✓] 系统依赖已安装"

echo ""
echo "==> 2/4 — 安装 Python 依赖"
pip3 install --upgrade pip setuptools wheel buildozer cython virtualenv 2>&1 | tail -1
echo "  [✓] Python 依赖已安装"

echo ""
echo "==> 3/4 — 构建 APK"
echo "  首次构建约 30-60 分钟，后续约 5 分钟"
python3 -m buildozer android debug 2>&1 | tee build_log.txt

echo ""
echo "==> 4/4 — 构建结果"
APK=$(ls -t bin/*.apk 2>/dev/null | head -1)
if [ -n "$APK" ]; then
    SIZE=$(du -h "$APK" | cut -f1)
    echo "  [✓] APK: $APK ($SIZE)"
else
    echo "  [!] 未找到 APK，请检查 bin/ 目录"
fi

echo ""
echo "=== 构建完成 ==="
