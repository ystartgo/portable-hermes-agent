"""
Hermes Agent - GUI Internationalization (i18n)
Supports Traditional Chinese (zh-hant), Simplified Chinese (zh), and English (en).
Provides runtime language switching with automatic persistence.
"""
from __future__ import annotations

import os
import locale
import logging
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES: List[Tuple[str, str]] = [
    ("zh-hant", "繁體中文"),
    ("zh", "简体中文"),
    ("en", "English"),
]

LANGUAGE_CODES = [code for code, _ in SUPPORTED_LANGUAGES]
DEFAULT_LANGUAGE = "en"

# Translation dictionary
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # App & Window
        "app.title": "Portable Hermes Agent",
        "app.exit_confirm": "Agent is still running. Exit anyway?",

        # Menu bar
        "menu.file": "File",
        "menu.view": "View",
        "menu.language": "Language",
        "menu.help": "Help",
        "menu.new_chat": "New Chat",
        "menu.api_setup": "API Key Setup",
        "menu.permissions": "Permissions",
        "menu.settings": "Settings",
        "menu.exit": "Exit",
        "menu.lm_studio": "LM Studio (Local Models)",
        "menu.skills": "Skills Browser",
        "menu.extensions": "Extensions",
        "menu.toggle_sidebar": "Toggle Sidebar",
        "menu.about": "About",

        # Sidebar
        "sidebar.new_chat": "+ New Chat",
        "sidebar.model": "Model:",
        "sidebar.recent_sessions": "Recent Sessions",
        "sidebar.no_sessions": "No recent sessions",
        "sidebar.delete_title": "Delete Session",
        "sidebar.delete_confirm": "Are you sure you want to delete session '{session_id}'?\n\nThis cannot be undone.",
        "sidebar.local_settings": "Local Model Settings",
        "sidebar.gpu_offload": "GPU Offload:",
        "sidebar.context_len": "Context Length:",
        "sidebar.threads": "CPU Threads:",
        "sidebar.temp": "Temperature:",
        "sidebar.loading_model": "Loading model...",
        "sidebar.model_loaded": "Model loaded",
        "sidebar.load_failed": "Failed to load: {error}",

        # Chat Area
        "chat.new_chat_title": "New Chat",
        "chat.attach": "📎 Attach",
        "chat.attach_tooltip": "Attach image (Ctrl+Shift+I)",
        "chat.send": "Send",
        "chat.send_tooltip": "Send message (Enter)",
        "chat.stop": "Stop",
        "chat.stop_tooltip": "Stop generation (Escape)",
        "chat.copy_all": "Copy All",
        "chat.select_all": "Select All",
        "chat.you": "You",
        "chat.hermes": "Hermes",
        "chat.tool": "Tool: {name}",
        "chat.error": "Error",
        "chat.system": "System",
        "chat.loading_image": "Loading image...",
        "chat.welcome_configured": (
            "Welcome to Portable Hermes Agent!\n"
            "Type a message below and press Enter to chat.\n"
            "Shift+Enter for newlines. Escape to interrupt."
        ),
        "chat.welcome_guided": (
            "Welcome to Portable Hermes Agent!\n\n"
            "No AI model is connected yet, but that's OK!\n"
            "I'm running in guided mode — ask me anything and I'll "
            "search the built-in guide for answers.\n\n"
            "Try typing:\n"
            "  • How do I get started?\n"
            "  • What is OpenRouter?\n"
            "  • How do I use local models?\n"
            "  • What can Hermes do?\n\n"
            "Or go to File > API Key Setup to connect an AI model."
        ),
        "chat.lm_fallback": (
            "LM Studio not detected. Local model \"{orig}\" unavailable.\n"
            "Using {model} instead. Start LM Studio and select your local model from the dropdown to switch back."
        ),

        # Status Bar
        "status.ready": "Ready",
        "status.thinking": "Thinking...",
        "status.running": "Running: {name}",
        "status.error": "Error",
        "status.step": "Step {n}",

        # Settings Dialog
        "settings.title": "Settings",
        "settings.tab_general": "  General  ",
        "settings.tab_api": "  API Keys  ",
        "settings.tab_model": "  Model  ",
        "settings.language": "Interface Language",
        "settings.default_model": "Default Model",
        "settings.model_hint": "You can type any OpenRouter model ID",
        "settings.save": "Save & Close",

        # Skills Browser
        "skills.title": "Skills Browser",
        "skills.search": "Search skills...",
        "skills.installed": "Installed",
        "skills.all": "All",
        "skills.close": "Close",

        # Permissions Panel
        "perms.title": "Permissions",
        "perms.subtitle": "Control what Hermes is allowed to do on your computer",
        "perms.save": "Save Permissions",
        "perms.cancel": "Cancel",
        "perms.reset": "Reset to Defaults",

        # Extensions
        "ext.title": "Extensions Manager",
        "ext.subtitle": "Install and manage portable AI extensions",
        "ext.install": "Install",
        "ext.launch": "Launch",
        "ext.stop": "Stop",
        "ext.close": "Close",

        # LM Studio Panel
        "lms.title": "LM Studio - Local Models",
        "lms.status": "Server Status:",
        "lms.running": "Connected & Running",
        "lms.not_running": "Not Running",
        "lms.refresh": "Refresh",
        "lms.use_for_chat": "Use for Chat",
        "lms.load": "Load Model",
        "lms.unload": "Unload Model",

        # API Setup Wizard
        "wizard.title": "Hermes Agent - API Setup Wizard",
        "wizard.back": "← Back",
        "wizard.next": "Next →",
        "wizard.skip": "Skip for now",
        "wizard.finish": "Finish & Start Chatting",
        "wizard.get_key": "Get Key",
        "wizard.save_key": "Save Key",

        # About Dialog
        "about.title": "About Portable Hermes Agent",
        "about.text": (
            "Portable Hermes Agent\n\n"
            "Hermes Agent core v{version}\n\n"
            "Portable Windows distribution by aivrar\n"
            "Built on Hermes Agent by Nous Research\n\n"
            "github.com/aivrar/portable-hermes-agent"
        ),
    },

    "zh-hant": {
        # App & Window
        "app.title": "便攜版 Hermes Agent",
        "app.exit_confirm": "Agent 仍在執行中，確定要結束嗎？",

        # Menu bar
        "menu.file": "檔案",
        "menu.view": "檢視",
        "menu.language": "語言",
        "menu.help": "說明",
        "menu.new_chat": "新對話",
        "menu.api_setup": "API 金鑰設定",
        "menu.permissions": "權限管理",
        "menu.settings": "設定",
        "menu.exit": "結束",
        "menu.lm_studio": "LM Studio (本地模型)",
        "menu.skills": "技能瀏覽器",
        "menu.extensions": "擴展模組",
        "menu.toggle_sidebar": "切換側邊欄",
        "menu.about": "關於",

        # Sidebar
        "sidebar.new_chat": "+ 新對話",
        "sidebar.model": "模型:",
        "sidebar.recent_sessions": "最近對話",
        "sidebar.no_sessions": "尚無對話紀錄",
        "sidebar.delete_title": "刪除對話",
        "sidebar.delete_confirm": "確定要刪除對話「{session_id}」嗎？\n\n此操作無法復原。",
        "sidebar.local_settings": "本地模型設定",
        "sidebar.gpu_offload": "GPU 卸載:",
        "sidebar.context_len": "上下文長度:",
        "sidebar.threads": "CPU 線程:",
        "sidebar.temp": "溫度:",
        "sidebar.loading_model": "正在載入模型...",
        "sidebar.model_loaded": "模型載入成功",
        "sidebar.load_failed": "載入失敗: {error}",

        # Chat Area
        "chat.new_chat_title": "新對話",
        "chat.attach": "📎 附件",
        "chat.attach_tooltip": "附加圖片 (Ctrl+Shift+I)",
        "chat.send": "發送",
        "chat.send_tooltip": "發送訊息 (Enter)",
        "chat.stop": "停止",
        "chat.stop_tooltip": "停止生成 (Escape)",
        "chat.copy_all": "複製全部",
        "chat.select_all": "全選",
        "chat.you": "你",
        "chat.hermes": "Hermes",
        "chat.tool": "工具: {name}",
        "chat.error": "錯誤",
        "chat.system": "系統",
        "chat.loading_image": "正在載入圖片...",
        "chat.welcome_configured": (
            "歡迎使用便攜版 Hermes Agent！\n"
            "在下方輸入訊息並按 Enter 即可交談。\n"
            "按 Shift+Enter 換行，按 Escape 中斷生成。"
        ),
        "chat.welcome_guided": (
            "歡迎使用便攜版 Hermes Agent！\n\n"
            "尚未連接 AI 模型，但沒關係！\n"
            "目前運行於引導模式 — 您可以向我詢問任何問題，我將在內建指南中搜尋解答。\n\n"
            "試著輸入：\n"
            "  • 如何開始使用？\n"
            "  • 什麼是 OpenRouter？\n"
            "  • 如何使用本地模型？\n"
            "  • Hermes 可以做什麼？\n\n"
            "或前往「檔案 > API 金鑰設定」連接 AI 模型。"
        ),
        "chat.lm_fallback": (
            "未偵測到 LM Studio。本地模型「{orig}」不可用。\n"
            "已改用 {model}。請啟動 LM Studio 並從下拉選單重新選擇本地模型以切換回來。"
        ),

        # Status Bar
        "status.ready": "就緒",
        "status.thinking": "思考中...",
        "status.running": "正在執行: {name}",
        "status.error": "錯誤",
        "status.step": "步驟 {n}",

        # Settings Dialog
        "settings.title": "設定",
        "settings.tab_general": "  一般設定  ",
        "settings.tab_api": "  API 金鑰  ",
        "settings.tab_model": "  模型設定  ",
        "settings.language": "介面語言",
        "settings.default_model": "預設模型",
        "settings.model_hint": "您可以輸入任何 OpenRouter 模型 ID",
        "settings.save": "儲存並關閉",

        # Skills Browser
        "skills.title": "技能瀏覽器",
        "skills.search": "搜尋技能...",
        "skills.installed": "已安裝",
        "skills.all": "全部",
        "skills.close": "關閉",

        # Permissions Panel
        "perms.title": "權限管理",
        "perms.subtitle": "控制 Hermes 在您電腦上被允許執行的操作",
        "perms.save": "儲存權限",
        "perms.cancel": "取消",
        "perms.reset": "恢復預設值",

        # Extensions
        "ext.title": "擴展管理器",
        "ext.subtitle": "安裝與管理便攜 AI 擴展模組",
        "ext.install": "安裝",
        "ext.launch": "啟動",
        "ext.stop": "停止",
        "ext.close": "關閉",

        # LM Studio Panel
        "lms.title": "LM Studio - 本地模型",
        "lms.status": "伺服器狀態:",
        "lms.running": "已連線並運行中",
        "lms.not_running": "未運行",
        "lms.refresh": "重新整理",
        "lms.use_for_chat": "用於對話",
        "lms.load": "載入模型",
        "lms.unload": "卸載模型",

        # API Setup Wizard
        "wizard.title": "Hermes Agent - API 設定精靈",
        "wizard.back": "← 上一步",
        "wizard.next": "下一步 →",
        "wizard.skip": "暫時略過",
        "wizard.finish": "完成並開始交談",
        "wizard.get_key": "取得金鑰",
        "wizard.save_key": "儲存金鑰",

        # About Dialog
        "about.title": "關於便攜版 Hermes Agent",
        "about.text": (
            "便攜版 Hermes Agent\n\n"
            "Hermes Agent 核心版本 v{version}\n\n"
            "Windows 便攜發行版 由 aivrar 維護\n"
            "基於 Nous Research 的 Hermes Agent 開發\n\n"
            "github.com/aivrar/portable-hermes-agent"
        ),
    },

    "zh": {
        # App & Window
        "app.title": "便携版 Hermes Agent",
        "app.exit_confirm": "Agent 仍在运行中，确定要退出吗？",

        # Menu bar
        "menu.file": "文件",
        "menu.view": "视图",
        "menu.language": "语言",
        "menu.help": "帮助",
        "menu.new_chat": "新建对话",
        "menu.api_setup": "API 密钥设置",
        "menu.permissions": "权限管理",
        "menu.settings": "设置",
        "menu.exit": "退出",
        "menu.lm_studio": "LM Studio (本地模型)",
        "menu.skills": "技能浏览器",
        "menu.extensions": "扩展模块",
        "menu.toggle_sidebar": "切换侧边栏",
        "menu.about": "关于",

        # Sidebar
        "sidebar.new_chat": "+ 新建对话",
        "sidebar.model": "模型:",
        "sidebar.recent_sessions": "最近对话",
        "sidebar.no_sessions": "暂无对话记录",
        "sidebar.delete_title": "删除对话",
        "sidebar.delete_confirm": "确定要删除对话「{session_id}」吗？\n\n此操作无法撤销。",
        "sidebar.local_settings": "本地模型设置",
        "sidebar.gpu_offload": "GPU 卸载:",
        "sidebar.context_len": "上下文长度:",
        "sidebar.threads": "CPU 线程:",
        "sidebar.temp": "温度:",
        "sidebar.loading_model": "正在加载模型...",
        "sidebar.model_loaded": "模型加载成功",
        "sidebar.load_failed": "加载失败: {error}",

        # Chat Area
        "chat.new_chat_title": "新建对话",
        "chat.attach": "📎 附件",
        "chat.attach_tooltip": "附加图片 (Ctrl+Shift+I)",
        "chat.send": "发送",
        "chat.send_tooltip": "发送消息 (Enter)",
        "chat.stop": "停止",
        "chat.stop_tooltip": "停止生成 (Escape)",
        "chat.copy_all": "复制全部",
        "chat.select_all": "全选",
        "chat.you": "你",
        "chat.hermes": "Hermes",
        "chat.tool": "工具: {name}",
        "chat.error": "错误",
        "chat.system": "系统",
        "chat.loading_image": "正在加载图片...",
        "chat.welcome_configured": (
            "欢迎使用便携版 Hermes Agent！\n"
            "在下方输入消息并按 Enter 即可交谈。\n"
            "按 Shift+Enter 换行，按 Escape 中断生成。"
        ),
        "chat.welcome_guided": (
            "欢迎使用便携版 Hermes Agent！\n\n"
            "尚未连接 AI 模型，但没关系！\n"
            "当前运行于引导模式 — 您可以向我询问任何问题，我将在内置指南中搜索解答。\n\n"
            "尝试输入：\n"
            "  • 如何开始使用？\n"
            "  • 什么是 OpenRouter？\n"
            "  • 如何使用本地模型？\n"
            "  • Hermes 可以做什么？\n\n"
            "或前往「文件 > API 密钥设置」连接 AI 模型。"
        ),
        "chat.lm_fallback": (
            "未检测到 LM Studio。本地模型「{orig}」不可用。\n"
            "已改用 {model}。请启动 LM Studio 并从下拉菜单重新选择本地模型以切换回来。"
        ),

        # Status Bar
        "status.ready": "就绪",
        "status.thinking": "思考中...",
        "status.running": "正在运行: {name}",
        "status.error": "错误",
        "status.step": "步骤 {n}",

        # Settings Dialog
        "settings.title": "设置",
        "settings.tab_general": "  通用设置  ",
        "settings.tab_api": "  API 密钥  ",
        "settings.tab_model": "  模型设置  ",
        "settings.language": "界面语言",
        "settings.default_model": "默认模型",
        "settings.model_hint": "您可以输入任何 OpenRouter 模型 ID",
        "settings.save": "保存并关闭",

        # Skills Browser
        "skills.title": "技能浏览器",
        "skills.search": "搜索技能...",
        "skills.installed": "已安装",
        "skills.all": "全部",
        "skills.close": "关闭",

        # Permissions Panel
        "perms.title": "权限管理",
        "perms.subtitle": "控制 Hermes 在您电脑上被允许执行的操作",
        "perms.save": "保存权限",
        "perms.cancel": "取消",
        "perms.reset": "恢复默认值",

        # Extensions
        "ext.title": "扩展管理器",
        "ext.subtitle": "安装与管理便携 AI 扩展模块",
        "ext.install": "安装",
        "ext.launch": "启动",
        "ext.stop": "停止",
        "ext.close": "关闭",

        # LM Studio Panel
        "lms.title": "LM Studio - 本地模型",
        "lms.status": "服务器状态:",
        "lms.running": "已连接并运行中",
        "lms.not_running": "未运行",
        "lms.refresh": "刷新",
        "lms.use_for_chat": "用于对话",
        "lms.load": "加载模型",
        "lms.unload": "卸载模型",

        # API Setup Wizard
        "wizard.title": "Hermes Agent - API 设置向导",
        "wizard.back": "← 上一步",
        "wizard.next": "下一步 →",
        "wizard.skip": "暂时跳过",
        "wizard.finish": "完成并开始交谈",
        "wizard.get_key": "获取密钥",
        "wizard.save_key": "保存密钥",

        # About Dialog
        "about.title": "关于便携版 Hermes Agent",
        "about.text": (
            "便携版 Hermes Agent\n\n"
            "Hermes Agent 核心版本 v{version}\n\n"
            "Windows 便携发行版 由 aivrar 维护\n"
            "基于 Nous Research 的 Hermes Agent 开发\n\n"
            "github.com/aivrar/portable-hermes-agent"
        ),
    },
}

_current_language: Optional[str] = None
_listeners: List[Callable[[str], None]] = []


def _detect_system_language() -> str:
    """Detect default language based on system locale."""
    try:
        loc = locale.getdefaultlocale()[0] or ""
        loc = loc.lower().replace("-", "_")
        if "tw" in loc or "hk" in loc or "mo" in loc or "hant" in loc:
            return "zh-hant"
        if "zh" in loc or "cn" in loc or "sg" in loc or "hans" in loc:
            return "zh"
    except Exception:
        pass
    return DEFAULT_LANGUAGE


def get_language() -> str:
    """Return current language code ('zh-hant', 'zh', 'en')."""
    global _current_language
    if _current_language:
        return _current_language

    # 1. Environment variable
    env_lang = os.environ.get("HERMES_LANGUAGE", "").strip().lower()
    if env_lang in LANGUAGE_CODES:
        _current_language = env_lang
        return _current_language
    elif env_lang in ("zh_tw", "zh-tw", "zh-hk", "traditional-chinese", "traditional_chinese"):
        _current_language = "zh-hant"
        return _current_language
    elif env_lang in ("zh_cn", "zh-cn", "chinese", "simplified-chinese"):
        _current_language = "zh"
        return _current_language

    # 2. Config file ~/.hermes/config.yaml
    try:
        from hermes_cli.config import load_config_readonly
        cfg = load_config_readonly()
        cfg_lang = (cfg.get("display") or {}).get("language", "").strip().lower()
        if cfg_lang in LANGUAGE_CODES:
            _current_language = cfg_lang
            return _current_language
        elif cfg_lang in ("zh_tw", "zh-tw", "zh-hk", "traditional-chinese", "traditional_chinese"):
            _current_language = "zh-hant"
            return _current_language
        elif cfg_lang in ("zh_cn", "zh-cn", "chinese", "simplified-chinese"):
            _current_language = "zh"
            return _current_language
    except Exception:
        pass

    # 3. System locale
    _current_language = _detect_system_language()
    return _current_language


def set_language(lang: str, persist: bool = True) -> None:
    """Switch active language, persist to config, and notify all listeners."""
    global _current_language

    # Normalize
    lang_clean = lang.strip().lower()
    if lang_clean in ("zh-tw", "zh_tw", "zh-hk", "traditional-chinese", "traditional_chinese"):
        lang_clean = "zh-hant"
    elif lang_clean in ("zh-cn", "zh_cn", "chinese", "simplified-chinese"):
        lang_clean = "zh"
    elif lang_clean not in LANGUAGE_CODES:
        lang_clean = DEFAULT_LANGUAGE

    _current_language = lang_clean
    os.environ["HERMES_LANGUAGE"] = lang_clean

    # Reset agent core i18n cache if available
    try:
        from agent import i18n
        i18n.reset_language_cache()
    except Exception:
        pass

    # Persist to ~/.hermes/config.yaml
    if persist:
        try:
            from hermes_cli.config import load_config, save_config
            cfg = load_config()
            if "display" not in cfg or not isinstance(cfg["display"], dict):
                cfg["display"] = {}
            cfg["display"]["language"] = lang_clean
            save_config(cfg)
        except Exception as exc:
            logger.warning("Could not persist language to config: %s", exc)

    # Notify listeners
    for callback in list(_listeners):
        try:
            callback(lang_clean)
        except Exception as exc:
            logger.exception("Error in language listener callback: %s", exc)


def register_listener(callback: Callable[[str], None]) -> None:
    """Register a callback that is called when language changes: callback(new_lang)."""
    if callback not in _listeners:
        _listeners.append(callback)


def unregister_listener(callback: Callable[[str], None]) -> None:
    """Unregister a language change callback."""
    if callback in _listeners:
        _listeners.remove(callback)


def t(key: str, default: Optional[str] = None, **format_kwargs: Any) -> str:
    """
    Translate key to active language.
    Falls back to English, then default, then key.
    """
    lang = get_language()
    val = TRANSLATIONS.get(lang, {}).get(key)
    if val is None and lang != "en":
        val = TRANSLATIONS.get("en", {}).get(key)
    if val is None:
        val = default if default is not None else key

    if format_kwargs:
        try:
            return val.format(**format_kwargs)
        except Exception:
            return val
    return val
