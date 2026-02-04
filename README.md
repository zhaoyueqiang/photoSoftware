# 照片处理软件 - 联系人匹配和照片打包工具

一款基于 PyQt5 的桌面应用程序，用于自动匹配 VCF 联系人文件与照片文件夹，并整理打包照片。

## 功能特性

### 核心功能

1. **联系人匹配**
   - 自动解析 VCF 联系人文件，提取姓名、单位、电话、邮箱、地址等信息
   - 智能匹配联系人信息与照片文件夹名称
   - 支持同名联系人的单位匹配（精确匹配和子序列匹配）
   - 无单位同名联系人自动匹配第一个出现的

2. **信息提取**
   - 从 VCF 文件提取：姓名、单位、职位、电话、邮箱、地址、备注
   - 支持多个电话、多个邮箱、多个地址
   - 自动处理多种编码格式（UTF-8、GBK、GB2312）

3. **照片整理**
   - 自动识别文件夹中的图片（支持 jpg、png、gif、bmp、webp 等格式）
   - 为每个匹配的联系人创建独立的输出文件夹
   - 保持原始图片文件名不变
   - 自动复制到对应的 photo 子文件夹

4. **信息保存**
   - 生成中文格式的联系人信息文件（`联系人名称.txt`）
   - 包含完整的联系人信息（姓名、单位、职位、电话、邮箱、地址、备注）

### 输出目录结构

```
输出目录/
├── 张三 北京科技有限公司/
│   ├── 张三.txt              # 联系人信息
│   └── photo/                # 照片文件夹
│       ├── meeting_01.jpg
│       └── office.png
├── 李四 广州电子科技/
│   ├── 李四.txt
│   └── photo/
│       └── product_demo.jpg
└── ...
```

## 系统要求

- **运行环境**：macOS 10.13 或更高版本
- **开发环境**：Python 3.7 或更高版本

## 使用方法

### 方式一：使用打包好的 Mac 应用（推荐）

1. **下载应用**
   - 访问 GitHub Actions：https://github.com/zhaoyueqiang/photoSoftware/actions
   - 下载最新的 `PhotoSoftware-Mac.zip`
   - 解压得到 `PhotoSoftware.app`

2. **运行应用**
   - 双击 `PhotoSoftware.app` 运行
   - 如果提示"无法打开"，右键点击 → 选择"打开"
   - 或在终端运行：`xattr -cr PhotoSoftware.app`

3. **使用步骤**
   - 选择源文件夹：包含多个子文件夹的基础目录（每个子文件夹格式：`姓名 单位`）
   - 选择 VCF 文件：包含联系人信息的 VCF 文件
   - 选择输出目录：保存处理结果的目录
   - 点击"开始处理"，等待完成

### 方式二：开发模式运行

1. **安装依赖**
   ```bash
   cd photoSoftware
   pip3 install -r requirements.txt
   ```

2. **运行程序**
   ```bash
   python3 main.py
   ```

## GitHub Actions 自动打包

本项目使用 GitHub Actions 自动在云端 Mac 上打包应用，无需本地 Mac 环境。

### 打包流程

1. **推送代码到 GitHub**
   ```bash
   git add .
   git commit -m "Update code"
   git push origin main
   ```

2. **自动触发打包**
   - 推送代码后，GitHub Actions 会自动开始打包
   - 访问：https://github.com/zhaoyueqiang/photoSoftware/actions
   - 查看 "Build Mac App" 工作流状态

3. **下载打包结果**
   - 等待 3-5 分钟完成打包
   - 点击完成的工作流
   - 滚动到底部 **Artifacts** 区域
   - 下载 **PhotoSoftware-Mac** ZIP 文件

### 手动触发打包

如果自动触发失败，可以手动触发：

1. 访问 GitHub 仓库的 **Actions** 标签
2. 选择 **Build Mac App** 工作流
3. 点击 **Run workflow** → **Run workflow**

### 打包配置

打包配置位于 `.github/workflows/build-mac.yml`，包含：
- Python 3.11 环境
- PyQt5 和 PyInstaller 自动安装
- Mac 应用打包和 ZIP 压缩
- 自动上传 Artifacts（保留 30 天）

## 项目结构

```
photoSoftware/
├── .github/
│   └── workflows/
│       └── build-mac.yml          # GitHub Actions 打包配置
├── photoSoftware/
│   ├── main.py                     # 主程序（PyQt5 界面）
│   ├── backend.py                  # 后端处理逻辑
│   ├── requirements.txt            # Python 依赖
│   ├── build_mac.sh                # 本地 Mac 打包脚本
│   ├── PACKAGING.md                # 详细打包说明
│   └── README.md                   # 项目说明
└── README.md                       # 本文件
```

## 匹配规则

### 文件夹命名格式

源文件夹中的子文件夹应遵循以下格式：
- `姓名 单位` - 例如：`张三 北京科技有限公司`
- `姓名` - 例如：`张三`（无单位）

### 匹配优先级

1. **精确匹配**：文件夹名称与联系人姓名完全匹配
2. **单位匹配**：
   - 优先精确匹配单位
   - 其次子序列匹配（联系人单位是文件夹单位的子序列）
3. **无单位匹配**：多个同名无单位联系人时，匹配第一个出现的

### 示例

| VCF 联系人 | 文件夹名称 | 匹配结果 |
|-----------|-----------|---------|
| 张三（北京科技有限公司） | 张三 北京科技有限公司 | ✅ 匹配 |
| 张三（上海贸易公司） | 张三 上海贸易公司 | ✅ 匹配 |
| 张三（无单位） | 张三 | ✅ 匹配第一个 |
| 赵六（深圳创新科技有限公司） | 赵六 深圳创新 | ✅ 子序列匹配 |

## 技术栈

- **PyQt5**：图形用户界面框架
- **PyInstaller**：应用打包工具
- **GitHub Actions**：CI/CD 自动化打包

## 常见问题

### Q: 应用无法打开？

运行以下命令移除隔离属性：
```bash
xattr -cr PhotoSoftware.app
```

### Q: 匹配结果不正确？

- 检查文件夹命名格式是否正确（`姓名 单位` 或 `姓名`）
- 检查 VCF 文件编码是否为 UTF-8 或 GBK
- 查看处理结果中的未匹配列表

### Q: 打包失败？

- 检查 GitHub Actions 日志
- 确保代码已正确推送到 main 分支
- 查看 `.github/workflows/build-mac.yml` 配置

## 许可证

本项目仅供学习和个人使用。

## 更新日志

- **v1.0.0**：初始版本
  - 联系人匹配功能
  - 照片自动整理
  - GitHub Actions 自动打包
