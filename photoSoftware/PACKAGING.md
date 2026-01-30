# Mac 应用程序打包指南

## 重要提示

⚠️ **PyInstaller 不支持跨平台打包**，必须在 Mac 系统上进行打包。

## 快速打包步骤

### 1. 将项目复制到 Mac

将整个 `photoSoftware` 文件夹复制到 Mac 上。

### 2. 打开终端并进入项目目录

```bash
cd /path/to/photoSoftware
```

### 3. 安装依赖

```bash
pip3 install -r requirements.txt
pip3 install pyinstaller
```

### 4. 运行打包脚本

```bash
chmod +x build_mac.sh
./build_mac.sh
```

### 5. 获取打包结果

打包完成后，在 `dist/` 目录下会生成：
- `PhotoSoftware.app` - Mac 应用程序包

## 打包环境要求

- macOS 10.13 或更高版本
- Python 3.7 或更高版本
- 网络连接（用于安装依赖）

## 在目标 Mac 上运行

### 1. 复制应用

将 `PhotoSoftware.app` 复制到目标 Mac 的"应用程序"文件夹或任意位置。

### 2. 首次运行

由于应用未经过 Apple 签名，首次运行可能会被阻止：

**方法一：右键打开**
- 右键点击应用 → 选择"打开" → 在弹出对话框中点击"打开"

**方法二：移除隔离属性**
```bash
xattr -cr "PhotoSoftware.app"
```

**方法三：系统偏好设置**
- 打开"系统偏好设置" → "安全性与隐私" → "通用"
- 点击"仍要打开"

### 3. 正常使用

应用包含所有依赖，无需在目标 Mac 上安装 Python 环境。

## 应用功能

- 选择包含子文件夹的源目录（每个子文件夹格式：姓名 单位）
- 选择 VCF 联系人文件
- 选择输出目录
- 自动匹配联系人并整理照片

## 常见问题

### Q: 打包失败？

1. 确保在 Mac 上运行打包脚本
2. 确保安装了所有依赖：
   ```bash
   pip3 install PyQt5 pyinstaller
   ```
3. 查看终端错误信息

### Q: 应用无法打开？

运行以下命令移除隔离属性：
```bash
xattr -cr "PhotoSoftware.app"
```

### Q: 应用闪退？

在终端中运行应用查看错误信息：
```bash
./dist/PhotoSoftware.app/Contents/MacOS/PhotoSoftware
```

### Q: 文件太大？

打包后的应用包含 Python 解释器和 PyQt5 库，通常 100-300MB，这是正常的。

### Q: Intel Mac 和 Apple Silicon Mac 兼容吗？

- 在 Intel Mac 上打包的应用只能在 Intel Mac 上运行
- 在 Apple Silicon Mac 上打包的应用只能在 Apple Silicon Mac 上运行
- 如需通用版本，需要分别打包后合并

## 手动打包命令

如果打包脚本无法运行，可以手动执行：

```bash
cd /path/to/photoSoftware

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
    --collect-all=PyQt5 \
    main.py
```
