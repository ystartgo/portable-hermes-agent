<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/Lang-English-blue?style=for-the-badge" alt="English"></a>
  <a href="README.zh-TW.md"><img src="https://img.shields.io/badge/Lang-%E7%B9%81%E9%AB%94%E4%B8%AD%E6%96%87-purple?style=for-the-badge" alt="繁體中文"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-red?style=for-the-badge" alt="简体中文"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Lang-Espa%C3%B1ol-yellow?style=for-the-badge" alt="Español"></a>
  <a href="README.ur-pk.md"><img src="https://img.shields.io/badge/Lang-%D8%A7%D8%B1%D8%AF%D9%88-green?style=for-the-badge" alt="اردو"></a>
</p>

# 便携版 Hermes Agent (Portable Hermes Agent)

**专为 Windows 设计的免安装便携 AI Agent 桌面端** — 集成 100 种工具、图形化界面 (GUI)、LM Studio 本地模型、TTS 语音生成、音乐创作、ComfyUI 绘图、自动化工作流与动态工具制作器。无需安装、无需 Docker、无需管理员权限。

基于 [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) (MIT License) 开发，并针对非技术用户进行了深度的本地化与便携化定制。

---

## 主要特性

### 桌面图形界面 (GUI)
- 深色现代风格 Tkinter 界面，内置实时聊天、侧边栏与会话记录管理
- **完整多语言界面**：支持 **繁体中文**、**简体中文** 与 **英文** 实时切换，所有窗口、菜单与向导全面本地化，配置自动保存
- **智能 API 设置向导**：逐步引导配置 **OpenRouter**、**TokenTable** (`https://tokentable.asia/v1`)、**自定义端点 (Other)**（自由填写 Base URL 与 API Key，兼容 Ollama、vLLM、OneAPI、LM Studio 或各类 OpenAI 兼容代理服务器）及搜索/图像工具
- **动态模型切换与自定义新增**：内置支持 **`auto`** 自动路由模型（特别适用于 TokenTable / 复合模型网关），并可在“设置”或侧边栏直接手动新增自定义模型名称
- **纯 Windows CRLF 批处理兼容**：所有启动批处理文件（`START.bat`、`UPDATE.bat`、`install.bat`、`hermes.bat`、`hermes_gui.bat`）均由 `.gitattributes` 强制规范 CRLF 换行，彻底解决原生 `cmd.exe` 在 Linux LF 格式下出现的字符偏移错误（如 `'tlocal'`、`'et'`、`'not'` 等命令找不到的报错）
- 支持图片附件与缩略图预览（完整支持多模态 Vision 模型）
- 内置引导模式 — 即使尚未连接 AI 模型也可离线使用
- 细粒度权限管理面板，精确控制文件、网络与系统访问权限

### 跨 20+ 工具集的 100 种强大工具

| 工具集 | 工具数 | 功能说明 |
|---------|-------|-------------|
| **LM Studio** | 10 | 加载/卸载模型、搜索 HuggingFace、Token 计算、嵌入向量、直接聊天 |
| **音乐生成 (Music)** | 7 | 文本生成音乐、模型管理、GPU 加速、作品库管理 |
| **语音合成 (TTS)** | 7 | 文本转语音、10 款语音模型、声音克隆、任务队列管理 |
| **ComfyUI** | 7 | AI 图像生成、实例管理、模型与节点浏览 |
| **自动化工作流 (Workflows)** | 6 | 创建、运行、调度与管理多步骤自动化流水线 |
| **动态工具制作器 (Tool Maker)** | 3 | 在运行期动态包装 REST API 或编写 Python 处理器 |
| **Serper** | 1 | 通过 Serper.dev API 提供 Google 搜索质量的网页检索 |
| **用户手册 (Guide)** | 1 | 内置全文检索使用手册 |
| **GPU 监控** | 1 | NVIDIA GPU 状态监控（显存、温度、利用率） |
| **模型切换器** | 1 | 在云端模型与本地 AI 模型之间快速切换 |
| **Hermes 更新** | 2 | 更新上游 Hermes，同时保留便携工具、扩展与运行期数据 |

外加所有 hermes-agent 内置工具：网页搜索、文件操作、浏览器自动化、代码执行、子代理委派、记忆库、技能、消息传递、Home Assistant 等。

### 扩展模块 (Extension Modules)

来自 [aivrar](https://github.com/aivrar) 的三款便携 AI 生成服务器：

| 扩展模块 | 端口 | 支持模型 | GPU 需求 |
|-----------|------|--------|-----|
| **[TTS Server](https://github.com/aivrar/portable-tts-server)** | 8200 | Kokoro, XTTS, Dia, Bark, Fish, 及其他 5 款模型 | 4 GB+ |
| **[Music Server](https://github.com/aivrar/portable-music-server)** | 9150 | MusicGen, Stable Audio, ACE-Step, Riffusion | 4 GB+ |
| **[ComfyUI](https://github.com/aivrar/comfyui-portable-installer)** | 5000 | SD 1.5, SDXL, Flux, 100+ 模型注册表 | 6 GB+ |

所有扩展模块均在首次使用时自动下载配置，不依赖任何全局系统环境。

### 自动化工作流引擎
将工具调用串联成自动化流水线，具备数据流传递、条件判断、循环、并行处理、错误处理与 Cron 定时调度功能。

### 动态工具制作器
在运行期创建自定义工具 — 封装任何 REST API 或编写专属 Python 处理器。工具可在各个会话间持续保留并自动重新加载。

### 离线引导模式
没有 API 密钥？完全没问题。内置 1,054 行用户手册，新手可通过离线问答获取逐步指引并配置第一个 AI 模型。

---

## 快速上手

### 1. 下载
从 [Releases](https://github.com/aivrar/portable-hermes-agent/releases/latest) 下载最新版本的 `portable-hermes-agent-v*.zip`，并解压到普通文件夹。

推荐路径：
```text
C:\Users\用户名\Portable-Hermes-Agent
```
*请避免解压到如 `C:\Program Files` 等受保护的系统文件夹。*

### 2. 启动
双击运行：
```batch
START.bat
```

首次启动时，`START.bat` 会自动执行便携环境配置，自动下载便携版 Python、依赖库、LM Studio SDK 与 Node.js 工具到本目录中。无需管理员权限。

手动安装方式：
```batch
install.bat
```

PowerShell 用户亦可运行：
```powershell
.\scripts\install.ps1
```

### 3. 日常启动
```batch
START.bat           :: 最简单的一键 GUI 启动方式
UPDATE.bat          :: 一键安全更新
hermes_gui.bat      :: GUI 模式
hermes.bat          :: CLI 终端模式
```

### 语言切换
启动 GUI 后，您可以直接从顶部菜单栏点击 **“语言 (Language)”** 进行切换：
- **繁體中文**
- **✓ 简体中文**
- **English**

或前往“文件 > 设置 > 通用设置”中修改界面语言。切换后界面文字将立即动态刷新，并自动永久保存。

### 4. 连接 AI 模型

打开上方菜单之 **“文件 > API 密钥设置”** 智能向导：

- **TokenTable（亚太与全球高速中转，推荐）：**
  1. 在向导中选择 **TokenTable**
  2. 点击 **“推荐申请 / 获取 Key”**（自动跳转至 [top.yia.app/token](https://top.yia.app/token)）快速获取密钥
  3. 粘贴您的 API 密钥（API Base URL 默认已为 `https://tokentable.asia/v1`）
  4. 在模型列表选取或输入 **`auto`**（智能自动路由），即可开始高速对话！

- **OpenRouter（云端与免费模型）：**
  1. 在向导中选择 **OpenRouter**
  2. 点击 **“推荐申请 / 获取 Key”** 前往 [openrouter.ai](https://openrouter.ai) 注册（免信用卡）
  3. 粘贴您的 API 密钥并选择喜欢的模型

- **其它自定义端点（Other - 兼容 Ollama / vLLM / OneAPI / 私有代理）：**
  1. 在向导中选择 **其它 (自定义端点)**
  2. 输入您的自定义 **API Base URL**（例如 `http://localhost:11434/v1`）与 **API Key**
  3. 输入自定义模型名称（亦可随时在侧边栏模型列表点击“+ 自定义模型...”快速手动新增）

- **本地模型（LM Studio，需 NVIDIA 独立显卡）：**
  1. 下载并安装 [LM Studio](https://lmstudio.ai)
  2. 下载模型并启动本地 Server
  3. 在界面菜单点击“视图 > LM Studio (本地模型)”
  4. 加载模型并点击“用于对话 (Use for Chat)”

---

## 系统要求

- Windows 10 / 11
- 互联网连接（用于云端 AI）或 8GB+ 显存之 NVIDIA GPU（用于本地 AI）
- 无需管理员权限、无需系统 Python、无需 Docker

---

## 开发与版权声明

- **基础框架**：[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) (MIT License)
- **便携发行版与扩展整合**：由 [aivrar](https://github.com/aivrar) 维护
- **多语言支持与界面定制**：Portable Hermes Agent Team

---

## 许可证

MIT License — 详情请参阅 [LICENSE](LICENSE)。
