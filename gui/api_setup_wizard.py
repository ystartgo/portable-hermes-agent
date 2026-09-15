"""
Hermes Agent - API Key Setup Wizard
Walks users through getting API keys with multi-language (i18n) support.
Opens signup pages in their real browser, they handle CAPTCHAs,
paste the key back, and we save it automatically.
Supports OpenRouter and TokenTable (https://tokentable.asia/v1, apply: https://top.yia.app/token).
"""
import os
import re
import tkinter as tk
from tkinter import ttk
import webbrowser
from pathlib import Path

from gui.theme import C, FONTS, set_dark_title_bar, Tooltip, SF
from hermes_constants import get_hermes_home
from gui.i18n import t, get_language

PROJECT_ROOT = Path(__file__).parent.parent

# ============================================================================
# API Service Definitions
# ============================================================================

def get_api_services():
    """Return list of API services with localized texts according to active language."""
    lang = get_language()
    is_zh_hant = (lang == "zh-hant")
    is_zh = (lang == "zh")

    if is_zh_hant:
        return [
            {
                "key": "OPENROUTER_API_KEY",
                "name": "OpenRouter",
                "icon": "LLM",
                "what": "驅動所有 AI 對話的核心大腦，支援全球上百種頂級與開源模型。",
                "unlocks": "對話聊天、多模型思考推理、圖像辨識分析",
                "signup_url": "https://openrouter.ai/keys",
                "recommend_url": "https://openrouter.ai/keys",
                "recommend_label": "申請 OpenRouter 金鑰（免費註冊）",
                "steps": [
                    "1. 點擊下方按鈕前往 OpenRouter 官網",
                    "2. 使用 Google 或 Email 登入／註冊（免費，免信用卡）",
                    "3. 在儀表板點擊「Create Key」建立金鑰",
                    "4. 複製金鑰（以 sk-or- 開頭）",
                    "5. 貼在下方輸入框並點擊「儲存並前往下一步」",
                ],
                "free_tier": "提供免費額度 — 多款開源模型完全免費使用",
                "required": False,
                "prefix": "sk-or-",
            },
            {
                "key": "TOKENTABLE_API_KEY",
                "name": "TokenTable",
                "icon": "LLM",
                "what": "AI 大模型聚合平台，支援 300+ 主流模型（Claude、GPT、Gemini 等），固定費率且免翻牆。",
                "unlocks": "對話聊天、深度推理、OpenAI 相容高速通道",
                "signup_url": "https://top.yia.app/token",
                "recommend_url": "https://top.yia.app/token",
                "recommend_label": "推薦申請 TokenTable API Key（開啟 top.yia.app/token）",
                "base_url": "https://tokentable.asia/v1",
                "steps": [
                    "1. 點擊下方「推薦申請按鈕」前往取得 TokenTable API Key",
                    "2. 登入並獲取專屬 API Key（Token）",
                    "3. 複製金鑰並貼到下方輸入框（通常以 sk- 開頭）",
                    "4. Base URL 自動配置為：https://tokentable.asia/v1",
                    "5. 點擊「儲存並前往下一步」即可完成配置",
                ],
                "free_tier": "API 端點伺服器：https://tokentable.asia/v1",
                "required": False,
                "prefix": "sk-",
            },
            {
                "key": "CUSTOM_API",
                "name": "其它 (自訂端點)",
                "icon": "LLM",
                "is_custom": True,
                "what": "自訂 OpenAI 相容 API 端點 — 支援任何中轉站、本地模型（Ollama、vLLM、LM Studio）或自建伺服器。",
                "unlocks": "自訂模型對話、私有大模型、第三方 API 代理通道",
                "steps": [
                    "1. 在下方輸入您的 API Base URL（例如：https://api.openai.com/v1 或 http://localhost:11434/v1）",
                    "2. 在下方輸入您的 API Key（若為本地無密碼模型可填入任意文字或略過）",
                    "3. 點擊「儲存並前往下一步」，系統將自動設定 OPENAI_BASE_URL 與 OPENAI_API_KEY",
                ],
                "free_tier": "相容所有遵循 OpenAI API 規範之伺服器與中轉通道",
                "required": False,
                "prefix": "",
            },
            {
                "key": "FIRECRAWL_API_KEY",
                "name": "Firecrawl",
                "icon": "WEB",
                "what": "網頁搜尋與網頁內容擷取 — 讓 Hermes 能夠即時上網搜尋最新資料。",
                "unlocks": "web_search、web_extract 工具",
                "signup_url": "https://www.firecrawl.dev/app/api-keys",
                "recommend_url": "https://www.firecrawl.dev/app/api-keys",
                "recommend_label": "取得 Firecrawl 金鑰（開啟註冊頁面）",
                "steps": [
                    "1. 點擊下方按鈕前往 Firecrawl 網站",
                    "2. 使用 Google 或 GitHub 免費註冊",
                    "3. 在儀表板進入「API Keys」頁面",
                    "4. 複製您的 API Key",
                    "5. 貼在下方輸入框並點擊儲存",
                ],
                "free_tier": "免費方案：每月 500 點額度（個人使用充裕）",
                "required": False,
                "prefix": "fc-",
            },
            {
                "key": "FAL_KEY",
                "name": "FAL.ai",
                "icon": "IMG",
                "what": "AI 圖片生成 — 讓 Hermes 能根據文字描述繪製高品質圖片。",
                "unlocks": "image_generate 工具（FLUX 模型）",
                "signup_url": "https://fal.ai/dashboard/keys",
                "recommend_url": "https://fal.ai/dashboard/keys",
                "recommend_label": "取得 FAL.ai 金鑰（開啟註冊頁面）",
                "steps": [
                    "1. 點擊下方按鈕前往 FAL.ai 網站",
                    "2. 使用 GitHub 或 Google 免費註冊",
                    "3. 在儀表板進入「Keys」頁面",
                    "4. 建立並複製您的 API Key",
                    "5. 貼在下方輸入框並點擊儲存",
                ],
                "free_tier": "免費方案：註冊贈送 $10 美元體驗額度",
                "required": False,
                "prefix": "",
            },
            {
                "key": "SERPER_API_KEY",
                "name": "Serper (Google Search)",
                "icon": "SRC",
                "what": "Google 等級精準搜尋結果 — 速度快、具結構化資訊與知識圖譜。",
                "unlocks": "serper_search 工具（針對事實性查詢比 DuckDuckGo 更精確）",
                "signup_url": "https://serper.dev/api-key",
                "recommend_url": "https://serper.dev/api-key",
                "recommend_label": "取得 Serper 金鑰（開啟註冊頁面）",
                "steps": [
                    "1. 點擊下方按鈕前往 Serper.dev 網站",
                    "2. 使用 Google 或 Email 免費註冊",
                    "3. 在儀表板直接複製您的 API Key",
                    "4. 貼在下方輸入框並點擊儲存",
                ],
                "free_tier": "免費方案：每月 2,500 次免費搜尋",
                "required": False,
                "prefix": "",
            },
            {
                "key": "BROWSERBASE_API_KEY",
                "name": "Browserbase",
                "icon": "WWW",
                "what": "雲端沙盒瀏覽器 — 具備抗爬蟲防護的雲端真實瀏覽器。",
                "unlocks": "將本機瀏覽器升級為雲端託管模式（選填）",
                "signup_url": "https://www.browserbase.com/sign-up",
                "recommend_url": "https://www.browserbase.com/sign-up",
                "recommend_label": "取得 Browserbase 金鑰（開啟註冊頁面）",
                "steps": [
                    "1. 點擊下方按鈕前往 Browserbase 網站",
                    "2. 免費註冊帳號",
                    "3. 在儀表板複製 API Key 與 Project ID",
                    "4. 貼在下方輸入框",
                    "5. （稍後亦可在設定中配置 BROWSERBASE_PROJECT_ID）",
                ],
                "free_tier": "免費方案：每月 1,000 次瀏覽工作階段",
                "required": False,
                "prefix": "",
            },
        ]
    elif is_zh:
        return [
            {
                "key": "OPENROUTER_API_KEY",
                "name": "OpenRouter",
                "icon": "LLM",
                "what": "驱动所有 AI 对话的核心大脑，支持全球上百种顶尖与开源模型。",
                "unlocks": "对话聊天、多模型思考推理、图像识别分析",
                "signup_url": "https://openrouter.ai/keys",
                "recommend_url": "https://openrouter.ai/keys",
                "recommend_label": "申请 OpenRouter 密钥（免费注册）",
                "steps": [
                    "1. 点击下方按钮前往 OpenRouter 官网",
                    "2. 使用 Google 或 Email 登录／注册（免费，免信用卡）",
                    "3. 在仪表板点击「Create Key」创建密钥",
                    "4. 复制密钥（以 sk-or- 开头）",
                    "5. 粘贴至下方输入框并点击「保存并前往下一步」",
                ],
                "free_tier": "提供免费额度 — 多款开源模型完全免费使用",
                "required": False,
                "prefix": "sk-or-",
            },
            {
                "key": "TOKENTABLE_API_KEY",
                "name": "TokenTable",
                "icon": "LLM",
                "what": "AI 大模型聚合平台，支持 300+ 主流模型（Claude、GPT、Gemini 等），固定费率且免翻墙。",
                "unlocks": "对话聊天、深度推理、OpenAI 兼容高速通道",
                "signup_url": "https://top.yia.app/token",
                "recommend_url": "https://top.yia.app/token",
                "recommend_label": "推荐申请 TokenTable API Key（打开 top.yia.app/token）",
                "base_url": "https://tokentable.asia/v1",
                "steps": [
                    "1. 点击下方「推荐申请按钮」前往获取 TokenTable API Key",
                    "2. 登录并获取专属 API Key（Token）",
                    "3. 复制密钥并粘贴至下方输入框（通常以 sk- 开头）",
                    "4. Base URL 自动配置为：https://tokentable.asia/v1",
                    "5. 点击「保存并前往下一步」即可完成配置",
                ],
                "free_tier": "API 端点服务器：https://tokentable.asia/v1",
                "required": False,
                "prefix": "sk-",
            },
            {
                "key": "CUSTOM_API",
                "name": "其它 (自订端点)",
                "icon": "LLM",
                "is_custom": True,
                "what": "自订 OpenAI 兼容 API 端点 — 支持任何中转站、本地模型（Ollama、vLLM、LM Studio）或自建服务器。",
                "unlocks": "自定义模型对话、私有大模型、第三方 API 代理通道",
                "steps": [
                    "1. 在下方输入您的 API Base URL（例如：https://api.openai.com/v1 或 http://localhost:11434/v1）",
                    "2. 在下方输入您的 API Key（若为本地无密码模型可填入任意字符或略过）",
                    "3. 点击「保存并前往下一步」，系统将自动配置 OPENAI_BASE_URL 与 OPENAI_API_KEY",
                ],
                "free_tier": "兼容所有遵循 OpenAI API 规范之服务器与中转通道",
                "required": False,
                "prefix": "",
            },
            {
                "key": "FIRECRAWL_API_KEY",
                "name": "Firecrawl",
                "icon": "WEB",
                "what": "网页搜索与网页内容提取 — 让 Hermes 能够即时上网搜索最新资料。",
                "unlocks": "web_search、web_extract 工具",
                "signup_url": "https://www.firecrawl.dev/app/api-keys",
                "recommend_url": "https://www.firecrawl.dev/app/api-keys",
                "recommend_label": "获取 Firecrawl 密钥（打开注册页面）",
                "steps": [
                    "1. 点击下方按钮前往 Firecrawl 网站",
                    "2. 使用 Google 或 GitHub 免费注册",
                    "3. 在控制台进入「API Keys」页面",
                    "4. 复制您的 API Key",
                    "5. 粘贴至下方输入框并点击保存",
                ],
                "free_tier": "免费方案：每月 500 额度（个人使用充裕）",
                "required": False,
                "prefix": "fc-",
            },
            {
                "key": "FAL_KEY",
                "name": "FAL.ai",
                "icon": "IMG",
                "what": "AI 图片生成 — 让 Hermes 能根据文字描述绘制高质量图片。",
                "unlocks": "image_generate 工具（FLUX 模型）",
                "signup_url": "https://fal.ai/dashboard/keys",
                "recommend_url": "https://fal.ai/dashboard/keys",
                "recommend_label": "获取 FAL.ai 密钥（打开注册页面）",
                "steps": [
                    "1. 点击下方按钮前往 FAL.ai 网站",
                    "2. 使用 GitHub 或 Google 免费注册",
                    "3. 在控制台进入「Keys」页面",
                    "4. 创建并复制您的 API Key",
                    "5. 粘贴至下方输入框并点击保存",
                ],
                "free_tier": "免费方案：注册赠送 $10 美元体验额度",
                "required": False,
                "prefix": "",
            },
            {
                "key": "SERPER_API_KEY",
                "name": "Serper (Google Search)",
                "icon": "SRC",
                "what": "Google 级别精准搜索结果 — 速度快、具结构化信息与知识图谱。",
                "unlocks": "serper_search 工具（针对事实性查询比 DuckDuckGo 更精确）",
                "signup_url": "https://serper.dev/api-key",
                "recommend_url": "https://serper.dev/api-key",
                "recommend_label": "获取 Serper 密钥（打开注册页面）",
                "steps": [
                    "1. 点击下方按钮前往 Serper.dev 网站",
                    "2. 使用 Google 或 Email 免费注册",
                    "3. 在控制台直接复制您的 API Key",
                    "4. 粘贴至下方输入框并点击保存",
                ],
                "free_tier": "免费方案：每月 2,500 次免费搜索",
                "required": False,
                "prefix": "",
            },
            {
                "key": "BROWSERBASE_API_KEY",
                "name": "Browserbase",
                "icon": "WWW",
                "what": "云端沙盒浏览器 — 具备反爬虫防护的云端真实浏览器。",
                "unlocks": "将本地浏览器升级为云端托管模式（选填）",
                "signup_url": "https://www.browserbase.com/sign-up",
                "recommend_url": "https://www.browserbase.com/sign-up",
                "recommend_label": "获取 Browserbase 密钥（打开注册页面）",
                "steps": [
                    "1. 点击下方按钮前往 Browserbase 网站",
                    "2. 免费注册账号",
                    "3. 在控制台复制 API Key 与 Project ID",
                    "4. 粘贴至下方输入框",
                    "5. （稍后亦可在设置中配置 BROWSERBASE_PROJECT_ID）",
                ],
                "free_tier": "免费方案：每月 1,000 次浏览会话",
                "required": False,
                "prefix": "",
            },
        ]
    else:
        return [
            {
                "key": "OPENROUTER_API_KEY",
                "name": "OpenRouter",
                "icon": "LLM",
                "what": "Powers all AI conversations — this is the brain.",
                "unlocks": "Chat, vision analysis, multi-model reasoning",
                "signup_url": "https://openrouter.ai/keys",
                "recommend_url": "https://openrouter.ai/keys",
                "recommend_label": "Get OpenRouter Key (Free Signup)",
                "steps": [
                    "1. Click 'Get Key' below — it opens OpenRouter in your browser",
                    "2. Sign up with Google or email (free, no credit card)",
                    "3. Click 'Create Key' on their dashboard",
                    "4. Copy the key (starts with sk-or-...)",
                    "5. Paste it below and click Save",
                ],
                "free_tier": "Free tier available — many models are free",
                "required": False,
                "prefix": "sk-or-",
            },
            {
                "key": "TOKENTABLE_API_KEY",
                "name": "TokenTable",
                "icon": "LLM",
                "what": "Unified AI Model Gateway — 300+ top models with flat pricing and OpenAI compatibility.",
                "unlocks": "Chat, deep reasoning, OpenAI compatible high-speed endpoints",
                "signup_url": "https://top.yia.app/token",
                "recommend_url": "https://top.yia.app/token",
                "recommend_label": "Recommended: Get TokenTable Key (top.yia.app/token)",
                "base_url": "https://tokentable.asia/v1",
                "steps": [
                    "1. Click 'Get Key' below to get your TokenTable API Key",
                    "2. Log in and acquire your dedicated token/API key",
                    "3. Copy the key (starts with sk-...)",
                    "4. Base URL is automatically configured to: https://tokentable.asia/v1",
                    "5. Paste it below and click Save & Next",
                ],
                "free_tier": "API endpoint: https://tokentable.asia/v1",
                "required": False,
                "prefix": "sk-",
            },
            {
                "key": "CUSTOM_API",
                "name": "Other (Custom Endpoint)",
                "icon": "LLM",
                "is_custom": True,
                "what": "Custom OpenAI-compatible API endpoint — connect to Ollama, vLLM, LM Studio, self-hosted servers, or third-party proxies.",
                "unlocks": "Custom model chat, local private LLMs, third-party API gateways",
                "steps": [
                    "1. Enter your API Base URL below (e.g. https://api.openai.com/v1 or http://localhost:11434/v1)",
                    "2. Enter your API Key below (can be any string for keyless local models)",
                    "3. Click 'Save & Next' — system will auto-configure OPENAI_BASE_URL and OPENAI_API_KEY",
                ],
                "free_tier": "Compatible with all OpenAI-compatible endpoints",
                "required": False,
                "prefix": "",
            },
            {
                "key": "FIRECRAWL_API_KEY",
                "name": "Firecrawl",
                "icon": "WEB",
                "what": "Web search and webpage reading — lets Hermes find info online.",
                "unlocks": "web_search, web_extract tools",
                "signup_url": "https://www.firecrawl.dev/app/api-keys",
                "recommend_url": "https://www.firecrawl.dev/app/api-keys",
                "recommend_label": "Get Firecrawl Key",
                "steps": [
                    "1. Click 'Get Key' below — it opens Firecrawl in your browser",
                    "2. Sign up with Google or GitHub (free)",
                    "3. Go to API Keys in their dashboard",
                    "4. Copy your API key",
                    "5. Paste it below and click Save",
                ],
                "free_tier": "Free: 500 credits/month (plenty for personal use)",
                "required": False,
                "prefix": "fc-",
            },
            {
                "key": "FAL_KEY",
                "name": "FAL.ai",
                "icon": "IMG",
                "what": "Image generation — Hermes can create images from descriptions.",
                "unlocks": "image_generate tool (FLUX model)",
                "signup_url": "https://fal.ai/dashboard/keys",
                "recommend_url": "https://fal.ai/dashboard/keys",
                "recommend_label": "Get FAL.ai Key",
                "steps": [
                    "1. Click 'Get Key' below — it opens FAL.ai in your browser",
                    "2. Sign up with GitHub or Google (free)",
                    "3. Go to Keys in their dashboard",
                    "4. Create and copy your API key",
                    "5. Paste it below and click Save",
                ],
                "free_tier": "Free: $10 in credits to start",
                "required": False,
                "prefix": "",
            },
            {
                "key": "SERPER_API_KEY",
                "name": "Serper (Google Search)",
                "icon": "SRC",
                "what": "Google-quality search results — structured, fast, with knowledge graphs.",
                "unlocks": "serper_search tool (better than DuckDuckGo for factual queries)",
                "signup_url": "https://serper.dev/api-key",
                "recommend_url": "https://serper.dev/api-key",
                "recommend_label": "Get Serper Key",
                "steps": [
                    "1. Click 'Get Key' below — it opens Serper.dev in your browser",
                    "2. Sign up with Google or email (free)",
                    "3. Copy your API key from the dashboard",
                    "4. Paste it below and click Save",
                ],
                "free_tier": "Free: 2,500 searches/month",
                "required": False,
                "prefix": "",
            },
            {
                "key": "BROWSERBASE_API_KEY",
                "name": "Browserbase",
                "icon": "WWW",
                "what": "Cloud browser — faster web browsing with anti-bot protection.",
                "unlocks": "Upgrades browser from local to cloud (optional)",
                "signup_url": "https://www.browserbase.com/sign-up",
                "recommend_url": "https://www.browserbase.com/sign-up",
                "recommend_label": "Get Browserbase Key",
                "steps": [
                    "1. Click 'Get Key' below — it opens Browserbase in your browser",
                    "2. Sign up (free tier available)",
                    "3. Copy your API Key AND Project ID from the dashboard",
                    "4. Paste the API key below",
                    "5. (You'll also need to set BROWSERBASE_PROJECT_ID in Settings)",
                ],
                "free_tier": "Free tier: 1000 browser sessions/month",
                "required": False,
                "prefix": "",
            },
        ]

API_SERVICES = get_api_services()


def _save_key_to_env(key: str, value: str):
    """Save an API key to .env file and set it in the current environment."""
    os.environ[key] = value
    env_path = get_hermes_home() / ".env"
    env_path.parent.mkdir(parents=True, exist_ok=True)
    content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""

    pattern = f"^{key}=.*$"
    replacement = f"{key}={value}"
    if re.search(pattern, content, re.MULTILINE):
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    else:
        content += f"\n{replacement}\n"

    env_path.write_text(content, encoding="utf-8")


def get_missing_keys():
    """Return list of API services that don't have keys set."""
    missing = []
    has_llm = bool(
        os.getenv("OPENROUTER_API_KEY")
        or os.getenv("TOKENTABLE_API_KEY")
        or os.getenv("CUSTOM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENAI_BASE_URL")
    )
    for svc in get_api_services():
        if svc["icon"] == "LLM" and has_llm:
            continue
        if svc.get("is_custom"):
            has_this = bool(os.getenv("CUSTOM_API_KEY") or (os.getenv("OPENAI_BASE_URL") and os.getenv("OPENAI_API_KEY")))
        else:
            has_this = bool(os.getenv(svc["key"]))
        if not has_this:
            missing.append(svc)
    return missing


def get_key_status():
    """Return dict of key -> bool for all services."""
    res = {}
    for svc in get_api_services():
        if svc.get("is_custom"):
            res[svc["key"]] = bool(os.getenv("CUSTOM_API_KEY") or (os.getenv("OPENAI_BASE_URL") and os.getenv("OPENAI_API_KEY")))
        else:
            res[svc["key"]] = bool(os.getenv(svc["key"]))
    return res


# ============================================================================
# Setup Wizard GUI
# ============================================================================

class APISetupWizard(tk.Toplevel):
    """
    Step-by-step wizard that walks users through getting API keys.
    Opens signup pages in their real browser, they paste keys back.
    """

    def __init__(self, parent, on_complete=None, auto_mode=False, single_service=None):
        super().__init__(parent)
        self.on_complete = on_complete
        self.auto_mode = auto_mode
        self.title(t("wizard.title", "Hermes Agent - API 設定精靈"))
        self.configure(bg=C["bg_main"])
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)
        self.minsize(620, 620)
        set_dark_title_bar(self)

        from gui.theme import center_window
        center_window(self, 640, 660, parent)

        self.current_step = -1
        self.key_entries = {}
        self.saved_keys = {}

        all_services = get_api_services()

        if single_service:
            svc = next((s for s in all_services if s["key"] == single_service), None)
            if svc:
                self.services = [svc]
                self.current_step = 0
                self._show_service(svc)
                return

        if auto_mode:
            self.services = get_missing_keys()
        else:
            self.services = list(all_services)

        self._show_welcome()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _show_welcome(self):
        self._clear()

        # Header
        hdr = tk.Frame(self, bg=C["bg_main"])
        hdr.pack(fill="x", padx=40, pady=(28, 0))

        tk.Label(hdr, text=t("wizard.header", "API 金鑰設定精靈"), font=FONTS["title"],
                fg=C["accent"], bg=C["bg_main"]).pack(anchor="w")
        tk.Label(hdr, text=t("wizard.subtitle", "為 Hermes Agent 配置智慧核心與強大工具"),
                font=FONTS["body"], fg=C["text_secondary"],
                bg=C["bg_main"]).pack(anchor="w", pady=(4, 0))

        # Status overview
        status_frame = tk.Frame(self, bg=C["bg_main"])
        status_frame.pack(fill="x", padx=40, pady=(16, 0))

        tk.Label(status_frame, text=t("wizard.status_header", "服務連線狀態："),
                font=FONTS["subheading"], fg=C["text_primary"],
                bg=C["bg_main"]).pack(anchor="w", pady=(0, 8))

        has_llm = bool(
            os.getenv("OPENROUTER_API_KEY")
            or os.getenv("TOKENTABLE_API_KEY")
            or os.getenv("CUSTOM_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("OPENAI_BASE_URL")
        )

        all_services = get_api_services()
        for svc in all_services:
            if svc.get("is_custom"):
                has_key = bool(os.getenv("CUSTOM_API_KEY") or (os.getenv("OPENAI_BASE_URL") and os.getenv("OPENAI_API_KEY")))
            else:
                has_key = bool(os.getenv(svc["key"]))
            is_llm = (svc.get("icon") == "LLM")

            if has_key:
                dot_color = C["success"]
                status_text = t("wizard.status_ready", "已就緒")
            elif svc["required"]:
                dot_color = C["danger"]
                status_text = t("wizard.status_required", "必要")
            else:
                dot_color = C["text_disabled"] if (is_llm and has_llm) else C["warning_dark"]
                status_text = t("wizard.status_not_set", "未設定")

            row = tk.Frame(status_frame, bg=C["bg_main"], cursor="hand2",
                          padx=4, pady=3)
            row.pack(fill="x", pady=1)

            tk.Label(row, text="\u25CF", font=SF("Segoe UI", 10),
                    fg=dot_color, bg=C["bg_main"]).pack(side="left", padx=(0, 8))
            tk.Label(row, text=f"[{svc['icon']}]", font=FONTS["mono_small"],
                    fg=C["text_disabled"], bg=C["bg_main"]).pack(side="left", padx=(0, 6))
            tk.Label(row, text=svc["name"], font=FONTS["body"],
                    fg=C["text_primary"], bg=C["bg_main"]).pack(side="left")
            tk.Label(row, text=status_text, font=FONTS["small"],
                    fg=dot_color, bg=C["bg_main"]).pack(side="right")
            tk.Label(row, text=f"  {t('wizard.setup_action', '設定')}", font=SF("Segoe UI", 8, "underline"),
                    fg=C["accent"], bg=C["bg_main"], cursor="hand2").pack(side="right")

            def _on_click(event, s=svc):
                self.services = [s]
                self.current_step = 0
                self._show_service(s)

            row.bind("<Button-1>", _on_click)
            for child in row.winfo_children():
                child.bind("<Button-1>", _on_click)

        if not self.services:
            tk.Label(self, text=t("wizard.all_set", "所有金鑰皆已設定完成！隨時可以開始對話。"),
                    font=FONTS["body"], fg=C["success"],
                    bg=C["bg_main"]).pack(pady=20)
            ttk.Button(self, text=t("wizard.close", "關閉"), style="Primary.TButton",
                       command=self._finish).pack(pady=10)
        else:
            missing_count = len(self.services)
            intro_msg = t("wizard.missing_intro",
                          "\n尚有 {count} 項服務可供設定，每項大約只需 1 分鐘。\n點擊按鈕開啟申請網頁 — 取得金鑰後複製，\n貼回此處即可自動儲存生效。",
                          count=missing_count)
            tk.Label(self, text=intro_msg,
                    font=FONTS["body"], fg=C["text_secondary"],
                    bg=C["bg_main"], justify="center").pack(pady=(12, 0))

            btn_frame = tk.Frame(self, bg=C["bg_main"])
            btn_frame.pack(pady=18)

            ttk.Button(btn_frame, text=t("wizard.lets_go", "開始設定！"), style="Primary.TButton",
                       command=self._next_step).pack(side="left", padx=4)
            ttk.Button(btn_frame, text=t("wizard.skip_all", "全部略過"), style="TButton",
                       command=self._finish).pack(side="left", padx=4)

    def _next_step(self):
        self.current_step += 1
        if self.current_step >= len(self.services):
            self._show_done()
            return
        self._show_service(self.services[self.current_step])

    def _show_service(self, svc):
        self._clear()

        key_name = svc["key"]
        step_num = self.current_step + 1
        total = len(self.services)

        # Progress bar (top)
        prog_frame = tk.Frame(self, bg=C["bg_sidebar"], height=4)
        prog_frame.pack(side="top", fill="x")
        prog_frame.pack_propagate(False)
        pct = step_num / total
        prog_fill = tk.Frame(prog_frame, bg=C["accent"], width=int(640 * pct))
        prog_fill.pack(side="left", fill="y")

        # Bottom action buttons (ALWAYS pinned at bottom of window so never cut off)
        bottom = tk.Frame(self, bg=C["bg_main"])
        bottom.pack(side="bottom", fill="x", padx=40, pady=(10, 16))

        ttk.Button(bottom, text=t("wizard.save_next", "儲存並前往下一步"), style="Primary.TButton",
                   command=lambda: self._save_current(svc)).pack(side="right")
        ttk.Button(bottom, text=t("wizard.skip", "略過"), style="TButton",
                   command=self._next_step).pack(side="right", padx=(0, 8))

        # Main content area (packed top-to-bottom)
        # Header
        hdr = tk.Frame(self, bg=C["bg_main"])
        hdr.pack(fill="x", padx=40, pady=(14, 0))

        step_text = t("wizard.step_progress", "步驟 {step} / {total}", step=step_num, total=total)
        tk.Label(hdr, text=step_text,
                font=FONTS["small"], fg=C["text_hint"],
                bg=C["bg_main"]).pack(anchor="w")
        tk.Label(hdr, text=f"[{svc['icon']}] {svc['name']}",
                font=FONTS["heading"], fg=C["accent"],
                bg=C["bg_main"]).pack(anchor="w", pady=(2, 0))
        tk.Label(hdr, text=svc["what"], font=FONTS["body"],
                fg=C["text_primary"], bg=C["bg_main"], wraplength=550, justify="left").pack(anchor="w", pady=(2, 0))

        # Unlocks & Free tier
        unlocks_text = t("wizard.unlocks", "解鎖功能：{features}", features=svc["unlocks"])
        tk.Label(hdr, text=unlocks_text,
                font=FONTS["small"], fg=C["success"],
                bg=C["bg_main"]).pack(anchor="w", pady=(2, 0))
        tk.Label(hdr, text=svc["free_tier"],
                font=FONTS["small"], fg=C["warning_dark"],
                bg=C["bg_main"]).pack(anchor="w")

        # Steps frame
        steps_frame = tk.Frame(self, bg=C["bg_card"], padx=14, pady=8,
                              highlightbackground=C["border"], highlightthickness=1)
        steps_frame.pack(fill="x", padx=40, pady=(10, 0))

        for s_text in svc["steps"]:
            tk.Label(steps_frame, text=s_text, font=FONTS["body"],
                    fg=C["text_primary"], bg=C["bg_card"],
                    anchor="w", justify="left").pack(fill="x", pady=1)

        # Action buttons
        rec_url = svc.get("recommend_url") or svc.get("signup_url")
        if rec_url:
            btn_frame = tk.Frame(self, bg=C["bg_main"])
            btn_frame.pack(fill="x", padx=40, pady=(10, 0))

            rec_label = svc.get("recommend_label", f"前往申請 {svc['name']} 金鑰")
            rec_btn = ttk.Button(btn_frame, text=f"👉 {rec_label}",
                                 style="Primary.TButton",
                                 command=lambda u=rec_url: webbrowser.open(u))
            rec_btn.pack(fill="x")
            Tooltip(rec_btn, f"在瀏覽器中開啟 {rec_url}")

        # Base URL input or display
        if svc.get("is_custom"):
            url_frame = tk.Frame(self, bg=C["bg_main"])
            url_frame.pack(fill="x", padx=40, pady=(8, 0))
            tk.Label(url_frame, text=t("wizard.custom_url_label", "API Base URL（伺服器端點網址）："),
                    font=FONTS["small"], fg=C["text_secondary"],
                    bg=C["bg_main"]).pack(anchor="w")
            self.base_url_entry = tk.Entry(url_frame, font=FONTS["mono_small"],
                                           bg=C["bg_input"], fg=C["text_primary"],
                                           insertbackground=C["text_primary"],
                                           relief="flat")
            self.base_url_entry.pack(fill="x", ipady=5, pady=(2, 0))
            cur_base = os.getenv("CUSTOM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or ""
            if cur_base:
                self.base_url_entry.insert(0, cur_base)
            tk.Label(url_frame,
                     text=t("wizard.custom_url_hint", "例如：https://api.openai.com/v1 或 http://localhost:11434/v1"),
                     font=SF("Segoe UI", 8), fg=C["text_hint"],
                     bg=C["bg_main"]).pack(anchor="w", pady=(1, 0))
        elif svc.get("base_url"):
            base_frame = tk.Frame(self, bg=C["bg_main"])
            base_frame.pack(fill="x", padx=40, pady=(6, 0))
            tk.Label(base_frame, text=t("wizard.base_url_label", "API Base URL（已自動配置）："),
                    font=FONTS["small"], fg=C["text_secondary"],
                    bg=C["bg_main"]).pack(side="left")
            base_lbl = tk.Label(base_frame, text=svc["base_url"],
                                font=FONTS["mono_small"], fg=C["accent"],
                                bg=C["bg_card"], padx=6, pady=2)
            base_lbl.pack(side="left", padx=(4, 0))

        # Key entry
        entry_frame = tk.Frame(self, bg=C["bg_main"])
        entry_frame.pack(fill="x", padx=40, pady=(8, 0))

        if svc.get("is_custom"):
            lbl_text = t("wizard.custom_key_label", "API Key（金鑰，若本地無密碼可填隨意字元）：")
        else:
            lbl_text = t("wizard.paste_label", "請在此處貼上您的金鑰 (API Key)：")

        tk.Label(entry_frame, text=lbl_text,
                font=FONTS["small"], fg=C["text_secondary"],
                bg=C["bg_main"]).pack(anchor="w")

        key_entry = tk.Entry(entry_frame, font=FONTS["mono"],
                            bg=C["bg_input"], fg=C["text_primary"],
                            insertbackground=C["text_primary"],
                            relief="flat")
        key_entry.pack(fill="x", ipady=6, pady=(3, 0))

        if svc.get("is_custom"):
            current = os.getenv("CUSTOM_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
        else:
            current = os.getenv(key_name, "")
        if current:
            key_entry.insert(0, current)

        self.key_entries[key_name] = key_entry

        clip_frame = tk.Frame(entry_frame, bg=C["bg_main"])
        clip_frame.pack(fill="x", pady=(4, 0))

        ttk.Button(clip_frame, text=t("wizard.paste_clip", "從剪貼簿貼上"),
                   style="Small.TButton",
                   command=lambda: self._paste_from_clipboard(key_entry)).pack(side="left")

        tk.Label(clip_frame, text=t("wizard.paste_hint", "  在網站複製金鑰後，點擊此按鈕或直接貼上"),
                font=SF("Segoe UI", 8), fg=C["text_hint"],
                bg=C["bg_main"]).pack(side="left")

        self.status_label = tk.Label(entry_frame, text="", font=FONTS["small"],
                                    bg=C["bg_main"])
        self.status_label.pack(anchor="w", pady=(2, 0))

        try:
            self._clip_snapshot = self.clipboard_get().strip()
        except tk.TclError:
            self._clip_snapshot = ""

        self._poll_clipboard(key_entry, svc)

        if svc.get("is_custom") and hasattr(self, "base_url_entry") and not self.base_url_entry.get().strip():
            self.base_url_entry.focus_set()
            self.base_url_entry.bind("<Return>", lambda e: key_entry.focus_set())
        else:
            key_entry.focus_set()

        key_entry.bind("<Return>", lambda e: self._save_current(svc))

    def _paste_from_clipboard(self, entry):
        try:
            clip = self.clipboard_get().strip()
            if clip:
                entry.delete(0, "end")
                entry.insert(0, clip)
        except tk.TclError:
            pass

    def _poll_clipboard(self, entry, svc):
        if not self.winfo_exists():
            return
        try:
            clip = self.clipboard_get().strip()
        except tk.TclError:
            clip = ""

        if clip and clip != self._clip_snapshot:
            if clip.startswith("http://") or clip.startswith("https://"):
                return

            current = entry.get().strip()
            prefix = svc.get("prefix", "")
            is_key = False

            if prefix and clip.startswith(prefix) and len(clip) > 15:
                is_key = True
            elif not prefix and len(clip) > 15 and " " not in clip and "\n" not in clip:
                is_key = True

            if is_key and clip != current:
                entry.delete(0, "end")
                entry.insert(0, clip)
                self._clip_snapshot = clip
                self.status_label.configure(
                    text=t("wizard.clip_detected", "已從剪貼簿偵測到金鑰！"),
                    fg=C["success"])

        try:
            self.after(2000, lambda: self._poll_clipboard(entry, svc))
        except tk.TclError:
            pass

    def _save_current(self, svc):
        key_name = svc["key"]
        entry = self.key_entries.get(key_name)
        if not entry:
            self._next_step()
            return

        if svc.get("is_custom"):
            base_url = ""
            if hasattr(self, "base_url_entry") and self.base_url_entry.winfo_exists():
                base_url = self.base_url_entry.get().strip()
            value = entry.get().strip()

            if not base_url and not value:
                self.status_label.configure(text=t("wizard.no_setting", "未輸入任何設定 — 已略過。"),
                                           fg=C["warning_dark"])
                self.after(1000, self._next_step)
                return

            if base_url:
                base_url = base_url.rstrip("/")
                _save_key_to_env("CUSTOM_BASE_URL", base_url)
                _save_key_to_env("OPENAI_BASE_URL", base_url)
            if value:
                _save_key_to_env("OPENAI_API_KEY", value)
                _save_key_to_env("CUSTOM_API_KEY", value)

            self.saved_keys[key_name] = True
            self.status_label.configure(text=t("wizard.saved", "已成功儲存！"), fg=C["success"])
            self.after(500, self._next_step)
            return

        value = entry.get().strip()
        if not value:
            self.status_label.configure(text=t("wizard.no_key", "未輸入金鑰 — 已略過。"),
                                       fg=C["warning_dark"])
            self.after(1000, self._next_step)
            return

        if svc.get("prefix") and not value.startswith(svc["prefix"]):
            hint_msg = t("wizard.prefix_hint",
                         "提示：金鑰通常以「{prefix}」開頭 — 仍為您儲存。",
                         prefix=svc["prefix"])
            self.status_label.configure(text=hint_msg, fg=C["warning_dark"])

        _save_key_to_env(key_name, value)
        self.saved_keys[key_name] = True

        if key_name == "TOKENTABLE_API_KEY":
            base_url = svc.get("base_url", "https://tokentable.asia/v1")
            _save_key_to_env("CUSTOM_BASE_URL", base_url)
            _save_key_to_env("OPENAI_BASE_URL", base_url)
            _save_key_to_env("OPENAI_API_KEY", value)

        self.status_label.configure(text=t("wizard.saved", "已成功儲存！"), fg=C["success"])
        self.after(500, self._next_step)

    def _show_done(self):
        self._clear()

        prog_frame = tk.Frame(self, bg=C["accent"], height=4)
        prog_frame.pack(fill="x")

        tk.Label(self, text=t("wizard.done_title", "設定完成！"), font=FONTS["title"],
                fg=C["accent"], bg=C["bg_main"]).pack(pady=(36, 8))

        saved_count = len(self.saved_keys)
        if saved_count > 0:
            done_msg = t("wizard.done_saved", "已成功儲存 {count} 項 API 服務金鑰。", count=saved_count)
            tk.Label(self, text=done_msg, font=FONTS["body"], fg=C["success"], bg=C["bg_main"]).pack()
        else:
            done_none_msg = t("wizard.done_none", "本次未新增任何金鑰。")
            tk.Label(self, text=done_none_msg, font=FONTS["body"], fg=C["text_hint"], bg=C["bg_main"]).pack()

        status_frame = tk.Frame(self, bg=C["bg_main"])
        status_frame.pack(fill="x", padx=40, pady=(18, 0))

        all_services = get_api_services()
        for svc in all_services:
            row = tk.Frame(status_frame, bg=C["bg_main"])
            row.pack(fill="x", pady=2)

            if svc.get("is_custom"):
                has_key = bool(os.getenv("CUSTOM_API_KEY") or (os.getenv("OPENAI_BASE_URL") and os.getenv("OPENAI_API_KEY")))
            else:
                has_key = bool(os.getenv(svc["key"]))
            dot_color = C["success"] if has_key else C["text_disabled"]
            status_text = t("wizard.status_ready", "已就緒") if has_key else t("wizard.status_not_set", "未設定")

            tk.Label(row, text="\u25CF", font=SF("Segoe UI", 10),
                    fg=dot_color, bg=C["bg_main"]).pack(side="left", padx=(0, 8))
            tk.Label(row, text=svc["name"], font=FONTS["body"],
                    fg=C["text_primary"], bg=C["bg_main"]).pack(side="left")
            tk.Label(row, text=status_text,
                    font=FONTS["small"], fg=dot_color,
                    bg=C["bg_main"]).pack(side="right")

        hint_msg = t("wizard.done_hint",
                     "\n您可以隨時在頂部選單「檔案 > API 金鑰設定」\n或「設定」中新增、切換與修改金鑰。")
        tk.Label(self, text=hint_msg,
                font=FONTS["small"], fg=C["text_hint"],
                bg=C["bg_main"], justify="center").pack(pady=(16, 0))

        ttk.Button(self, text=t("wizard.start_chatting", "開始對話！"), style="Primary.TButton",
                   command=self._finish).pack(side="bottom", pady=(0, 24))

    def _finish(self):
        if self.on_complete:
            self.on_complete(self.saved_keys)
        self.destroy()
