# 照片处理软件 - 联系人照片匹配和HTML相册生成工具

一款基于 PyQt5 的桌面应用程序，用于自动匹配 VCF 联系人文件与带有人脸识别标记的照片，并生成美观的HTML相册。

## 功能特性

### 核心功能

1. **智能照片标签提取**
   - 从照片的XMP元数据中提取人脸识别标记的人员信息
   - 支持多种XMP格式：dc:subject、MPReg:PersonDisplayName、mwg-rs:Name、digiKam:TagsList等
   - 支持一张照片包含多个人名的情况
   - 自动处理多种编码格式

2. **联系人匹配**
   - 自动解析 VCF 联系人文件，提取姓名、单位、电话、邮箱、地址等信息
   - 智能匹配照片中的人名标签与联系人信息
   - 支持同名联系人的单位匹配（优先匹配有单位的联系人）
   - 无单位同名联系人自动匹配第一个出现的

3. **HTML相册生成**
   - 生成美观的静态HTML相册，支持深色主题
   - 照片网格布局，每张照片可点击放大查看
   - 智能照片管理：超过6张照片时，默认显示前6张，支持"查看更多"展开
   - 联系人信息完整展示：姓名、单位、职位、电话、邮箱、地址、备注
   - 强大的搜索功能：支持按姓名、单位、电话、邮箱搜索

4. **信息提取**
   - 从 VCF 文件提取：姓名、单位、职位、电话、邮箱、地址、备注
   - 支持多个电话、多个邮箱、多个地址
   - 自动处理多种编码格式（UTF-8、GBK、GB2312）

### 界面特色

- 🌙 **深色主题**：护眼的深色背景，减少视觉疲劳
- 🎨 **现代设计**：渐变背景、圆角卡片、流畅动画
- 📱 **响应式布局**：自适应不同屏幕尺寸
- 🔍 **实时搜索**：输入即搜索，快速定位联系人

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
   - **选择照片文件夹**：包含带有人脸识别标记的照片的文件夹（支持多级子文件夹）
   - **选择 VCF 文件**：包含联系人信息的 VCF 文件
   - **选择输出HTML文件**：保存生成的HTML相册的路径
   - 点击"开始处理"，等待完成
   - 处理完成后会自动在浏览器中打开HTML相册

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

## 照片标签提取说明

程序从照片的XMP元数据中提取人脸识别标记的人员信息。支持的XMP字段包括：

- `dc:subject` - 主题/标签（通常包含人名）
- `MPReg:PersonDisplayName` - Microsoft Photo 人员显示名称
- `mwg-rs:Name` - 区域名称（通常是人名）
- `digiKam:TagsList` - digiKam标签列表（格式：People/人名）
- `acdsee:categories` - ACDSee分类（HTML编码的XML）
- `MicrosoftPhoto:LastKeywordXMP` - Microsoft Photo最后关键字
- `lr:hierarchicalSubject` - Lightroom层级主题
- `mediapro:CatalogSets` - MediaPro目录集

**注意**：程序仅从XMP元数据提取人名，不处理Windows图片属性（EXIF）字段。

## HTML相册功能

生成的HTML相册具有以下特性：

1. **照片展示**
   - 3列网格布局，整齐美观
   - 默认显示前6张照片
   - 超过6张时，显示"查看更多"按钮
   - 点击照片可放大查看

2. **联系人信息**
   - 完整的联系人信息展示
   - 清晰的层次结构
   - 易于阅读的排版

3. **搜索功能**
   - 实时搜索，输入即显示结果
   - 支持按姓名、单位、电话、邮箱搜索
   - 高亮显示匹配的联系人

4. **深色主题**
   - 护眼的深色背景
   - 高对比度文字
   - 现代化的紫色强调色

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
- PyQt5、Pillow、defusedxml 和 PyInstaller 自动安装
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
│   ├── backend.py                  # 后端处理逻辑（VCF解析、XMP提取、HTML生成）
│   ├── requirements.txt            # Python 依赖
│   ├── build_mac.sh                # 本地 Mac 打包脚本
│   ├── PACKAGING.md                # 详细打包说明
│   └── README.md                   # 项目说明
└── README.md                       # 本文件
```

## 匹配规则

### 照片标签匹配

程序从照片的XMP元数据中提取人名标签，然后与VCF联系人进行匹配：

1. **精确匹配**：照片标签中的人名与联系人姓名完全匹配
2. **同名匹配**：
   - 优先匹配有单位的联系人
   - 如果都有单位或都没有，匹配第一个出现的
3. **多标签支持**：一张照片可以匹配多个联系人

### 示例

| 照片标签 | VCF 联系人 | 匹配结果 |
|---------|-----------|---------|
| 张三 | 张三（北京科技有限公司） | ✅ 匹配 |
| 张三、李四 | 张三（北京科技有限公司）、李四（广州电子科技） | ✅ 匹配两个 |
| 王五 | 王五（无单位1）、王五（无单位2） | ✅ 匹配第一个 |

## 技术栈

- **PyQt5**：图形用户界面框架
- **Pillow (PIL)**：图片处理和XMP元数据读取
- **defusedxml**：安全的XML解析
- **PyInstaller**：应用打包工具
- **GitHub Actions**：CI/CD 自动化打包

## 常见问题

### Q: 应用无法打开？

运行以下命令移除隔离属性：
```bash
xattr -cr PhotoSoftware.app
```

### Q: 照片标签提取失败？

- 确保照片包含XMP元数据（通常由人脸识别软件添加）
- 检查照片是否支持XMP格式（JPEG、TIFF等）
- 查看处理结果中的调试信息，了解提取到的标签

### Q: 匹配结果不正确？

- 检查照片XMP元数据中的人名是否正确
- 检查VCF文件中的联系人姓名是否正确
- 查看处理结果中的未匹配列表

### Q: HTML相册显示异常？

- 确保输出路径有写入权限
- 检查照片路径是否正确（相对路径）
- 尝试在浏览器中刷新页面

### Q: 打包失败？

- 检查 GitHub Actions 日志
- 确保代码已正确推送到 main 分支
- 查看 `.github/workflows/build-mac.yml` 配置

## 更新日志

### v2.0.0（当前版本）
- ✨ 新增HTML相册生成功能
- ✨ 新增深色主题界面
- ✨ 新增照片标签提取功能（从XMP元数据）
- ✨ 新增智能照片管理（超过6张自动折叠）
- ✨ 新增强大的搜索功能
- 🔧 优化匹配逻辑，支持一张照片匹配多个联系人
- 🔧 移除Windows图片属性提取（仅使用XMP）

### v1.0.0
- 联系人匹配功能
- 照片自动整理
- GitHub Actions 自动打包

## 许可证

本项目仅供学习和个人使用。
