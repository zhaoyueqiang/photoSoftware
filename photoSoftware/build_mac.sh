#!/bin/bash
# Mac 应用程序打包脚本
# 照片处理软件 - 联系人匹配和照片打包工具

set -e

echo "=========================================="
echo "照片处理软件 - Mac 打包脚本"
echo "=========================================="

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查是否在 Mac 上运行
if [[ "$(uname)" != "Darwin" ]]; then
    echo "错误: 此脚本只能在 Mac 系统上运行"
    echo "PyInstaller 不支持跨平台打包"
    exit 1
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    echo "请先安装 Python3: https://www.python.org/downloads/"
    exit 1
fi

echo "Python 版本: $(python3 --version)"

# 检查并安装依赖
echo ""
echo "检查依赖包..."

if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "正在安装 PyInstaller..."
    pip3 install pyinstaller
fi

if ! python3 -c "import PyQt5" 2>/dev/null; then
    echo "正在安装 PyQt5..."
    pip3 install PyQt5
fi

if ! python3 -c "import PIL" 2>/dev/null; then
    echo "正在安装 Pillow..."
    pip3 install Pillow
fi

if ! python3 -c "import defusedxml" 2>/dev/null; then
    echo "正在安装 defusedxml..."
    pip3 install defusedxml
fi

echo "所有依赖已就绪"

# 清理旧的构建文件
echo ""
echo "清理旧的构建文件..."
rm -rf build/ dist/ *.spec __pycache__/

# 打包
echo ""
echo "开始打包应用（这可能需要几分钟）..."
echo ""

python3 -m PyInstaller \
    --name="PhotoSoftware" \
    --windowed \
    --onedir \
    --clean \
    --noconfirm \
    --osx-bundle-identifier=com.photosoftware.contactmatcher \
    --hidden-import=PyQt5 \
    --hidden-import=PyQt5.QtCore \
    --hidden-import=PyQt5.QtGui \
    --hidden-import=PyQt5.QtWidgets \
    --hidden-import=PyQt5.sip \
    --hidden-import=PIL \
    --hidden-import=PIL.Image \
    --collect-all=PyQt5 \
    --collect-all=PIL \
    --strip \
    main.py

# 检查结果
APP_NAME="PhotoSoftware.app"
if [ -d "dist/$APP_NAME" ]; then
    # 获取应用大小
    APP_SIZE=$(du -sh "dist/$APP_NAME" | cut -f1)
    
    echo ""
    echo "=========================================="
    echo "✅ 打包成功！"
    echo "=========================================="
    echo ""
    echo "应用程序: dist/$APP_NAME"
    echo "文件大小: $APP_SIZE"
    echo ""
    echo "----------------------------------------"
    echo "使用方法:"
    echo "----------------------------------------"
    echo "1. 将 dist/$APP_NAME 复制到目标 Mac"
    echo "2. 双击运行"
    echo ""
    echo "如果提示'无法打开'，请在终端运行:"
    echo "   xattr -cr \"dist/$APP_NAME\""
    echo ""
    echo "或者右键点击应用 -> 打开"
    echo "=========================================="
else
    echo ""
    echo "❌ 打包失败，请检查上方错误信息"
    exit 1
fi
