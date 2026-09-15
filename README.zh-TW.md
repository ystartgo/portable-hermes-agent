<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/Lang-English-blue?style=for-the-badge" alt="English"></a>
  <a href="README.zh-TW.md"><img src="https://img.shields.io/badge/Lang-%E7%B9%81%E9%AB%94%E4%B8%AD%E6%96%87-purple?style=for-the-badge" alt="繁體中文"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-red?style=for-the-badge" alt="简体中文"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Lang-Espa%C3%B1ol-yellow?style=for-the-badge" alt="Español"></a>
  <a href="README.ur-pk.md"><img src="https://img.shields.io/badge/Lang-%D8%A7%D8%B1%D8%AF%D9%88-green?style=for-the-badge" alt="اردو"></a>
</p>

# 便攜版 Hermes Agent (Portable Hermes Agent)

**專為 Windows 設計的免安裝便攜 AI Agent 桌面端** — 整合 100 種工具、圖形化介面 (GUI)、LM Studio 本地模型、TTS 語音生成、音樂創作、ComfyUI 繪圖、自動化工作流與動態工具製作器。無需安裝、無需 Docker、無需系統管理員權限。

基於 [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) (MIT License) 開發，並針對非技術使用者進行了深度的在地化與便攜化客製。

---

## 主要特色

### 桌面圖形化介面 (GUI)
- 深色現代風格 Tkinter 介面，內建即時交談、側邊欄與對話紀錄管理
- **完整多語系介面**：支援 **繁體中文**、**簡體中文** 與 **英文** 即時切換，所有視窗、選單與精靈全面在地化，設定自動保存
- **智慧型 API 設定精靈**：逐步引導配置 **OpenRouter**、**TokenTable** (`https://tokentable.asia/v1`)、**自訂端點 (Other)**（自由填寫 Base URL 與 API Key，相容 Ollama、vLLM、OneAPI、LM Studio 或各類 OpenAI 相容代理伺服器）及搜尋/圖像工具
- **動態模型切換與自訂新增**：內建支援 **`auto`** 自動路由模型（特別適用於 TokenTable / 複合模型網關），並可於「設定」或側邊欄直接手動新增自訂模型名稱
- **純 Windows CRLF 批次檔相容**：所有啟動批次檔（`START.bat`、`UPDATE.bat`、`install.bat`、`hermes.bat`、`hermes_gui.bat`）皆經由 `.gitattributes` 強制 CRLF 換行，徹底解決原生 `cmd.exe` 在 Linux LF 格式下出現的字元偏移錯誤（如 `'tlocal'`、`'et'`、`'not'` 等指令找不到的報錯）
- 支援圖片附件與縮圖預覽（完整支援多模態 Vision 模型）
- 內建引導模式 — 即使尚未連接 AI 模型也能離線使用
- 細部權限管理面板，精確控制檔案、網路與系統存取權限

### 跨 20+ 工具集的 100 種強大工具

| 工具集 | 工具數 | 功能說明 |
|---------|-------|-------------|
| **LM Studio** | 10 | 載入/卸載模型、搜尋 HuggingFace、Token 計算、嵌入向量、直接交談 |
| **音樂生成 (Music)** | 7 | 文字生成音樂、模型管理、GPU 加速、作品庫管理 |
| **語音合成 (TTS)** | 7 | 文字轉語音、10 款語音模型、聲音複製、佇列任務管理 |
| **ComfyUI** | 7 | AI 圖片生成、實例管理、模型與節點瀏覽 |
| **自動化工作流 (Workflows)** | 6 | 建立、執行、排程與管理多步驟自動化流程 |
| **動態工具製作器 (Tool Maker)** | 3 | 於執行階段動態包裝 REST API 或撰寫 Python 處理常式 |
| **Serper** | 1 | 透過 Serper.dev API 提供 Google 搜尋品質的網路搜尋 |
| **使用者指南 (Guide)** | 1 | 內建全文檢索使用手冊 |
| **GPU 監控** | 1 | NVIDIA GPU 狀態監控（顯存、溫度、使用率） |
| **模型切換器** | 1 | 於雲端模型與本地 AI 模型之間快速切換 |
| **Hermes 更新** | 2 | 更新上游 Hermes，同時保留便攜工具、擴展與執行階段資料 |

外加所有 hermes-agent 內建工具：網路搜尋、檔案操作、瀏覽器自動化、程式碼執行、子代理委派、記憶庫、技能、訊息傳遞、Home Assistant 等。

### 擴展模組 (Extension Modules)

來自 [aivrar](https://github.com/aivrar) 的三款便攜 AI 生成伺服器：

| 擴展模組 | 連接埠 | 支援模型 | GPU 需求 |
|-----------|------|--------|-----|
| **[TTS Server](https://github.com/aivrar/portable-tts-server)** | 8200 | Kokoro, XTTS, Dia, Bark, Fish, 及其他 5 款模型 | 4 GB+ |
| **[Music Server](https://github.com/aivrar/portable-music-server)** | 9150 | MusicGen, Stable Audio, ACE-Step, Riffusion | 4 GB+ |
| **[ComfyUI](https://github.com/aivrar/comfyui-portable-installer)** | 5000 | SD 1.5, SDXL, Flux, 100+ 模型註冊表 | 6 GB+ |

所有擴展模組均在首次使用時自動下載配置，不依賴任何全域系統環境。

### 自動化工作流引擎
將工具呼叫串接成自動化管線，具備資料流傳遞、條件判斷、迴圈、平行處理、錯誤處理與 Cron 定時排程功能。

### 動態工具製作器
於執行階段建立自訂工具 — 封裝任何 REST API 或撰寫專屬 Python 處理程式。工具可在各對話階段間持續存在並自動重新載入。

### 離線引導模式
沒有 API 金鑰？完全沒問題。內建 1,054 行使用者指南，新手能透過離線問答獲取逐步指引並設定第一個 AI 模型。

---

## 快速上手

### 1. 下載
自 [Releases](https://github.com/aivrar/portable-hermes-agent/releases/latest) 下載最新版的 `portable-hermes-agent-v*.zip`，並解壓縮至一般資料夾。

建議路徑：
```text
C:\Users\使用者名稱\Portable-Hermes-Agent
```
*請避免解壓縮至如 `C:\Program Files` 等受保護的系統資料夾。*

### 2. 啟動
雙擊執行：
```batch
START.bat
```

首次啟動時，`START.bat` 會自動執行便攜環境配置，自動下載便攜版 Python、依賴項、LM Studio SDK 與 Node.js 工具至本目錄中。無需系統管理員權限。

手動安裝方式：
```batch
install.bat
```

PowerShell 使用者亦可執行：
```powershell
.\scripts\install.ps1
```

### 3. 日常啟動
```batch
START.bat           :: 最簡單的一鍵 GUI 啟動方式
UPDATE.bat          :: 一鍵安全更新
hermes_gui.bat      :: GUI 模式
hermes.bat          :: CLI 終端模式
```

### 語言切換
啟動 GUI 後，您可以直接由上方選單列點擊 **「語言 (Language)」** 切換：
- **✓ 繁體中文**
- **简体中文**
- **English**

或至「檔案 > 設定 > 一般設定」中調整介面語言。切換後介面將立即即時更新，並永久保存。

### 4. 連接 AI 模型

開啟上方選單之 **「檔案 > API 金鑰設定」** 智慧精靈：

- **TokenTable（亞太與全球高速中轉，推薦）：**
  1. 於精靈中選取 **TokenTable**
  2. 點選 **「推薦申請 / 取得 Key」**（自動導向至 [top.yia.app/token](https://top.yia.app/token)）快速獲取金鑰
  3. 貼上您的 API 金鑰（API Base URL 預設已為 `https://tokentable.asia/v1`）
  4. 於模型清單選取或輸入 **`auto`**（智慧自動路由），即可開始高速交談！

- **OpenRouter（雲端與免費模型）：**
  1. 於精靈中選取 **OpenRouter**
  2. 點選 **「推薦申請 / 取得 Key」** 前往 [openrouter.ai](https://openrouter.ai) 註冊（免信用卡）
  3. 貼上您的 API 金鑰並選擇喜好的模型

- **其它自訂端點（Other - 相容 Ollama / vLLM / OneAPI / 私有代理）：**
  1. 於精靈中選取 **其它 (自訂端點)**
  2. 輸入您的自訂 **API Base URL**（例如 `http://localhost:11434/v1`）與 **API Key**
  3. 輸入自訂模型名稱（亦可隨時在側邊欄模型清單點選「+ 自訂模型...」快速手動新增）

- **本地模型（LM Studio，需 NVIDIA 獨立顯卡）：**
  1. 下載並安裝 [LM Studio](https://lmstudio.ai)
  2. 下載模型並啟動本地 Server
  3. 在介面選單點選「檢視 > LM Studio (本地模型)」
  4. 載入模型並點擊「用於對話 (Use for Chat)」

---

## 系統需求

- Windows 10 / 11
- 網際網路連線（用於雲端 AI）或 8GB+ 顯存之 NVIDIA GPU（用於本地 AI）
- 無需管理員權限、無需系統 Python、無需 Docker

---

## 開發與版權聲明

- **基礎框架**：[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) (MIT License)
- **便攜發行版與擴展整合**：由 [aivrar](https://github.com/aivrar) 維護
- **多語系支援與介面客製**：Portable Hermes Agent Team

---

## 授權條款

MIT License — 詳情請參閱 [LICENSE](LICENSE)。
