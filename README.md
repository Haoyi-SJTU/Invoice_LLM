# 发票智能处理系统 (Invoice Intelligent Processing System)

![GitHub Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen)
![LLM](https://img.shields.io/badge/LLM-Qwen--VL-orange)

基于 Python 和 PyQt6 的自动化发票数据提取工具。通过集成阿里云通义千问（Qwen-VL-OCR）大模型，该系统能够自动识别并提取发票中的关键财务信息，并将其导出为结构化的 Excel 表格。


## 1. 核心特性

现有发票数据录入软件普遍存在以下问题，如商用软件收费高、免费软件功能有限且操作复杂、软件臃肿且不支持批量处理，软件输出结果需要手动整理等。本项目旨在解决这些问题，提供一个**免费、开源、轻量化**的发票数据录入工具。

- **轻量化**：仅依赖 PyQt6、pymupdf、pandas、openpyxl 等基础库，无需额外安装。
- **开源**：本项目基于BSD-3协议开源，您可以在遵守协议的前提下自由使用、修改和分发本项目的代码。
- **输出直接可用**：输出数据格式已适配上海交通大学财务报销要求，可直接使用。

此外，本项目具有以下特点：

- **多格式支持**：完美支持 `PDF`、`PNG`、`JPG`、`JPEG` 格式的发票文件。
- **智能提取逻辑**：
  - **金额自动转换**：通过读取发票中的“中文大写金额”并转换为“阿拉伯数字”，大幅提高金额识别的准确率。
  - **项目名称优化**：支持精准提取发票明细的第一行项目名称。
- **Token 优化机制**：内置图像压缩算法，在上传前自动将大图压缩至 1280px，降低 API 消耗，提升响应速度。
- **UI 配置化**：无需修改代码或 JSON 文件，直接通过软件界面配置 API Key 和 Base URL。
- **实时校对流**：支持“识别 -> 人工校验/修改 -> 确认写入”的闭环流程，防止错误数据进入账本。
- **进度追踪**：直观的进度条和状态提示，适合批量处理大量发票。


## 2. 源码运行

### 2.1. 克隆仓库

```bash

git clone https://github.com/Haoyi-SJTU/InvoiceApp.git
cd InvoiceApp
```

### 2.2. 安装依赖库
建议使用 `pip` 安装所需的第三方库：
```bash
pip install PyQt6 pymupdf pandas openpyxl Pillow requests
```

### 2.3. 配置大模型

配置`key.json`文件，放置在代码根目录下：
- **API Key**: 填入您的阿里云百炼 API Key。
- **Base URL**: 默认已填入通义千问兼容接口，如有特殊需求可修改。


### 2.4. 运行程序

```bash
python invoice.py
```



## 3.Release 版说明（打包为 EXE）

### 3.1. 下载 Release 版本
从[Release页面](https://github.com/Haoyi-SJTU/Invoice_LLM/releases/tag/release)下载最新版本的EXE文件。

### 3.2. 使用方法
  1. 双击 `发票助手.exe`。
  2. 启动程序后，点击右侧蓝色的 **“⚙️ 配置大模型”** 按钮：
     - **API Key**: 填入您的阿里云百炼 API Key。
     - **Base URL**: 默认已填入通义千问兼容接口，如有特殊需求可修改。

**注意**：打包版运行 PDF 识别时，会自动在同级目录生成 `temp_invoice.png` 作为临时预览图，程序关闭时会自动清理。



## 4. 技术架构

- **GUI 框架**: [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- **PDF 解析**: [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/)
- **数据处理**: [Pandas](https://pandas.pydata.org/) & [Openpyxl](https://openpyxl.readthedocs.io/)
- **图像处理**: [Pillow (PIL)](https://python-pillow.org/)
- **API 通讯**: [Requests](https://requests.readthedocs.io/)
- **模型支持**: [阿里云通义千问 (DashScope)](https://help.aliyun.com/zh/model-studio/vision)

## 5. 其它说明

- **导出文件**：点击“确认并处理下一张”后，数据将实时追加到程序目录下的 `发票汇总.xlsx` 中。
- **隐私保护**：本工具直接与阿里云官方 API 通讯，本地不存储任何发票图像。
- **错误排查**：若无法进入下一张，请检查 `发票汇总.xlsx` 是否被 Excel 占用（关闭该 Excel 即可）。

## 6. 致谢

作者：[Haoyi-SJTU](https://github.com/Haoyi-SJTU)

如果您觉得这个工具有帮助，欢迎在 GitHub 上给个 Star！


