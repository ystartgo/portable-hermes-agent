"""
Hermes Agent - Windows Desktop GUI
Styled to match ImageBuddy/ImageDownloader visual design.
Pure tkinter + ttk, dark theme, flat design.
"""
import os
import sys
import re
import io
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import webbrowser
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

try:
    from PIL import Image, ImageTk
    import httpx
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gui.theme import C, FONTS, apply_theme, set_dark_title_bar, Tooltip, center_window, init_dpi_scaling, S, SF
from gui.agent_bridge import AgentBridge
from gui.api_setup_wizard import APISetupWizard, get_missing_keys
from gui.extensions import ExtensionsManager
from gui.lm_studio import LMStudioPanel
from gui.permissions_panel import PermissionsPanel
from gui.permissions import load_permissions, get_permissions_summary
from hermes_constants import get_hermes_home
from hermes_cli import __version__ as HERMES_CORE_VERSION
from gui.i18n import t, get_language, set_language, SUPPORTED_LANGUAGES, register_listener


# ============================================================================
# Chat Message Widgets
# ============================================================================

class MessageBubble(tk.Frame):
    """A single chat message."""

    def __init__(self, parent, text, msg_type="user", tool_name=None):
        super().__init__(parent, bg=C["bg_main"])

        if msg_type == "user":
            bg, border, label, label_fg = C["msg_user"], C["msg_user_border"], t("chat.you", "You"), C["accent"]
        elif msg_type == "ai":
            bg, border, label, label_fg = C["msg_ai"], C["msg_ai_border"], t("chat.hermes", "Hermes"), C["success"]
        elif msg_type == "tool":
            bg, border = C["msg_tool"], C["msg_tool_border"]
            label, label_fg = t("chat.tool", "Tool: {name}", name=tool_name or '?'), C["warning_dark"]
        elif msg_type == "error":
            bg, border, label, label_fg = C["msg_error"], C["msg_error_border"], t("chat.error", "Error"), C["danger"]
        else:  # system
            bg, border, label, label_fg = C["msg_system"], C["msg_system_border"], t("chat.system", "System"), C["text_hint"]

        # Outer padding
        pad = tk.Frame(self, bg=C["bg_main"])
        pad.pack(fill="x", padx=16, pady=3)

        # Card
        card = tk.Frame(pad, bg=bg, highlightbackground=border,
                       highlightthickness=1, padx=12, pady=8)
        if msg_type == "user":
            card.pack(side="right", anchor="e")
        else:
            card.pack(side="left", anchor="w", fill="x", expand=True)

        # Header row
        hdr = tk.Frame(card, bg=bg)
        hdr.pack(fill="x")

        tk.Label(hdr, text=label, font=FONTS["small"] + ("bold",),
                fg=label_fg, bg=bg).pack(side="left")

        ts = datetime.now().strftime("%H:%M")
        tk.Label(hdr, text=ts, font=SF("Segoe UI", 8),
                fg=C["text_disabled"], bg=bg).pack(side="right")

        # Check for markdown images: ![alt](url)
        self._images = []  # Keep references so GC doesn't kill them
        image_pattern = r'!\[([^\]]*)\]\((https?://[^\)]+)\)'
        image_matches = list(re.finditer(image_pattern, text))

        # Strip image markdown from text for display
        display_text = re.sub(image_pattern, '', text).strip()

        # Message body (text part)
        if display_text:
            body = tk.Text(card, wrap="word", bg=bg, fg=C["text_primary"],
                          font=FONTS["body"], relief="flat", borderwidth=0,
                          padx=0, pady=2, cursor="arrow",
                          selectbackground=C["accent"], selectforeground="white",
                          highlightthickness=0)
            body.insert("1.0", display_text)
            body.configure(state="disabled")

            lines = max(1, display_text.count('\n') + 1)
            for line in display_text.split('\n'):
                lines += max(0, len(line) // 70)
            body.configure(height=min(lines, 25))
            body.pack(fill="x")

            body.bind("<Button-3>", lambda e: self._ctx_menu(e, body))

        # Render images inline
        if HAS_PIL and image_matches:
            for match in image_matches:
                alt_text = match.group(1)
                url = match.group(2)
                img_frame = tk.Frame(card, bg=bg)
                img_frame.pack(fill="x", pady=(6, 2))

                # Loading label (replaced by image when downloaded)
                loading = tk.Label(img_frame, text=t("chat.loading_image", "Loading image..."),
                                  font=FONTS["small"], fg=C["text_hint"], bg=bg)
                loading.pack()

                # Download and display in background
                threading.Thread(target=self._load_image,
                               args=(img_frame, loading, url, alt_text, bg),
                               daemon=True).start()
        elif image_matches and not HAS_PIL:
            # Fallback: show clickable link
            for match in image_matches:
                url = match.group(2)
                link = tk.Label(card, text=f"[Image: {url}]",
                               font=FONTS["small"], fg=C["accent"], bg=bg,
                               cursor="hand2")
                link.pack(fill="x", pady=(4, 0))
                link.bind("<Button-1>", lambda e, u=url: __import__('webbrowser').open(u))

    def _ctx_menu(self, event, tw):
        menu = tk.Menu(self, tearoff=0,
                      bg=C["bg_card"], fg=C["text_primary"],
                      activebackground=C["accent"], activeforeground="white")
        menu.add_command(label=t("chat.copy_all", "Copy All"), command=lambda: self._copy(tw))
        menu.add_command(label=t("chat.select_all", "Select All"), command=lambda: self._select_all(tw))
        menu.post(event.x_root, event.y_root)

    def _copy(self, tw):
        tw.configure(state="normal")
        txt = tw.get("1.0", "end-1c")
        tw.configure(state="disabled")
        self.clipboard_clear()
        self.clipboard_append(txt)

    def _select_all(self, tw):
        tw.configure(state="normal")
        tw.tag_add("sel", "1.0", "end-1c")
        tw.configure(state="disabled")

    def _load_image(self, frame, loading_label, url, alt_text, bg):
        """Download image from URL and display it inline."""
        try:
            resp = httpx.get(url, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            img_data = resp.content

            img = Image.open(io.BytesIO(img_data))

            # Resize to fit chat area (max 400px wide, maintain aspect ratio)
            max_w = 400
            if img.width > max_w:
                ratio = max_w / img.width
                img = img.resize((max_w, int(img.height * ratio)), Image.LANCZOS)

            # Convert to tkinter-compatible image
            tk_img = ImageTk.PhotoImage(img)

            # Must update GUI from main thread
            def _show():
                try:
                    loading_label.destroy()
                    img_label = tk.Label(frame, image=tk_img, bg=bg, cursor="hand2")
                    img_label.pack()
                    # Keep reference so GC doesn't destroy it
                    self._images.append(tk_img)
                    # Click to open full size in browser
                    img_label.bind("<Button-1>",
                                  lambda e: __import__('webbrowser').open(url))
                    # Tooltip
                    from gui.theme import Tooltip
                    Tooltip(img_label, f"Click to open full size\n{alt_text}")
                except tk.TclError:
                    pass

            frame.after(0, _show)

        except Exception as e:
            def _show_error():
                try:
                    loading_label.configure(text=f"Could not load image: {e}",
                                           fg=C["danger"])
                except tk.TclError:
                    pass
            frame.after(0, _show_error)


class ToolCallWidget(tk.Frame):
    """Compact expandable tool-call indicator."""

    def __init__(self, parent, tool_name, args_preview):
        super().__init__(parent, bg=C["bg_main"])
        self.tool_name = tool_name
        self.args_preview = str(args_preview or "")
        self._expanded = False

        pad = tk.Frame(self, bg=C["bg_main"])
        pad.pack(fill="x", padx=16, pady=2)

        self.card = tk.Frame(pad, bg=C["msg_tool"], highlightbackground=C["msg_tool_border"],
                             highlightthickness=1, padx=8, pady=4, cursor="hand2")
        self.card.pack(side="left", fill="x", expand=True)

        row = tk.Frame(self.card, bg=C["msg_tool"], cursor="hand2")
        row.pack(fill="x")

        self.arrow_lbl = tk.Label(row, text="\u25B6", font=SF("Segoe UI", 8),
                                  fg=C["warning_dark"], bg=C["msg_tool"])
        self.arrow_lbl.pack(side="left", padx=(0, 6))

        tk.Label(row, text=tool_name, font=FONTS["mono_small"] + ("bold",),
                 fg=C["accent"], bg=C["msg_tool"]).pack(side="left")

        self.toggle_btn = tk.Label(row, text=t("chat.tool_expand", "Details \u25bc"),
                                   font=SF("Segoe UI", 8), fg=C["text_hint"],
                                   bg=C["msg_tool"], cursor="hand2")
        self.toggle_btn.pack(side="right", padx=(4, 0))

        # Compact preview
        self.preview_lbl = None
        if self.args_preview:
            preview = self.args_preview[:90].replace("\n", " ")
            if len(self.args_preview) > 90:
                preview += "..."
            self.preview_lbl = tk.Label(self.card, text=preview, font=FONTS["mono_small"],
                                        fg=C["text_hint"], bg=C["msg_tool"],
                                        wraplength=S(600), justify="left", anchor="w", cursor="hand2")
            self.preview_lbl.pack(fill="x", pady=(2, 0))

        # Expanded details frame (initially hidden)
        self.details_frame = tk.Frame(self.card, bg=C["bg_input"], padx=6, pady=4)
        detail_header = tk.Label(self.details_frame, text=t("chat.tool_args", "Arguments / Parameters:"),
                                 font=SF("Segoe UI", 8, "bold"), fg=C["accent"], bg=C["bg_input"], anchor="w")
        detail_header.pack(fill="x", pady=(0, 2))

        self.detail_text = tk.Text(self.details_frame, wrap="word", bg=C["bg_input"],
                                   fg=C["text_primary"], font=FONTS["mono_small"],
                                   relief="flat", borderwidth=0, highlightthickness=0,
                                   padx=2, pady=2, cursor="arrow")
        self.detail_text.insert("1.0", self.args_preview)
        self.detail_text.configure(state="disabled")
        lines = max(2, min(14, self.args_preview.count('\n') + max(1, len(self.args_preview) // 60)))
        self.detail_text.configure(height=lines)
        self.detail_text.pack(fill="x")

        # Bind clicks to toggle expansion
        for w in (self.card, row, self.arrow_lbl, self.toggle_btn):
            w.bind("<Button-1>", lambda e: self.toggle())
        if self.preview_lbl:
            self.preview_lbl.bind("<Button-1>", lambda e: self.toggle())

    def toggle(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.arrow_lbl.configure(text="\u25BC")
            self.toggle_btn.configure(text=t("chat.tool_collapse", "Collapse \u25b2"))
            if self.preview_lbl:
                self.preview_lbl.pack_forget()
            self.details_frame.pack(fill="x", pady=(4, 2))
        else:
            self.arrow_lbl.configure(text="\u25B6")
            self.toggle_btn.configure(text=t("chat.tool_expand", "Details \u25bc"))
            self.details_frame.pack_forget()
            if self.preview_lbl:
                self.preview_lbl.pack(fill="x", pady=(2, 0))


class ThinkingBubble(tk.Frame):
    """Collapsible card displaying the model's thinking / reasoning process."""

    def __init__(self, parent):
        super().__init__(parent, bg=C["bg_main"])
        self._full_text = ""
        self._expanded = True
        self._finalized = False

        pad = tk.Frame(self, bg=C["bg_main"])
        pad.pack(fill="x", padx=16, pady=2)

        self.card = tk.Frame(pad, bg=C["bg_card"],
                             highlightbackground=C["border"],
                             highlightthickness=1, padx=8, pady=4)
        self.card.pack(side="left", fill="x", expand=True)

        # Header row
        hdr = tk.Frame(self.card, bg=C["bg_card"], cursor="hand2")
        hdr.pack(fill="x")

        tk.Label(hdr, text="\U0001f9e0", font=SF("Segoe UI", 10),
                 fg=C["accent"], bg=C["bg_card"]).pack(side="left", padx=(0, 6))

        self.title_lbl = tk.Label(hdr, text=t("chat.thinking_process", "Thinking Process"),
                                  font=FONTS["small"] + ("bold",),
                                  fg=C["text_secondary"], bg=C["bg_card"])
        self.title_lbl.pack(side="left")

        self.status_lbl = tk.Label(hdr, text=f"({t('chat.thinking_active', 'Thinking...')})",
                                   font=SF("Segoe UI", 8),
                                   fg=C["info"], bg=C["bg_card"])
        self.status_lbl.pack(side="left", padx=(6, 0))

        self.toggle_btn = tk.Label(hdr, text=t("chat.thinking_collapse", "Collapse \u25b2"),
                                   font=SF("Segoe UI", 8), fg=C["accent"],
                                   bg=C["bg_card"], cursor="hand2")
        self.toggle_btn.pack(side="right")

        # Body text area
        self.body_frame = tk.Frame(self.card, bg=C["bg_card"], padx=4, pady=2)
        self.body_frame.pack(fill="x", pady=(4, 0))

        self.body = tk.Text(self.body_frame, wrap="word", bg=C["bg_card"],
                            fg=C["text_disabled"], font=FONTS["mono_small"],
                            relief="flat", borderwidth=0,
                            padx=4, pady=2, cursor="arrow",
                            highlightthickness=0, height=1)
        self.body.pack(fill="x")

        # Bind toggle
        for w in (hdr, self.title_lbl, self.status_lbl, self.toggle_btn):
            w.bind("<Button-1>", lambda e: self.toggle())

    def append_reasoning(self, text: str):
        if not text:
            return
        self._full_text += text
        self.body.insert("end", text)
        content = self.body.get("1.0", "end-1c")
        lines = max(1, content.count('\n') + 1)
        for line in content.split('\n'):
            lines += max(0, len(line) // 70)
        self.body.configure(height=min(lines, 12))
        self.body.see("end")

    def finalize(self):
        if self._finalized:
            return
        self._finalized = True
        try:
            self.body.configure(state="disabled")
            count = len(self._full_text.strip())
            self.status_lbl.configure(
                text=t("chat.thinking_finished", "Thinking finished ({count} chars)", count=count),
                fg=C["text_hint"]
            )
        except Exception:
            pass

    def toggle(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.toggle_btn.configure(text=t("chat.thinking_collapse", "Collapse \u25b2"))
            self.body_frame.pack(fill="x", pady=(4, 0))
        else:
            self.toggle_btn.configure(text=t("chat.thinking_expand", "Expand \u25bc"))
            self.body_frame.pack_forget()

    def get_text(self) -> str:
        return self._full_text


class StreamingBubble(tk.Frame):
    """A chat bubble that streams text token-by-token."""

    def __init__(self, parent):
        super().__init__(parent, bg=C["bg_main"])
        self._full_text = ""
        self._bg = C["msg_ai"]

        pad = tk.Frame(self, bg=C["bg_main"])
        pad.pack(fill="x", padx=16, pady=3)

        self._card = tk.Frame(pad, bg=self._bg,
                             highlightbackground=C["msg_ai_border"],
                             highlightthickness=1, padx=10, pady=4)
        self._card.pack(side="left", anchor="w", fill="x", expand=True)

        # Header — tight single row
        hdr = tk.Frame(self._card, bg=self._bg)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Hermes", font=FONTS["small"] + ("bold",),
                fg=C["success"], bg=self._bg, pady=0).pack(side="left")
        ts = datetime.now().strftime("%H:%M")
        tk.Label(hdr, text=ts, font=SF("Segoe UI", 8),
                fg=C["text_disabled"], bg=self._bg, pady=0).pack(side="right")

        # Body text widget — stays editable (normal) during streaming
        self._body = tk.Text(self._card, wrap="word", bg=self._bg,
                            fg=C["text_primary"], font=FONTS["body"],
                            relief="flat", borderwidth=0,
                            padx=0, pady=0, cursor="arrow",
                            selectbackground=C["accent"],
                            selectforeground="white",
                            highlightthickness=0, height=1,
                            spacing1=0, spacing2=0, spacing3=0)
        self._body.pack(fill="x")

        # Blinking cursor — separate label so it can't corrupt text
        self._cursor_lbl = tk.Label(self._card, text="\u258c",
                                    font=FONTS["body"], fg=C["info"],
                                    bg=self._bg, pady=0)
        self._cursor_lbl.pack(anchor="w")
        self._cursor_on = True
        self._blink()

    def append_text(self, text: str):
        """Append a text delta to the streaming bubble."""
        if text is None:
            return
        self._full_text += text
        self._body.insert("end", text)
        # Auto-resize height based on content
        content = self._body.get("1.0", "end-1c")
        lines = max(1, content.count('\n') + 1)
        for line in content.split('\n'):
            lines += max(0, len(line) // 70)
        self._body.configure(height=min(lines, 30))

    def get_text(self) -> str:
        return self._full_text

    def finalize(self):
        """Stop cursor blink, lock the text, remove cursor."""
        self._cursor_on = False
        try:
            self._cursor_lbl.destroy()
        except tk.TclError:
            pass
        self._body.configure(state="disabled")

    def _blink(self):
        if not self._cursor_on:
            return
        try:
            cur = self._cursor_lbl.cget("fg")
            self._cursor_lbl.configure(
                fg=self._bg if cur != self._bg else C["info"])
            self.after(500, self._blink)
        except tk.TclError:
            pass


def get_custom_models() -> List[str]:
    """Load user-defined custom model IDs."""
    path = get_hermes_home() / "custom_models.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [str(m).strip() for m in data if str(m).strip()]
        except Exception:
            pass
    return []


def add_custom_model(model_id: str) -> bool:
    """Add a custom model ID and persist it."""
    model_id = model_id.strip()
    if not model_id:
        return False
    models = get_custom_models()
    if model_id not in models:
        models.append(model_id)
        path = get_hermes_home() / "custom_models.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(json.dumps(models, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except Exception:
            pass
    return False


def remove_custom_model(model_id: str) -> bool:
    """Remove a custom model ID and persist it."""
    model_id = model_id.strip()
    models = get_custom_models()
    if model_id in models:
        models.remove(model_id)
        path = get_hermes_home() / "custom_models.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(json.dumps(models, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except Exception:
            pass
    return False


def update_custom_model(old_id: str, new_id: str) -> bool:
    """Update a custom model ID."""
    old_id = old_id.strip()
    new_id = new_id.strip()
    if not new_id or old_id == new_id:
        return False
    models = get_custom_models()
    if old_id in models:
        idx = models.index(old_id)
        models[idx] = new_id
        path = get_hermes_home() / "custom_models.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(json.dumps(models, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except Exception:
            pass
    return False


# ============================================================================
# Custom API Endpoints Manager
# ============================================================================

def get_custom_endpoints() -> List[Dict[str, Any]]:
    """Load user-defined custom API endpoints."""
    path = get_hermes_home() / "custom_endpoints.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list) and len(data) > 0:
                return data
        except Exception:
            pass
    initial = []
    tt_key = os.getenv("TOKENTABLE_API_KEY", "")
    if tt_key:
        initial.append({
            "id": "tokentable",
            "name": "TokenTable",
            "base_url": "https://tokentable.asia/v1",
            "api_key": tt_key,
            "model": "auto"
        })
    custom_base = os.getenv("CUSTOM_BASE_URL", "") or os.getenv("OPENAI_BASE_URL", "")
    custom_key = os.getenv("CUSTOM_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    if custom_base and custom_base != "https://tokentable.asia/v1":
        initial.append({
            "id": "custom_default",
            "name": "Custom Endpoint",
            "base_url": custom_base,
            "api_key": custom_key,
            "model": "auto"
        })
    return initial


def save_custom_endpoints(endpoints: List[Dict[str, Any]]) -> bool:
    """Save user-defined custom API endpoints."""
    path = get_hermes_home() / "custom_endpoints.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(endpoints, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def add_custom_endpoint(name: str, base_url: str, api_key: str, model: str = "auto") -> Dict[str, Any]:
    endpoints = get_custom_endpoints()
    ep_id = f"ep_{uuid.uuid4().hex[:8]}"
    item = {
        "id": ep_id,
        "name": name.strip() or "Custom Endpoint",
        "base_url": base_url.strip().rstrip("/"),
        "api_key": api_key.strip(),
        "model": model.strip() or "auto"
    }
    for i, ep in enumerate(endpoints):
        if ep.get("name", "").lower() == item["name"].lower():
            item["id"] = ep.get("id", ep_id)
            endpoints[i] = item
            save_custom_endpoints(endpoints)
            return item
    endpoints.append(item)
    save_custom_endpoints(endpoints)
    return item


def delete_custom_endpoint(endpoint_id: str) -> bool:
    endpoints = get_custom_endpoints()
    new_eps = [ep for ep in endpoints if ep.get("id") != endpoint_id]
    if len(new_eps) != len(endpoints):
        save_custom_endpoints(new_eps)
        return True
    return False


def activate_custom_endpoint(endpoint: Dict[str, Any]) -> bool:
    """Activate an endpoint: sets in os.environ and persists to .env."""
    base_url = endpoint.get("base_url", "").strip().rstrip("/")
    api_key = endpoint.get("api_key", "").strip()
    model = endpoint.get("model", "").strip() or "auto"
    name = endpoint.get("name", "")

    if not base_url:
        return False

    os.environ["OPENAI_BASE_URL"] = base_url
    os.environ["CUSTOM_BASE_URL"] = base_url
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["CUSTOM_API_KEY"] = api_key
    os.environ["ACTIVE_CUSTOM_ENDPOINT_ID"] = endpoint.get("id", "")

    from gui.api_setup_wizard import _save_key_to_env
    _save_key_to_env("OPENAI_BASE_URL", base_url)
    _save_key_to_env("CUSTOM_BASE_URL", base_url)
    _save_key_to_env("OPENAI_API_KEY", api_key)
    _save_key_to_env("CUSTOM_API_KEY", api_key)
    _save_key_to_env("ACTIVE_CUSTOM_ENDPOINT_ID", endpoint.get("id", ""))
    if name.lower() == "tokentable":
        os.environ["TOKENTABLE_API_KEY"] = api_key
        _save_key_to_env("TOKENTABLE_API_KEY", api_key)

    if model:
        add_custom_model(model)

    return True


# ============================================================================
# Sidebar
# ============================================================================

class Sidebar(tk.Frame):
    """Left sidebar with branding, new-chat, session history, and model switcher."""

    BASE_MODELS = [
        ("auto", "Auto", "TokenTable / Default routing"),
        ("google/gemini-2.5-flash", "Gemini Flash", "Fast & cheap"),
        ("google/gemini-2.5-pro", "Gemini Pro", "Smart & affordable"),
        ("anthropic/claude-sonnet-4", "Claude Sonnet", "Great all-rounder"),
        ("anthropic/claude-opus-4.6", "Claude Opus", "Most capable"),
        ("openai/gpt-4o", "GPT-4o", "OpenAI flagship"),
        ("openai/gpt-4o-mini", "GPT-4o Mini", "Fast & cheap"),
        ("deepseek/deepseek-chat-v3", "DeepSeek V3", "Strong & cheap"),
        ("meta-llama/llama-4-maverick", "Llama Maverick", "Open source"),
    ]
    MODELS = BASE_MODELS

    def _get_unified_models(self) -> List[tuple]:
        """Combine base models, custom user models, and local LM Studio models."""
        base_ids = {m[0] for m in self.BASE_MODELS}
        customs = []
        for mid in get_custom_models():
            if mid not in base_ids:
                customs.append((mid, mid, "Custom"))
        return list(self.BASE_MODELS) + customs + list(self._lm_studio_models)

    def __init__(self, parent, on_new=None, on_model_change=None,
                 on_session_select=None, on_local_models=None,
                 on_auto_load=None, **kw):
        super().__init__(parent, bg=C["bg_sidebar"], width=S(260), **kw)
        self.pack_propagate(False)
        self.on_new = on_new
        self.on_model_change = on_model_change
        self.on_session_select = on_session_select
        self.on_local_models = on_local_models  # callback(list_of_model_ids)
        self.on_auto_load = on_auto_load  # callback(model_id, gpu, ctx, settings)
        self._confirm_delete = True  # Show confirmation dialog
        self._loading_model = False  # True while auto-loading

        # Unified model list: cloud + local + custom
        self._lm_studio_models: List[tuple] = []  # [(id, name, note), ...]
        self._all_models: List[tuple] = self._get_unified_models()
        self._model_states: Dict[str, str] = {}  # model_id -> "loaded"/"not-loaded"

        # -- Logo --
        logo_fr = tk.Frame(self, bg=C["bg_sidebar"], pady=12, padx=16)
        logo_fr.pack(fill="x")
        tk.Label(logo_fr, text="HERMES", font=FONTS["logo"],
                fg=C["accent"], bg=C["bg_sidebar"]).pack(anchor="w")
        tk.Label(logo_fr, text="AGENT", font=FONTS["logo_sub"],
                fg=C["text_secondary"], bg=C["bg_sidebar"]).pack(anchor="w")

        # -- New Chat button --
        btn_fr = tk.Frame(self, bg=C["bg_sidebar"], padx=16)
        btn_fr.pack(fill="x")
        self.new_btn = ttk.Button(btn_fr, text=t("sidebar.new_chat", "+ New Chat"), style="Primary.TButton",
                                  command=self._on_new)
        self.new_btn.pack(fill="x", pady=(0, 8))

        # -- Model Switcher --
        model_fr = tk.Frame(self, bg=C["bg_sidebar"], padx=16)
        model_fr.pack(fill="x")

        self.model_lbl = tk.Label(model_fr, text=t("sidebar.model", "Model:"), font=FONTS["small"],
                                  fg=C["text_hint"], bg=C["bg_sidebar"])
        self.model_lbl.pack(anchor="w")

        self.model_var = tk.StringVar(value="auto")
        display_values = [self._display_name(m) for m in self._all_models]
        display_values.append(t("sidebar.add_custom_model", "+ 自訂模型..."))
        display_values.append(t("sidebar.manage_models", "✎ 管理模型清單..."))
        self.model_combo = ttk.Combobox(model_fr, textvariable=tk.StringVar(),
                                        values=display_values,
                                        font=FONTS["small"], state="readonly")
        current_model = self.model_var.get()
        self._select_model_in_combo(current_model)

        self.model_combo.pack(fill="x", pady=(2, 4))
        self.model_combo.bind("<<ComboboxSelected>>", self._on_model_selected)
        self.model_combo.bind("<Button-1>", lambda e: self.refresh_models())

        # -- Loading status indicator (hidden by default) --
        self._load_status_var = tk.StringVar(value="")
        self._load_status_lbl = tk.Label(model_fr, textvariable=self._load_status_var,
                                         font=FONTS["small"], fg=C["warning"],
                                         bg=C["bg_sidebar"], anchor="w")
        # Don't pack yet — shown/hidden dynamically

        # -- Local Model Settings (collapsible) --
        self._local_settings_fr = tk.Frame(self, bg=C["bg_sidebar"], padx=16)
        # Don't pack yet — shown when a local model is selected
        self._build_local_settings(self._local_settings_fr)

        # Probe LM Studio models in background after startup
        self.after(1000, self.refresh_models)

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # -- Sessions header --
        self.sessions_lbl = tk.Label(self, text=t("sidebar.recent_sessions", "Recent Sessions"), font=FONTS["small"],
                                     fg=C["text_hint"], bg=C["bg_sidebar"], padx=16, pady=8,
                                     anchor="w")
        self.sessions_lbl.pack(fill="x")

        # -- Session list (scrollable) --
        self.session_canvas = tk.Canvas(self, bg=C["bg_sidebar"],
                                        highlightthickness=0, borderwidth=0)
        self.session_canvas.pack(fill="both", expand=True, padx=4)

        self.session_frame = tk.Frame(self.session_canvas, bg=C["bg_sidebar"])
        self.session_canvas.create_window((0, 0), window=self.session_frame, anchor="nw",
                                          tags="inner")
        self.session_frame.bind("<Configure>", lambda e: self.session_canvas.configure(
            scrollregion=self.session_canvas.bbox("all")))
        self.session_canvas.bind("<Configure>", lambda e: self.session_canvas.itemconfig(
            "inner", width=e.width))

        # Mouse wheel on session list
        def _sw(event):
            self.session_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.session_canvas.bind("<MouseWheel>", _sw)
        self.session_frame.bind("<MouseWheel>", _sw)

        # Load sessions on startup
        self.after(500, self._load_sessions)

    @staticmethod
    def _display_name(entry):
        """Build display string for a model tuple (id, name, note)."""
        _, name, note = entry
        return f"{name}  ({note})"

    def _select_model_in_combo(self, model_id):
        """Select model_id in the combobox, or show raw ID if not found."""
        for i, (mid, _, _) in enumerate(self._all_models):
            if mid == model_id:
                self.model_combo.current(i)
                return
        if model_id and model_id != t("sidebar.add_custom_model", "+ 自訂模型..."):
            self._all_models.append((model_id, model_id, "Custom"))
            display_values = [self._display_name(m) for m in self._all_models]
            display_values.append(t("sidebar.add_custom_model", "+ 自訂模型..."))
            display_values.append(t("sidebar.manage_models", "✎ 管理模型清單..."))
            self.model_combo["values"] = display_values
            self.model_combo.current(len(self._all_models) - 1)
            return
        self.model_combo.set(model_id)

    def set_model(self, name):
        self.model_var.set(name)
        self._select_model_in_combo(name)

    def _update_combobox_values(self):
        """Rebuild combobox values from _all_models (must be called on main thread)."""
        current = self.model_var.get()
        self._all_models = self._get_unified_models()
        display_values = [self._display_name(m) for m in self._all_models]
        display_values.append(t("sidebar.add_custom_model", "+ 自訂模型..."))
        display_values.append(t("sidebar.manage_models", "✎ 管理模型清單..."))
        self.model_combo["values"] = display_values
        self._select_model_in_combo(current)

    def refresh_model_list(self, selected=None):
        """Force refresh of model combobox including any newly added custom models."""
        self._update_combobox_values()
        if selected:
            self.set_model(selected)

    def _build_local_settings(self, parent):
        """Build the compact local model settings panel."""
        # Load persisted settings from env
        _hermes_home = get_hermes_home()

        # Header
        self.local_hdr_lbl = tk.Label(parent, text=t("sidebar.local_settings", "Local Model Settings"), font=FONTS["small"],
                                      fg=C["accent"], bg=C["bg_sidebar"])
        self.local_hdr_lbl.pack(anchor="w", pady=(4, 2))

        # GPU selector
        gpu_row = tk.Frame(parent, bg=C["bg_sidebar"])
        gpu_row.pack(fill="x", pady=2)
        self.gpu_lbl = tk.Label(gpu_row, text=t("sidebar.gpu_offload", "GPU:"), font=FONTS["small"],
                                fg=C["text_hint"], bg=C["bg_sidebar"], width=6, anchor="w")
        self.gpu_lbl.pack(side="left")
        self._gpu_var = tk.StringVar(value="")
        self._gpu_combo = ttk.Combobox(gpu_row, textvariable=self._gpu_var,
                                        font=FONTS["small"], state="readonly", width=22)
        self._gpu_combo.pack(side="left", fill="x", expand=True)
        self._gpu_combo.bind("<<ComboboxSelected>>", lambda e: self._save_local_settings())

        # Detect GPUs in background
        def _detect_gpus():
            try:
                from gui.lm_studio import get_available_gpus
                gpus = get_available_gpus()
            except Exception:
                gpus = ["CPU"]
            try:
                self.after(0, lambda: self._populate_gpus(gpus))
            except Exception:
                pass
        threading.Thread(target=_detect_gpus, daemon=True).start()

        # Context length
        ctx_row = tk.Frame(parent, bg=C["bg_sidebar"])
        ctx_row.pack(fill="x", pady=2)
        self.ctx_lbl = tk.Label(ctx_row, text=t("sidebar.context_len", "Ctx:"), font=FONTS["small"],
                                fg=C["text_hint"], bg=C["bg_sidebar"], width=6, anchor="w")
        self.ctx_lbl.pack(side="left")
        self._ctx_var = tk.IntVar(value=32768)
        ctx_spin = ttk.Spinbox(ctx_row, from_=32768, to=131072, increment=4096,
                               textvariable=self._ctx_var, font=FONTS["small"], width=8)
        ctx_spin.pack(side="left")
        ctx_spin.bind("<FocusOut>", lambda e: self._save_local_settings())
        ctx_spin.bind("<Return>", lambda e: self._save_local_settings())
        tk.Label(ctx_row, text="tokens", font=FONTS["small"],
                fg=C["text_disabled"], bg=C["bg_sidebar"]).pack(side="left", padx=(4, 0))

        # Temperature
        temp_row = tk.Frame(parent, bg=C["bg_sidebar"])
        temp_row.pack(fill="x", pady=2)
        self.temp_lbl = tk.Label(temp_row, text=t("sidebar.temp", "Temp:"), font=FONTS["small"],
                                 fg=C["text_hint"], bg=C["bg_sidebar"], width=6, anchor="w")
        self.temp_lbl.pack(side="left")
        self._temp_var = tk.DoubleVar(value=0.7)
        temp_spin = ttk.Spinbox(temp_row, from_=0.0, to=2.0, increment=0.1,
                                textvariable=self._temp_var, font=FONTS["small"], width=8,
                                format="%.1f")
        temp_spin.pack(side="left")
        temp_spin.bind("<FocusOut>", lambda e: self._save_local_settings())
        temp_spin.bind("<Return>", lambda e: self._save_local_settings())

        # Top-P
        topp_row = tk.Frame(parent, bg=C["bg_sidebar"])
        topp_row.pack(fill="x", pady=2)
        tk.Label(topp_row, text="Top-P:", font=FONTS["small"],
                fg=C["text_hint"], bg=C["bg_sidebar"], width=6, anchor="w").pack(side="left")
        self._topp_var = tk.DoubleVar(value=0.9)
        topp_spin = ttk.Spinbox(topp_row, from_=0.0, to=1.0, increment=0.05,
                                textvariable=self._topp_var, font=FONTS["small"], width=8,
                                format="%.2f")
        topp_spin.pack(side="left")
        topp_spin.bind("<FocusOut>", lambda e: self._save_local_settings())
        topp_spin.bind("<Return>", lambda e: self._save_local_settings())

        # Checkboxes row
        cb_fr = tk.Frame(parent, bg=C["bg_sidebar"])
        cb_fr.pack(fill="x", pady=(4, 4))

        self._auto_load_var = tk.BooleanVar(value=True)
        auto_cb = tk.Checkbutton(cb_fr, text="Auto-load",
                                 variable=self._auto_load_var,
                                 font=FONTS["small"], fg=C["text_hint"],
                                 bg=C["bg_sidebar"], selectcolor=C["bg_input"],
                                 activebackground=C["bg_sidebar"],
                                 activeforeground=C["text_primary"],
                                 command=self._save_local_settings)
        auto_cb.pack(side="left")

        self._flash_attn_var = tk.BooleanVar(value=True)
        flash_cb = tk.Checkbutton(cb_fr, text="Flash Attn",
                                  variable=self._flash_attn_var,
                                  font=FONTS["small"], fg=C["text_hint"],
                                  bg=C["bg_sidebar"], selectcolor=C["bg_input"],
                                  activebackground=C["bg_sidebar"],
                                  activeforeground=C["text_primary"],
                                  command=self._save_local_settings)
        flash_cb.pack(side="left", padx=(8, 0))

    def _populate_gpus(self, gpus):
        """Populate GPU combobox (called on main thread)."""
        self._gpu_combo["values"] = gpus
        saved = self._gpu_var.get()
        if saved and saved in gpus:
            self._gpu_combo.set(saved)
        elif len(gpus) > 1:
            # Default to first real GPU
            self._gpu_combo.current(1)
            self._gpu_var.set(gpus[1])
        elif gpus:
            self._gpu_combo.current(0)
        # Persist the selection so bridge can read it
        self._save_local_settings()

    def _save_local_settings(self):
        """Settings are held in UI widgets — nothing to persist."""
        pass

    def _get_gpu_index(self) -> Optional[int]:
        """Parse GPU index from the GPU combobox selection."""
        val = self._gpu_var.get()
        if val and val.startswith("GPU "):
            try:
                return int(val.split(":")[0].replace("GPU ", ""))
            except (ValueError, IndexError):
                pass
        return None

    def get_local_settings(self) -> dict:
        """Return current local model settings."""
        return {
            "gpu_index": self._get_gpu_index(),
            "context_length": self._ctx_var.get(),
            "temperature": self._temp_var.get(),
            "top_p": self._topp_var.get(),
            "flash_attention": self._flash_attn_var.get(),
        }

    def _show_local_settings(self, show: bool):
        """Show or hide the local model settings panel."""
        if show:
            # Insert after model combo, before the separator
            try:
                self._local_settings_fr.pack(fill="x", after=self.model_combo.master)
            except Exception:
                self._local_settings_fr.pack(fill="x")
        else:
            self._local_settings_fr.pack_forget()

    def _show_load_status(self, text: str = ""):
        """Show or hide the loading status label."""
        if text:
            self._load_status_var.set(text)
            self._load_status_lbl.pack(fill="x", pady=(0, 2))
        else:
            self._load_status_var.set("")
            self._load_status_lbl.pack_forget()

    def _is_local_entry(self, model_id: str) -> bool:
        """Check if a model_id belongs to the local LM Studio models."""
        return any(mid == model_id for mid, _, _ in self._lm_studio_models)

    def refresh_models(self):
        """Probe LM Studio in a background thread and merge local models into the list."""
        def _probe():
            local_models = []
            states = {}
            try:
                from gui.lm_studio import LMStudioPanel, LMStudioClient
                url = LMStudioPanel._resolve_base_url()
                client = LMStudioClient(base_url=url)
                if client.is_running():
                    for m in client.list_models_api():
                        mid = m.get("id", "")
                        if mid:
                            state = m.get("state", "unknown")
                            states[mid] = state
                            short = mid.split("/")[-1] if "/" in mid else mid
                            tag = "\u2713 " if state == "loaded" else ""
                            local_models.append((mid, f"[Local] {tag}{short}", "LM Studio"))
            except Exception:
                pass
            self._lm_studio_models = local_models
            self._model_states = states
            self._all_models = self._get_unified_models()
            # Register local model IDs with the bridge for routing
            if self.on_local_models and local_models:
                local_ids = [mid for mid, _, _ in local_models]
                try:
                    self.after(0, lambda ids=local_ids: self.on_local_models(ids))
                except Exception:
                    pass
            # Update combobox on main thread
            try:
                self.after(0, self._update_combobox_values)
            except Exception:
                pass

        threading.Thread(target=_probe, daemon=True).start()

    def _on_new(self):
        if self.on_new:
            self.on_new()

    def _on_model_selected(self, event):
        idx = self.model_combo.current()
        if idx == len(self._all_models):
            # User selected "+ 自訂模型..."
            title = t("sidebar.add_custom_model", "+ 自訂模型...")
            prompt = t("sidebar.custom_model_prompt", "請輸入模型 ID（例如：auto、claude-3-7-sonnet、deepseek-chat）：")
            new_model = simpledialog.askstring(title, prompt, parent=self.winfo_toplevel())
            if new_model and new_model.strip():
                new_model = new_model.strip()
                add_custom_model(new_model)
                self.model_var.set(new_model)
                self._update_combobox_values()
                if self.on_model_change:
                    self.on_model_change(new_model)
            else:
                self._select_model_in_combo(self.model_var.get())
            return
        elif idx == len(self._all_models) + 1:
            # User selected "✎ 管理模型清單..."
            CustomModelsDialog(self.winfo_toplevel(), on_change=lambda mid=None: self.refresh_model_list(mid))
            self._select_model_in_combo(self.model_var.get())
            return

        if 0 <= idx < len(self._all_models):
            model_id = self._all_models[idx][0]
            self.model_var.set(model_id)
            is_local = self._is_local_entry(model_id)

            # Show/hide local settings panel
            self._show_local_settings(is_local)

            if is_local and self._auto_load_var.get():
                # Always load via SDK to ensure correct GPU placement,
                # even if the model is already loaded (may be on wrong GPU)
                self._auto_load_model(model_id)
                return  # on_model_change called after load completes
            if self.on_model_change:
                self.on_model_change(model_id)

    def _auto_load_model(self, model_id: str):
        """Auto-load a local model in background, then fire on_model_change."""
        if self._loading_model:
            return
        self._loading_model = True
        self._show_load_status("Loading model...")
        self.model_combo.configure(state="disabled")

        settings = self.get_local_settings()

        def _load():
            import logging as _log
            _dbg = _log.getLogger("hermes.autoload")
            if not _dbg.handlers:
                _log_dir = get_hermes_home() / "logs"
                _log_dir.mkdir(parents=True, exist_ok=True)
                _fh = _log.FileHandler(str(_log_dir / "bridge.log"), encoding="utf-8")
                _fh.setFormatter(_log.Formatter("%(asctime)s %(levelname)s %(message)s"))
                _dbg.addHandler(_fh)
                _dbg.setLevel(_log.DEBUG)

            success = False
            error_msg = ""
            _dbg.debug("auto-load START model=%r gpu=%r ctx=%r",
                       model_id, settings["gpu_index"], settings["context_length"])
            try:
                from gui.lm_studio import LMStudioPanel, LMStudioClient
                url = LMStudioPanel._resolve_base_url()
                client = LMStudioClient(base_url=url)
                if not client.connect_sdk():
                    error_msg = "LM Studio SDK not available. Load the model manually in LM Studio."
                    _dbg.debug("auto-load SDK connect FAILED")
                else:
                    _dbg.debug("auto-load SDK connected, calling load_model...")
                    client.load_model(
                        model_path=model_id,
                        gpu_index=settings["gpu_index"],
                        context_length=settings["context_length"],
                        flash_attention=settings.get("flash_attention", True),
                    )
                    success = True
                    _dbg.debug("auto-load SUCCESS")
            except Exception as e:
                error_msg = str(e)
                _dbg.error("auto-load EXCEPTION: %s", error_msg)

            # Back to main thread
            try:
                self.after(0, lambda: self._on_auto_load_complete(model_id, success, error_msg))
            except Exception:
                pass

        threading.Thread(target=_load, daemon=True).start()

    def _on_auto_load_complete(self, model_id: str, success: bool, error: str):
        """Handle auto-load result on main thread."""
        self._loading_model = False
        self.model_combo.configure(state="readonly")

        if success:
            self._show_load_status("\u2713 Loaded")
            self._model_states[model_id] = "loaded"
            self.after(500, self.refresh_models)
            self.after(1500, lambda: self._show_load_status(""))
        else:
            short_err = error[:80] if error else "Unknown error"
            self._show_load_status(f"\u2717 {short_err}")
            self.after(5000, lambda: self._show_load_status(""))

        # Notify HermesGUI of load result
        if self.on_auto_load:
            self.on_auto_load(model_id, success, error)
        # Always switch to the model (user may have loaded it manually)
        if self.on_model_change:
            self.on_model_change(model_id)

    def _load_sessions(self):
        """Load recent sessions from SessionDB."""
        try:
            from hermes_state import SessionDB
            with SessionDB() as db:
                sessions = db.list_sessions_rich(source=None, limit=20)
            for widget in self.session_frame.winfo_children():
                widget.destroy()
            if not sessions:
                tk.Label(self.session_frame, text="No past sessions yet",
                        font=FONTS["small"], fg=C["text_disabled"],
                        bg=C["bg_sidebar"], padx=12).pack(anchor="w", pady=4)
                return
            for sess in sessions:
                self._add_session_entry(sess)
        except Exception:
            tk.Label(self.session_frame, text="No sessions found",
                    font=FONTS["small"], fg=C["text_disabled"],
                    bg=C["bg_sidebar"], padx=12).pack(anchor="w", pady=4)

    def _add_session_entry(self, sess):
        sid = sess.get("id", "")
        title = sess.get("title") or sess.get("preview", "Untitled")
        if len(title) > 35:
            title = title[:32] + "..."
        model = sess.get("model", "")
        msg_count = sess.get("message_count", 0)

        if not hasattr(self, '_session_widgets'):
            self._session_widgets = {}
        entry = tk.Frame(self.session_frame, bg=C["bg_sidebar"], padx=12, pady=4,
                        cursor="hand2")
        entry.pack(fill="x", pady=1)
        self._session_widgets[sid] = entry

        # Top row: title + delete button
        top_row = tk.Frame(entry, bg=C["bg_sidebar"])
        top_row.pack(fill="x")

        tk.Label(top_row, text=title, font=FONTS["small"],
                fg=C["text_primary"], bg=C["bg_sidebar"],
                anchor="w", wraplength=S(190)).pack(side="left", fill="x", expand=True)

        # Delete button (only visible on hover)
        del_btn = tk.Label(top_row, text="\u2715", font=SF("Segoe UI", 9),
                          fg=C["bg_sidebar"], bg=C["bg_sidebar"],
                          cursor="hand2", padx=4)
        del_btn.pack(side="right")
        del_btn.bind("<Button-1>", lambda e, s=sid: self._delete_session(s))

        info_text = f"{msg_count} msgs"
        if model:
            short_model = model.split("/")[-1][:15]
            info_text += f" | {short_model}"

        tk.Label(entry, text=info_text, font=SF("Segoe UI", 8),
                fg=C["text_disabled"], bg=C["bg_sidebar"],
                anchor="w").pack(fill="x")

        # Hover effect — show delete button on hover
        def _enter(e, f=entry, d=del_btn):
            f.configure(bg=C["bg_hover"])
            for c in f.winfo_children():
                c.configure(bg=C["bg_hover"])
                for gc in c.winfo_children():
                    gc.configure(bg=C["bg_hover"])
            d.configure(fg=C["danger"])  # Show the X

        def _leave(e, f=entry, d=del_btn):
            f.configure(bg=C["bg_sidebar"])
            for c in f.winfo_children():
                c.configure(bg=C["bg_sidebar"])
                for gc in c.winfo_children():
                    gc.configure(bg=C["bg_sidebar"])
            d.configure(fg=C["bg_sidebar"])  # Hide the X

        entry.bind("<Enter>", _enter)
        entry.bind("<Leave>", _leave)
        for child in entry.winfo_children():
            child.bind("<Enter>", _enter)
            child.bind("<Leave>", _leave)
            for gc in child.winfo_children():
                gc.bind("<Enter>", _enter)
                gc.bind("<Leave>", _leave)
                if gc != del_btn:
                    gc.bind("<Button-1>", lambda e, s=sid: self._select_session(s))
        entry.bind("<Button-1>", lambda e, s=sid: self._select_session(s))
        entry.bind("<MouseWheel>", lambda e: self.session_canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))

    def _select_session(self, session_id):
        if self.on_session_select:
            self.on_session_select(session_id)

    def _delete_session(self, session_id):
        """Delete a session with optional confirmation dialog."""
        if self._confirm_delete:
            # Custom dialog with "don't show again" checkbox
            dlg = tk.Toplevel(self)
            dlg.title(t("sidebar.delete_title", "Delete Session"))
            dlg.configure(bg=C["bg_main"])
            dlg.transient(self.winfo_toplevel())
            dlg.grab_set()

            # Content — pack first so we can measure before geometry
            tk.Label(dlg, text=t("sidebar.delete_title", "Delete Session"),
                    font=FONTS["subheading"], fg=C["text_primary"],
                    bg=C["bg_main"]).pack(pady=(20, 4))
            tk.Label(dlg, text=t("sidebar.delete_confirm",
                                 "Are you sure you want to delete session '{session_id}'?\n\nThis cannot be undone.",
                                 session_id=session_id[:8]),
                    font=FONTS["small"], fg=C["text_hint"],
                    bg=C["bg_main"], justify="center").pack(pady=(0, 12))

            # Don't show again checkbox
            dont_ask = tk.BooleanVar(value=False)
            tk.Checkbutton(dlg, text="Don't ask me again",
                          variable=dont_ask, font=FONTS["small"],
                          fg=C["text_secondary"], bg=C["bg_main"],
                          selectcolor=C["bg_input"],
                          activebackground=C["bg_main"],
                          activeforeground=C["text_primary"]).pack(pady=(0, 8))

            btn_frame = tk.Frame(dlg, bg=C["bg_main"])
            btn_frame.pack(pady=(4, 16))

            def _do_delete():
                if dont_ask.get():
                    self._confirm_delete = False
                dlg.destroy()
                self._perform_delete(session_id)

            ttk.Button(btn_frame, text=f"  {t('sidebar.delete_title', 'Delete')}  ", style="Danger.TButton",
                       command=_do_delete).pack(side="left", padx=8)
            ttk.Button(btn_frame, text=f"  {t('perms.cancel', 'Cancel')}  ", style="TButton",
                       command=dlg.destroy).pack(side="left", padx=8)

            set_dark_title_bar(dlg)
            center_window(dlg, 420, 220, self.winfo_toplevel())
        else:
            self._perform_delete(session_id)

    def _perform_delete(self, session_id):
        """Remove widget instantly, delete from DB in background."""
        # Immediate visual removal
        widget = getattr(self, '_session_widgets', {}).pop(session_id, None)
        if widget:
            widget.destroy()

        # DB delete in background
        def _do():
            try:
                from hermes_state import SessionDB
                with SessionDB() as db:
                    db.delete_session(session_id)
            except Exception:
                try:
                    import sqlite3
                    from hermes_state import DEFAULT_DB_PATH
                    conn = sqlite3.connect(str(DEFAULT_DB_PATH))
                    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
        threading.Thread(target=_do, daemon=True).start()

    def refresh_sessions(self):
        self._load_sessions()

    def update_language(self):
        """Refresh sidebar texts according to active language."""
        if hasattr(self, 'new_btn'):
            self.new_btn.configure(text=t("sidebar.new_chat", "+ New Chat"))
        if hasattr(self, 'model_lbl'):
            self.model_lbl.configure(text=t("sidebar.model", "Model:"))
        if hasattr(self, 'sessions_lbl'):
            self.sessions_lbl.configure(text=t("sidebar.recent_sessions", "Recent Sessions"))
        if hasattr(self, 'local_hdr_lbl'):
            self.local_hdr_lbl.configure(text=t("sidebar.local_settings", "Local Model Settings"))
        if hasattr(self, 'gpu_lbl'):
            self.gpu_lbl.configure(text=t("sidebar.gpu_offload", "GPU:"))
        if hasattr(self, 'ctx_lbl'):
            self.ctx_lbl.configure(text=t("sidebar.context_len", "Ctx:"))
        if hasattr(self, 'temp_lbl'):
            self.temp_lbl.configure(text=t("sidebar.temp", "Temp:"))


# ============================================================================
# About Dialog
# ============================================================================

class AboutDialog(tk.Toplevel):
    """Custom About dialog with MIT license info and clickable hyperlinks."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title(t("about.title", "About Portable Hermes Agent"))
        self.configure(bg=C["bg_main"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        try:
            center_window(self, 520, 440, parent)
            set_dark_title_bar(self)
        except Exception:
            pass

        pad = tk.Frame(self, bg=C["bg_main"], padx=20, pady=16)
        pad.pack(fill="both", expand=True)

        # Header
        tk.Label(pad, text="HERMES AGENT", font=FONTS["logo"],
                 fg=C["accent"], bg=C["bg_main"]).pack(pady=(0, 2))
        tk.Label(pad, text=f"Core v{HERMES_CORE_VERSION} • Portable Windows Distribution",
                 font=FONTS["small"] + ("bold",), fg=C["text_primary"], bg=C["bg_main"]).pack(pady=(0, 10))

        # License Frame
        lic_frame = tk.LabelFrame(pad, text=t("about.license_title", "License: MIT Open Source License"),
                                  font=FONTS["small"] + ("bold",), fg=C["accent"],
                                  bg=C["bg_card"], padx=10, pady=8, highlightthickness=0)
        lic_frame.pack(fill="x", pady=(0, 12))

        tk.Label(lic_frame, text=t("about.copy_notice", "Copyright (c) 2024-2026 Nous Research & Portable Hermes Contributors"),
                 font=SF("Segoe UI", 8), fg=C["text_secondary"], bg=C["bg_card"], anchor="w").pack(fill="x")
        tk.Label(lic_frame, text=t("about.license_summary", "Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files, to deal in the Software without restriction."),
                 font=SF("Segoe UI", 8), fg=C["text_hint"], bg=C["bg_card"], wraplength=S(460), justify="left", anchor="w").pack(fill="x", pady=(4, 0))

        # Clickable Hyperlinks
        links_frame = tk.Frame(pad, bg=C["bg_main"])
        links_frame.pack(fill="x", pady=(0, 12))

        def _make_link(parent_frame, text, url):
            row = tk.Frame(parent_frame, bg=C["bg_main"])
            row.pack(fill="x", pady=2)
            lbl = tk.Label(row, text=text, font=SF("Segoe UI", 9, "underline"),
                           fg=C["accent"], bg=C["bg_main"], cursor="hand2", anchor="w")
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
            Tooltip(lbl, f"點擊在瀏覽器中開啟 {url}")

        _make_link(links_frame, "🌐 " + t("about.repo_link", "GitHub Repository: https://github.com/aivrar/portable-hermes-agent"), "https://github.com/aivrar/portable-hermes-agent")
        _make_link(links_frame, "📦 " + t("about.upstream_link", "Upstream Project: https://github.com/NousResearch/hermes-agent"), "https://github.com/NousResearch/hermes-agent")
        _make_link(links_frame, "📜 " + t("about.license_link", "MIT License: https://opensource.org/licenses/MIT"), "https://opensource.org/licenses/MIT")

        # Close button
        ttk.Button(pad, text=t("about.close", "關閉"), style="Primary.TButton",
                   command=self.destroy).pack(pady=(4, 0))


# ============================================================================
# Custom Models Dialog
# ============================================================================

class CustomModelsDialog(tk.Toplevel):
    """Dialog to manage (view, add, edit, delete) custom model IDs."""

    def __init__(self, parent, on_change=None):
        super().__init__(parent)
        self.on_change = on_change
        self.title(t("models.manage_title", "管理自訂模型清單"))
        self.configure(bg=C["bg_main"])
        self.transient(parent)
        self.grab_set()

        try:
            center_window(self, 460, 380, parent)
            set_dark_title_bar(self)
        except Exception:
            pass

        pad = tk.Frame(self, bg=C["bg_main"], padx=16, pady=16)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text=t("models.manage_title", "管理自訂模型清單"),
                 font=FONTS["subtitle"], fg=C["accent"], bg=C["bg_main"]).pack(anchor="w", pady=(0, 8))

        list_frame = tk.Frame(pad, bg=C["bg_input"], highlightbackground=C["border"], highlightthickness=1)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                  font=FONTS["mono_small"], bg=C["bg_input"],
                                  fg=C["text_primary"], selectbackground=C["accent"],
                                  selectforeground="white", relief="flat", borderwidth=0)
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        btn_row = tk.Frame(pad, bg=C["bg_main"])
        btn_row.pack(fill="x", pady=(0, 6))

        ttk.Button(btn_row, text=t("models.add", "+ 新增模型"), style="Small.TButton",
                   command=self._add_model).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text=t("models.edit", "✎ 編輯"), style="Small.TButton",
                   command=self._edit_model).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text=t("models.delete", "🗑 刪除"), style="Small.TButton",
                   command=self._delete_model).pack(side="left")

        ttk.Button(pad, text=t("about.close", "關閉"), style="Primary.TButton",
                   command=self.destroy).pack(pady=(6, 0))

        self._refresh()

    def _refresh(self):
        self.listbox.delete(0, "end")
        models = get_custom_models()
        for m in models:
            self.listbox.insert("end", m)

    def _add_model(self):
        val = simpledialog.askstring(t("models.add", "+ 新增模型"),
                                    t("sidebar.custom_model_prompt", "請輸入模型 ID："),
                                    parent=self)
        if val and val.strip():
            add_custom_model(val.strip())
            self._refresh()
            if self.on_change:
                self.on_change(val.strip())

    def _edit_model(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        old_val = self.listbox.get(sel[0])
        new_val = simpledialog.askstring(t("models.edit_title", "編輯模型 ID"),
                                         t("models.edit_prompt", "請輸入新的模型識別碼："),
                                         initialvalue=old_val, parent=self)
        if new_val and new_val.strip() and new_val.strip() != old_val:
            update_custom_model(old_val, new_val.strip())
            self._refresh()
            if self.on_change:
                self.on_change(new_val.strip())

    def _delete_model(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        val = self.listbox.get(sel[0])
        if messagebox.askyesno(t("models.delete", "刪除模型"),
                               t("models.delete_confirm", "確定要刪除模型「{model}」嗎？", model=val),
                               parent=self):
            remove_custom_model(val)
            self._refresh()
            if self.on_change:
                self.on_change(None)


# ============================================================================
# Custom Endpoints Dialog
# ============================================================================

class CustomEndpointsDialog(tk.Toplevel):
    """Dialog to manage multiple custom API endpoints."""

    def __init__(self, parent, on_change=None):
        super().__init__(parent)
        self.on_change = on_change
        self.title(t("endpoints.title", "自訂 API 端點清單"))
        self.configure(bg=C["bg_main"])
        self.transient(parent)
        self.grab_set()

        try:
            center_window(self, 560, 460, parent)
            set_dark_title_bar(self)
        except Exception:
            pass

        pad = tk.Frame(self, bg=C["bg_main"], padx=16, pady=16)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text=t("endpoints.title", "自訂 API 端點清單"),
                 font=FONTS["subtitle"], fg=C["accent"], bg=C["bg_main"]).pack(anchor="w")
        tk.Label(pad, text=t("endpoints.desc", "管理多個 OpenAI 相容端點（支援 TokenTable、Ollama、vLLM、OneAPI 等）"),
                 font=SF("Segoe UI", 8), fg=C["text_secondary"], bg=C["bg_main"]).pack(anchor="w", pady=(0, 8))

        list_frame = tk.Frame(pad, bg=C["bg_input"], highlightbackground=C["border"], highlightthickness=1)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                  font=FONTS["mono_small"], bg=C["bg_input"],
                                  fg=C["text_primary"], selectbackground=C["accent"],
                                  selectforeground="white", relief="flat", borderwidth=0)
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        self.status_lbl = tk.Label(pad, text="", font=SF("Segoe UI", 8), fg=C["success"], bg=C["bg_main"])
        self.status_lbl.pack(anchor="w", pady=(0, 4))

        btn_row = tk.Frame(pad, bg=C["bg_main"])
        btn_row.pack(fill="x", pady=(0, 6))

        ttk.Button(btn_row, text=t("endpoints.activate", "★ 設為目前啟用"), style="Primary.TButton",
                   command=self._activate_selected).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text=t("endpoints.add", "+ 新增端點"), style="Small.TButton",
                   command=self._add_endpoint).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text=t("endpoints.edit", "✎ 編輯"), style="Small.TButton",
                   command=self._edit_endpoint).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text=t("endpoints.delete", "🗑 刪除"), style="Small.TButton",
                   command=self._delete_endpoint).pack(side="left")

        ttk.Button(pad, text=t("about.close", "關閉"), style="Secondary.TButton",
                   command=self.destroy).pack(pady=(4, 0))

        self._refresh()

    def _refresh(self):
        self.listbox.delete(0, "end")
        self.endpoints = get_custom_endpoints()
        active_id = os.getenv("ACTIVE_CUSTOM_ENDPOINT_ID", "")
        cur_url = os.getenv("OPENAI_BASE_URL", "").rstrip("/")

        for ep in self.endpoints:
            name = ep.get("name", "Endpoint")
            url = ep.get("base_url", "")
            is_active = (ep.get("id") == active_id) or (url.rstrip("/") == cur_url and cur_url != "")
            badge = "★ [啟用中] " if is_active else "   "
            self.listbox.insert("end", f"{badge}{name}  ({url})")

    def _activate_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        ep = self.endpoints[sel[0]]
        activate_custom_endpoint(ep)
        self._refresh()
        self.status_lbl.configure(text=t("endpoints.activated_msg", "已將端點「{name}」設為目前啟用端點。", name=ep.get("name")), fg=C["success"])
        if self.on_change:
            self.on_change(ep)

    def _add_endpoint(self):
        self._open_edit_dialog(None)

    def _edit_endpoint(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        self._open_edit_dialog(self.endpoints[sel[0]])

    def _open_edit_dialog(self, ep):
        dlg = tk.Toplevel(self)
        dlg.title(t("endpoints.edit_title", "端點設定"))
        dlg.configure(bg=C["bg_main"])
        dlg.transient(self)
        dlg.grab_set()

        try:
            center_window(dlg, 420, 320, self)
            set_dark_title_bar(dlg)
        except Exception:
            pass

        p = tk.Frame(dlg, bg=C["bg_main"], padx=16, pady=12)
        p.pack(fill="both", expand=True)

        tk.Label(p, text=t("endpoints.name", "名稱："), font=FONTS["small"], fg=C["text_secondary"], bg=C["bg_main"]).pack(anchor="w")
        name_ent = tk.Entry(p, font=FONTS["body"], bg=C["bg_input"], fg=C["text_primary"], insertbackground=C["text_primary"], relief="flat")
        name_ent.pack(fill="x", pady=(2, 6))
        if ep:
            name_ent.insert(0, ep.get("name", ""))

        tk.Label(p, text=t("endpoints.base_url", "端點網址 (Base URL)："), font=FONTS["small"], fg=C["text_secondary"], bg=C["bg_main"]).pack(anchor="w")
        url_ent = tk.Entry(p, font=FONTS["mono_small"], bg=C["bg_input"], fg=C["text_primary"], insertbackground=C["text_primary"], relief="flat")
        url_ent.pack(fill="x", pady=(2, 6))
        if ep:
            url_ent.insert(0, ep.get("base_url", ""))
        else:
            url_ent.insert(0, "https://")

        tk.Label(p, text=t("endpoints.api_key", "金鑰 (API Key)："), font=FONTS["small"], fg=C["text_secondary"], bg=C["bg_main"]).pack(anchor="w")
        key_ent = tk.Entry(p, font=FONTS["mono_small"], bg=C["bg_input"], fg=C["text_primary"], insertbackground=C["text_primary"], relief="flat")
        key_ent.pack(fill="x", pady=(2, 6))
        if ep:
            key_ent.insert(0, ep.get("api_key", ""))

        tk.Label(p, text=t("endpoints.model", "預設模型："), font=FONTS["small"], fg=C["text_secondary"], bg=C["bg_main"]).pack(anchor="w")
        model_ent = tk.Entry(p, font=FONTS["mono_small"], bg=C["bg_input"], fg=C["text_primary"], insertbackground=C["text_primary"], relief="flat")
        model_ent.pack(fill="x", pady=(2, 10))
        if ep:
            model_ent.insert(0, ep.get("model", "auto"))
        else:
            model_ent.insert(0, "auto")

        def _save_ep():
            nm = name_ent.get().strip() or "Custom Endpoint"
            u = url_ent.get().strip()
            k = key_ent.get().strip()
            m = model_ent.get().strip() or "auto"
            if not u:
                return
            if ep:
                ep["name"] = nm
                ep["base_url"] = u
                ep["api_key"] = k
                ep["model"] = m
                save_custom_endpoints(self.endpoints)
            else:
                add_custom_endpoint(nm, u, k, m)
            dlg.destroy()
            self._refresh()
            if self.on_change:
                self.on_change(None)

        ttk.Button(p, text=t("settings.save", "儲存"), style="Primary.TButton", command=_save_ep).pack()

    def _delete_endpoint(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        ep = self.endpoints[sel[0]]
        if messagebox.askyesno(t("endpoints.delete", "刪除端點"),
                               t("endpoints.delete_confirm", "確定要刪除端點「{name}」嗎？", name=ep.get("name")),
                               parent=self):
            delete_custom_endpoint(ep.get("id"))
            self._refresh()
            if self.on_change:
                self.on_change(None)


# ============================================================================
# Settings Dialog
# ============================================================================

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, bridge):
        super().__init__(parent)
        self.bridge = bridge
        self.title(t("settings.title", "Settings"))
        self.configure(bg=C["bg_main"])
        self.transient(parent)
        self.grab_set()
        set_dark_title_bar(self)
        center_window(self, 560, 620, parent)
        self.resizable(True, True)

        tk.Label(self, text=t("settings.title", "Settings"), font=FONTS["title"],
                fg=C["accent"], bg=C["bg_main"]).pack(pady=(16, 6))

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=8)

        # -- General tab --
        gen_fr = tk.Frame(nb, bg=C["bg_main"], padx=16, pady=16)
        nb.add(gen_fr, text=t("settings.tab_general", "  General  "))
        self._build_general(gen_fr)

        # -- API Keys tab --
        api_fr = tk.Frame(nb, bg=C["bg_main"], padx=16, pady=16)
        nb.add(api_fr, text=t("settings.tab_api", "  API Keys  "))
        self._build_api(api_fr)

        # -- Custom Endpoints tab --
        ep_fr = tk.Frame(nb, bg=C["bg_main"], padx=16, pady=16)
        nb.add(ep_fr, text=t("settings.tab_endpoints", "  API Endpoints  "))
        self._build_endpoints(ep_fr)

        # -- Model tab --
        mdl_fr = tk.Frame(nb, bg=C["bg_main"], padx=16, pady=16)
        nb.add(mdl_fr, text=t("settings.tab_model", "  Model  "))
        self._build_model(mdl_fr)

        ttk.Button(self, text=t("settings.save", "Save & Close"), style="Primary.TButton",
                   command=self._save).pack(pady=(4, 16))

    def _build_general(self, parent):
        tk.Label(parent, text=t("settings.language", "Interface Language"), font=FONTS["small"],
                fg=C["text_secondary"], bg=C["bg_main"]).pack(anchor="w", pady=(6, 2))

        self.lang_var = tk.StringVar(value=get_language())
        self._lang_map = {name: code for code, name in SUPPORTED_LANGUAGES}
        self._code_to_name = {code: name for code, name in SUPPORTED_LANGUAGES}

        current_name = self._code_to_name.get(self.lang_var.get(), "English")
        lang_names = [name for _, name in SUPPORTED_LANGUAGES]

        self.lang_combo = ttk.Combobox(parent, values=lang_names, state="readonly", font=FONTS["small"])
        self.lang_combo.set(current_name)
        self.lang_combo.pack(fill="x", pady=(2, 16))

    def _build_api(self, parent):
        keys = [
            ("OPENROUTER_API_KEY", "OpenRouter (main LLM provider)"),
            ("TOKENTABLE_API_KEY", "TokenTable (AI 大模型聚合平台)"),
            ("CUSTOM_BASE_URL", "Custom API Base URL (自訂端點網址)"),
            ("OPENAI_API_KEY", "Custom / OpenAI API Key (自訂端點金鑰)"),
            ("FIRECRAWL_API_KEY", "Firecrawl (web search)"),
            ("FAL_KEY", "FAL.ai (image generation)"),
            ("SERPER_API_KEY", "Serper.dev (Google search)"),
            ("VOICE_TOOLS_OPENAI_KEY", "OpenAI (voice/transcription)"),
            ("GITHUB_TOKEN", "GitHub (Skills Hub rate limits)"),
        ]
        self.key_entries = {}
        for key, label in keys:
            tk.Label(parent, text=label, font=FONTS["small"],
                    fg=C["text_secondary"], bg=C["bg_main"]).pack(anchor="w", pady=(4, 0))
            show_char = "" if "BASE_URL" in key else "*"
            ent = tk.Entry(parent, font=FONTS["mono_small"],
                          bg=C["bg_input"], fg=C["text_primary"],
                          insertbackground=C["text_primary"],
                          relief="flat", show=show_char)
            ent.pack(fill="x", ipady=3)
            cur = os.getenv(key, "")
            if not cur and key == "CUSTOM_BASE_URL":
                cur = os.getenv("OPENAI_BASE_URL", "")
            if not cur and key == "OPENAI_API_KEY":
                cur = os.getenv("CUSTOM_API_KEY", "")
            if cur:
                ent.insert(0, cur)
            self.key_entries[key] = ent

    def _build_endpoints(self, parent):
        tk.Label(parent, text=t("endpoints.desc", "管理多個 OpenAI 相容端點（支援 TokenTable、Ollama、vLLM、OneAPI 等）"),
                 font=SF("Segoe UI", 8), fg=C["text_secondary"], bg=C["bg_main"],
                 wraplength=S(500), justify="left").pack(anchor="w", pady=(0, 8))

        list_frame = tk.Frame(parent, bg=C["bg_input"], highlightbackground=C["border"], highlightthickness=1)
        list_frame.pack(fill="both", expand=True, pady=(0, 8))

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.ep_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                     font=FONTS["mono_small"], bg=C["bg_input"],
                                     fg=C["text_primary"], selectbackground=C["accent"],
                                     selectforeground="white", relief="flat", borderwidth=0)
        scrollbar.config(command=self.ep_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.ep_listbox.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        self.ep_status_lbl = tk.Label(parent, text="", font=SF("Segoe UI", 8), fg=C["success"], bg=C["bg_main"])
        self.ep_status_lbl.pack(anchor="w", pady=(0, 4))

        btn_row = tk.Frame(parent, bg=C["bg_main"])
        btn_row.pack(fill="x", pady=(0, 4))

        ttk.Button(btn_row, text=t("endpoints.activate", "★ 設為目前啟用"), style="Primary.TButton",
                   command=self._activate_selected_ep).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text=t("endpoints.add", "+ 新增端點"), style="Small.TButton",
                   command=self._add_ep).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text=t("endpoints.edit", "✎ 編輯"), style="Small.TButton",
                   command=self._edit_ep).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text=t("endpoints.delete", "🗑 刪除"), style="Small.TButton",
                   command=self._delete_ep).pack(side="left")

        self._refresh_endpoints()

    def _refresh_endpoints(self):
        self.ep_listbox.delete(0, "end")
        self.endpoints_data = get_custom_endpoints()
        active_id = os.getenv("ACTIVE_CUSTOM_ENDPOINT_ID", "")
        cur_url = os.getenv("OPENAI_BASE_URL", "").rstrip("/")

        for ep in self.endpoints_data:
            name = ep.get("name", "Endpoint")
            url = ep.get("base_url", "")
            is_active = (ep.get("id") == active_id) or (url.rstrip("/") == cur_url and cur_url != "")
            badge = "★ [啟用中] " if is_active else "   "
            self.ep_listbox.insert("end", f"{badge}{name}  ({url})")

    def _activate_selected_ep(self):
        sel = self.ep_listbox.curselection()
        if not sel:
            return
        ep = self.endpoints_data[sel[0]]
        activate_custom_endpoint(ep)
        self._refresh_endpoints()
        if "CUSTOM_BASE_URL" in self.key_entries:
            self.key_entries["CUSTOM_BASE_URL"].delete(0, "end")
            self.key_entries["CUSTOM_BASE_URL"].insert(0, ep.get("base_url", ""))
        if "OPENAI_API_KEY" in self.key_entries:
            self.key_entries["OPENAI_API_KEY"].delete(0, "end")
            self.key_entries["OPENAI_API_KEY"].insert(0, ep.get("api_key", ""))
        self.ep_status_lbl.configure(text=t("endpoints.activated_msg", "已將端點「{name}」設為目前啟用端點。", name=ep.get("name")), fg=C["success"])

    def _add_ep(self):
        CustomEndpointsDialog(self, on_change=lambda ep: self._refresh_endpoints())

    def _edit_ep(self):
        CustomEndpointsDialog(self, on_change=lambda ep: self._refresh_endpoints())

    def _delete_ep(self):
        sel = self.ep_listbox.curselection()
        if not sel:
            return
        ep = self.endpoints_data[sel[0]]
        if messagebox.askyesno(t("endpoints.delete", "刪除端點"),
                               t("endpoints.delete_confirm", "確定要刪除端點「{name}」嗎？", name=ep.get("name")),
                               parent=self):
            delete_custom_endpoint(ep.get("id"))
            self._refresh_endpoints()

    def _build_model(self, parent):
        tk.Label(parent, text=t("settings.default_model", "Default Model"), font=FONTS["small"],
                fg=C["text_secondary"], bg=C["bg_main"]).pack(anchor="w", pady=(2, 0))

        base_ids = [m[0] for m in Sidebar.BASE_MODELS]
        custom_ids = [m for m in get_custom_models() if m not in base_ids]
        models = base_ids + custom_ids

        cur_model = self.bridge.get_model() if self.bridge else "auto"
        if cur_model not in models:
            models.insert(0, cur_model)

        self.model_var = tk.StringVar(value=cur_model)
        self.model_combo = ttk.Combobox(parent, textvariable=self.model_var,
                                        values=models, font=FONTS["mono_small"])
        self.model_combo.pack(fill="x", pady=(4, 6))

        tk.Label(parent, text=t("settings.model_hint", "可選取或輸入任意模型 ID（例如 TokenTable 的 auto、claude-3-7-sonnet、deepseek-chat 等）"),
                font=SF("Segoe UI", 8), fg=C["text_disabled"], bg=C["bg_main"], wraplength=500, justify="left").pack(anchor="w", pady=(0, 10))

        # Add custom model frame
        add_frame = tk.LabelFrame(parent, text=t("settings.add_custom_model", "手動新增自訂模型"),
                                  font=FONTS["small"], fg=C["accent"], bg=C["bg_main"],
                                  padx=10, pady=8)
        add_frame.pack(fill="x", pady=(0, 10))

        input_row = tk.Frame(add_frame, bg=C["bg_main"])
        input_row.pack(fill="x", pady=(2, 4))

        self.custom_model_entry = tk.Entry(input_row, font=FONTS["mono_small"],
                                           bg=C["bg_input"], fg=C["text_primary"],
                                           insertbackground=C["text_primary"],
                                           relief="flat")
        self.custom_model_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 8))

        def _do_add_model():
            new_id = self.custom_model_entry.get().strip()
            if not new_id:
                return
            add_custom_model(new_id)
            vals = list(self.model_combo["values"])
            if new_id not in vals:
                vals.append(new_id)
                self.model_combo["values"] = vals
            self.model_var.set(new_id)
            self.custom_model_entry.delete(0, "end")
            self.model_status_lbl.configure(
                text=t("settings.model_added", "已新增並選取模型「{name}」", name=new_id),
                fg=C["success"]
            )

        add_btn = ttk.Button(input_row, text=t("settings.add_model_btn", "+ 新增至清單"),
                             style="Small.TButton", command=_do_add_model)
        add_btn.pack(side="right")
        self.custom_model_entry.bind("<Return>", lambda e: _do_add_model())

        self.model_status_lbl = tk.Label(add_frame, text="", font=SF("Segoe UI", 8),
                                         bg=C["bg_main"])
        self.model_status_lbl.pack(anchor="w")

        # Manage models button
        manage_row = tk.Frame(parent, bg=C["bg_main"])
        manage_row.pack(fill="x", pady=(0, 8))
        ttk.Button(manage_row, text=t("models.manage_title", "✎ 管理自訂模型清單..."),
                   style="Small.TButton", command=self._open_custom_models).pack(anchor="w")

    def _open_custom_models(self):
        def _on_models_changed(new_id=None):
            base_ids = [m[0] for m in Sidebar.BASE_MODELS]
            custom_ids = [m for m in get_custom_models() if m not in base_ids]
            self.model_combo["values"] = base_ids + custom_ids
            if new_id:
                self.model_var.set(new_id)
        CustomModelsDialog(self, on_change=_on_models_changed)

    def _save(self):
        # Save language
        chosen_name = self.lang_combo.get()
        chosen_code = self._lang_map.get(chosen_name, "en")
        if chosen_code != get_language():
            set_language(chosen_code)

        env_path = get_hermes_home() / ".env"
        env_path.parent.mkdir(parents=True, exist_ok=True)
        import re
        content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
        for key, ent in self.key_entries.items():
            val = ent.get().strip()
            if val:
                os.environ[key] = val
                pat = f"^{key}=.*$"
                repl = f"{key}={val}"
                if re.search(pat, content, re.MULTILINE):
                    content = re.sub(pat, repl, content, flags=re.MULTILINE)
                else:
                    content += f"\n{key}={val}\n"
                if key == "TOKENTABLE_API_KEY":
                    base_url = "https://tokentable.asia/v1"
                    add_custom_endpoint("TokenTable", base_url, val, "auto")
                    for extra_k, extra_v in [
                        ("CUSTOM_BASE_URL", base_url),
                        ("OPENAI_BASE_URL", base_url),
                        ("OPENAI_API_KEY", val),
                    ]:
                        os.environ[extra_k] = extra_v
                        p_extra = f"^{extra_k}=.*$"
                        r_extra = f"{extra_k}={extra_v}"
                        if re.search(p_extra, content, re.MULTILINE):
                            content = re.sub(p_extra, r_extra, content, flags=re.MULTILINE)
                        else:
                            content += f"\n{extra_k}={extra_v}\n"
                elif key == "CUSTOM_BASE_URL":
                    val_url = val.rstrip("/")
                    if val_url and val_url != "https://tokentable.asia/v1":
                        api_k = self.key_entries.get("OPENAI_API_KEY", None)
                        k_val = api_k.get().strip() if api_k else ""
                        add_custom_endpoint("Custom Endpoint", val_url, k_val, "auto")
                    os.environ["OPENAI_BASE_URL"] = val_url
                    p_extra = "^OPENAI_BASE_URL=.*$"
                    r_extra = f"OPENAI_BASE_URL={val_url}"
                    if re.search(p_extra, content, re.MULTILINE):
                        content = re.sub(p_extra, r_extra, content, flags=re.MULTILINE)
                    else:
                        content += f"\nOPENAI_BASE_URL={val_url}\n"
                elif key == "OPENAI_API_KEY":
                    os.environ["CUSTOM_API_KEY"] = val
                    p_extra = "^CUSTOM_API_KEY=.*$"
                    r_extra = f"CUSTOM_API_KEY={val}"
                    if re.search(p_extra, content, re.MULTILINE):
                        content = re.sub(p_extra, r_extra, content, flags=re.MULTILINE)
                    else:
                        content += f"\nCUSTOM_API_KEY={val}\n"
        model = self.model_var.get().strip()
        if model:
            add_custom_model(model)
            if self.bridge:
                self.bridge.set_model(model)
            try:
                from hermes_cli.config import load_config, save_config
                cfg = load_config()
                if "model" not in cfg or not isinstance(cfg["model"], dict):
                    cfg["model"] = {}
                cfg["model"]["default"] = model
                save_config(cfg)
            except Exception:
                pass
            if hasattr(self.master, "sidebar"):
                self.master.sidebar.refresh_model_list(selected=model)
            if hasattr(self.master, "status_bar"):
                self.master.status_bar.set_model(model)
        env_path.write_text(content, encoding="utf-8")
        self.destroy()


# ============================================================================
# Skills Browser
# ============================================================================

def _discover_installed_skills(skills_dir: Path) -> Dict[str, list]:
    """Return current nested SKILL.md entries grouped for the GUI browser."""
    import yaml

    categories: Dict[str, list] = {}
    for skill_md in sorted(skills_dir.rglob("SKILL.md")):
        relative_dir = skill_md.parent.relative_to(skills_dir)
        if any(part.startswith(".") for part in relative_dir.parts):
            continue

        name = skill_md.parent.name
        description = ""
        category = relative_dir.parts[0] if len(relative_dir.parts) > 1 else "uncategorized"
        try:
            text = skill_md.read_text(encoding="utf-8")
            if text.startswith("---"):
                frontmatter = yaml.safe_load(text.split("---", 2)[1]) or {}
                name = str(frontmatter.get("name") or name)
                description = str(frontmatter.get("description") or "")
                hermes_meta = (frontmatter.get("metadata") or {}).get("hermes") or {}
                category = str(hermes_meta.get("category") or category)
        except Exception:
            pass
        categories.setdefault(category, []).append((name, description))
    return categories

class SkillsBrowser(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(t("skills.title", "Skills Browser"))
        self.configure(bg=C["bg_main"])
        self.transient(parent)
        set_dark_title_bar(self)
        center_window(self, 650, 500, parent)

        tk.Label(self, text=t("skills.installed", "Installed Skills"), font=FONTS["title"],
                fg=C["accent"], bg=C["bg_main"]).pack(pady=(20, 8))

        self.text = tk.Text(self, wrap="word", bg=C["bg_card"], fg=C["text_primary"],
                           font=FONTS["mono_small"], relief="flat", padx=16, pady=12,
                           highlightthickness=0)
        sb = ttk.Scrollbar(self, command=self.text.yview)
        self.text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(0, 16), pady=(0, 16))
        self.text.pack(fill="both", expand=True, padx=(16, 0), pady=(0, 16))

        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            skills_dir = get_hermes_home() / "skills"
            if not skills_dir.exists():
                self.after(0, lambda: self._set("No skills directory found."))
                return
            cats = _discover_installed_skills(skills_dir)
            lines = []
            for cat in sorted(cats):
                lines.append(f"\n  {cat.upper()}")
                lines.append("  " + "-" * 40)
                for n, d in cats[cat]:
                    lines.append(f"    {n:30s} {d[:50]}" if d else f"    {n}")
            self.after(0, lambda: self._set("\n".join(lines) or "No skills found."))
        except Exception as e:
            self.after(0, lambda: self._set(f"Error: {e}"))

    def _set(self, txt):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", txt)
        self.text.configure(state="disabled")


# ============================================================================
# Status Bar
# ============================================================================

class StatusBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C["bg_sidebar"], height=S(28))
        self.pack_propagate(False)
        self._state = "ready"
        self._state_data = ""
        self._step_n = None

        self.dot = tk.Label(self, text="\u25CF", font=SF("Segoe UI", 10),
                           fg=C["success"], bg=C["bg_sidebar"])
        self.dot.pack(side="left", padx=(12, 4))

        self.status_lbl = tk.Label(self, text=t("status.ready", "Ready"), font=FONTS["small"],
                                  fg=C["text_hint"], bg=C["bg_sidebar"])
        self.status_lbl.pack(side="left")

        self.model_lbl = tk.Label(self, text="", font=FONTS["mono_small"],
                                 fg=C["text_disabled"], bg=C["bg_sidebar"])
        self.model_lbl.pack(side="right", padx=12)

        self.iter_lbl = tk.Label(self, text="", font=FONTS["mono_small"],
                                fg=C["text_disabled"], bg=C["bg_sidebar"])
        self.iter_lbl.pack(side="right", padx=8)

    def set_ready(self):
        self._state = "ready"
        self._state_data = ""
        self.dot.configure(fg=C["success"])
        self.status_lbl.configure(text=t("status.ready", "Ready"))

    def set_thinking(self, text=""):
        self._state = "thinking"
        self._state_data = text
        self.dot.configure(fg=C["info"])
        if text:
            # Truncate to fit status bar width
            display = text[:120] if len(text) > 120 else text
            self.status_lbl.configure(text=display)
        else:
            self.status_lbl.configure(text=t("status.thinking", "Thinking..."))

    def set_tool(self, name):
        self._state = "tool"
        self._state_data = name
        self.dot.configure(fg=C["warning_dark"])
        self.status_lbl.configure(text=t("status.running", f"Running: {name}", name=name))

    def set_error(self):
        self._state = "error"
        self.dot.configure(fg=C["danger"])
        self.status_lbl.configure(text=t("status.error", "Error"))

    def set_model(self, m):
        self.model_lbl.configure(text=m)

    def set_iter(self, n):
        self._step_n = n
        self.iter_lbl.configure(text=t("status.step", f"Step {n}", n=n))

    def update_language(self):
        if self._state == "ready":
            self.status_lbl.configure(text=t("status.ready", "Ready"))
        elif self._state == "thinking" and not self._state_data:
            self.status_lbl.configure(text=t("status.thinking", "Thinking..."))
        elif self._state == "tool":
            self.status_lbl.configure(text=t("status.running", f"Running: {self._state_data}", name=self._state_data))
        elif self._state == "error":
            self.status_lbl.configure(text=t("status.error", "Error"))

        if self._step_n is not None:
            self.iter_lbl.configure(text=t("status.step", f"Step {self._step_n}", n=self._step_n))


# ============================================================================
# Main Application
# ============================================================================

class HermesGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide until fully themed to avoid white flash

        # DPI awareness + scaling — must happen before any geometry calls
        init_dpi_scaling(self.root)

        self.root.title(t("app.title", "Portable Hermes Agent"))
        self.root.geometry(f"{S(1100)}x{S(700)}")
        self.root.minsize(S(900), S(550))

        # Apply full theme (also sets dark title bar)
        apply_theme(self.root)

        # Center and show
        center_window(self.root, 1100, 700)
        self.root.deiconify()

        # Agent bridge
        self.bridge = AgentBridge(
            self.root,
            on_response=self._on_response,
            on_tool_call=self._on_tool_call,
            on_thinking=self._on_thinking,
            on_error=self._on_error,
            on_step=self._on_step,
            on_clarify=self._on_clarify,
            on_complete=self._on_complete,
            on_approval=self._on_approval,
            on_reasoning=self._on_reasoning,
            on_stream_delta=self._on_stream_delta,
        )
        self._stream_bubble = None  # Active streaming bubble
        self._thinking_bubble = None  # Active thinking/reasoning bubble
        self._has_streamed = False   # True once any stream delta arrived

        self._build_menu()
        self._build_layout()

        # Register UI language change listener
        register_listener(self.update_ui_language)

        # First-run wizard — show if any required keys are missing
        missing = get_missing_keys()
        if any(s["required"] for s in missing):
            self.root.after(500, self._show_api_setup)

        model = self.bridge.get_model()
        self.status_bar.set_model(model)
        self.sidebar.set_model(model)

        # Show local settings if current model is local
        if self.bridge._is_local_model(model):
            self.sidebar._show_local_settings(True)

        # Show context-aware welcome message
        has_key = self.bridge._is_model_configured()
        if has_key:
            self._add_msg(
                t("chat.welcome_configured",
                  "Welcome to Portable Hermes Agent!\n"
                  "Type a message below and press Enter to chat.\n"
                  "Shift+Enter for newlines. Escape to interrupt."),
                "system"
            )
        else:
            self._add_msg(
                t("chat.welcome_guided",
                  "Welcome to Portable Hermes Agent!\n\n"
                  "No AI model is connected yet, but that's OK!\n"
                  "I'm running in guided mode — ask me anything and I'll "
                  "search the built-in guide for answers.\n\n"
                  "Try typing:\n"
                  "  • How do I get started?\n"
                  "  • What is OpenRouter?\n"
                  "  • How do I use local models?\n"
                  "  • What can Hermes do?\n\n"
                  "Or go to File > API Key Setup to connect an AI model."),
                "system"
            )

        # Notify user if we fell back from a local model
        if self.bridge._startup_fallback:
            orig = getattr(self.bridge, '_startup_original_model', 'local model')
            self._add_msg(
                t("chat.lm_fallback",
                  f"LM Studio not detected. Local model \"{orig}\" unavailable.\n"
                  f"Using {model} instead. Start LM Studio and select your local model from the dropdown to switch back.",
                  orig=orig, model=model),
                "system"
            )

        self.root.bind("<Control-n>", lambda e: self._new_chat())
        self.root.bind("<Control-comma>", lambda e: self._open_settings())
        self.root.bind("<Escape>", lambda e: self._interrupt())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---- Menu ----

    def _build_menu(self):
        # Custom dark menu bar (frame-based to avoid Windows white menu strip)
        if hasattr(self, 'menu_bar') and self.menu_bar.winfo_exists():
            for child in self.menu_bar.winfo_children():
                child.destroy()
        else:
            self.menu_bar = tk.Frame(self.root, bg=C["bg_sidebar"], height=S(28))
            self.menu_bar.pack(fill="x", side="top")
            self.menu_bar.pack_propagate(False)

        current_lang = get_language()

        # Build Language sub-items
        lang_items = []
        for code, name in SUPPORTED_LANGUAGES:
            prefix = "✓  " if code == current_lang else "    "
            lang_items.append((f"{prefix}{name}", lambda c=code: self._change_language(c)))

        for label, items in [
            (t("menu.file", "File"), [
                (t("menu.new_chat", "New Chat"), self._new_chat),
                None,
                (t("menu.api_setup", "API Key Setup"), self._show_api_setup),
                (t("menu.permissions", "Permissions"), self._open_permissions),
                (t("menu.settings", "Settings"), self._open_settings),
                None,
                (t("menu.exit", "Exit"), self._on_close),
            ]),
            (t("menu.view", "View"), [
                (t("menu.lm_studio", "LM Studio (Local Models)"), self._open_lm_studio),
                (t("menu.skills", "Skills Browser"), self._open_skills),
                (t("menu.extensions", "Extensions"), self._open_extensions),
                None,
                (t("menu.toggle_sidebar", "Toggle Sidebar"), self._toggle_sidebar),
            ]),
            (t("menu.language", "Language"), lang_items),
            (t("menu.help", "Help"), [
                (t("menu.about", "About"), self._about),
            ]),
        ]:
            btn = tk.Menubutton(self.menu_bar, text=f"  {label}  ",
                               font=FONTS["small"], fg=C["text_secondary"],
                               bg=C["bg_sidebar"], activebackground=C["bg_hover"],
                               activeforeground=C["text_primary"],
                               relief="flat", padx=4)
            btn.pack(side="left")

            menu = tk.Menu(btn, tearoff=0,
                          bg=C["bg_card"], fg=C["text_primary"],
                          activebackground=C["accent"], activeforeground="white",
                          relief="flat", borderwidth=1)
            for item in items:
                if item is None:
                    menu.add_separator()
                else:
                    menu.add_command(label=item[0], command=item[1])
            btn.configure(menu=menu)

    # ---- Layout ----

    def _build_layout(self):
        main = tk.Frame(self.root, bg=C["bg_main"])
        main.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = Sidebar(main, on_new=self._new_chat,
                               on_model_change=self._on_model_change,
                               on_session_select=self._on_session_select,
                               on_local_models=self._on_local_models_discovered,
                               on_auto_load=self._on_auto_load_status)
        self.sidebar.pack(side="left", fill="y")

        # Vertical separator
        tk.Frame(main, bg=C["separator"], width=1).pack(side="left", fill="y")

        # Chat area
        chat_area = tk.Frame(main, bg=C["bg_main"])
        chat_area.pack(side="left", fill="both", expand=True)

        # Chat header
        hdr = tk.Frame(chat_area, bg=C["bg_sidebar"], height=S(40))
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        self.chat_title = tk.Label(hdr, text=t("chat.new_chat_title", "New Chat"), font=FONTS["subheading"],
                                  fg=C["text_primary"], bg=C["bg_sidebar"])
        self.chat_title.pack(side="left", padx=16)

        # Stop button is created here but packed in the input area (next to Send)
        # so it doesn't overlap the chat. See btn_frame below.

        # Messages scroll area
        msg_outer = tk.Frame(chat_area, bg=C["bg_main"])
        msg_outer.pack(fill="both", expand=True)

        self.msg_canvas = tk.Canvas(msg_outer, bg=C["bg_main"],
                                    highlightthickness=0, borderwidth=0)
        self.msg_sb = ttk.Scrollbar(msg_outer, orient="vertical", command=self.msg_canvas.yview)
        self.msg_canvas.configure(yscrollcommand=self.msg_sb.set)

        self.msg_sb.pack(side="right", fill="y")
        self.msg_canvas.pack(side="left", fill="both", expand=True)

        self.msg_frame = tk.Frame(self.msg_canvas, bg=C["bg_main"])
        self._msg_win = self.msg_canvas.create_window((0, 0), window=self.msg_frame, anchor="nw")

        self.msg_frame.bind("<Configure>", lambda e: self.msg_canvas.configure(
            scrollregion=self.msg_canvas.bbox("all")))
        self.msg_canvas.bind("<Configure>", lambda e: self.msg_canvas.itemconfig(
            self._msg_win, width=e.width))

        # Mouse wheel
        def _mw(event):
            self.msg_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.msg_canvas.bind_all("<MouseWheel>", _mw, add="+")

        # Input area
        inp_outer = tk.Frame(chat_area, bg=C["bg_sidebar"], padx=16, pady=12)
        inp_outer.pack(fill="x")

        # Image attachment preview (hidden until images attached)
        self._attached_images = []
        self._attach_frame = tk.Frame(inp_outer, bg=C["bg_sidebar"])
        # Not packed initially — shown when images are attached

        inp_card = tk.Frame(inp_outer, bg=C["bg_input"],
                           highlightbackground=C["border"], highlightthickness=1)
        inp_card.pack(fill="x")

        self.input_text = tk.Text(inp_card, wrap="word",
                                 bg=C["bg_input"], fg=C["text_primary"],
                                 font=FONTS["body"], relief="flat", height=3,
                                 padx=12, pady=8, insertbackground=C["text_primary"],
                                 selectbackground=C["accent"], selectforeground="white",
                                 highlightthickness=0)
        self.input_text.pack(fill="both", expand=True)

        # Button row below the text input, separate from the text card
        btn_row = tk.Frame(inp_outer, bg=C["bg_sidebar"])
        btn_row.pack(fill="x", pady=(6, 0))

        self.attach_btn = ttk.Button(btn_row, text=t("chat.attach", "\U0001f4ce Attach"), width=8,
                                     command=self._attach_image)
        self.attach_btn.pack(side="left", padx=(0, 4))
        self.attach_tooltip = Tooltip(self.attach_btn, t("chat.attach_tooltip", "Attach image (Ctrl+Shift+I)"))

        self.send_btn = ttk.Button(btn_row, text=t("chat.send", "Send"), style="Primary.TButton",
                                   command=self._send)
        self.send_btn.pack(side="right", padx=(4, 0))
        self.send_tooltip = Tooltip(self.send_btn, t("chat.send_tooltip", "Send message (Enter)"))

        self.stop_btn = ttk.Button(btn_row, text=t("chat.stop", "Stop"), style="Danger.TButton",
                                   command=self._interrupt)
        self.stop_btn.pack(side="right", padx=(4, 0))
        self.stop_tooltip = Tooltip(self.stop_btn, t("chat.stop_tooltip", "Stop generation (Escape)"))

        self.root.bind("<Control-Shift-I>", lambda e: self._attach_image())

        self.input_text.bind("<Return>", self._on_enter)
        self.input_text.bind("<Shift-Return>", lambda e: None)
        self.input_text.focus_set()

        # Status bar
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill="x", side="bottom")

    # ---- Actions ----

    def _on_enter(self, event):
        if not (event.state & 0x1):  # no Shift
            self._send()
            return "break"

    def _attach_image(self):
        """Open file dialog to attach an image."""
        from tkinter import filedialog
        paths = filedialog.askopenfilenames(
            title="Attach Image",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("All files", "*.*"),
            ],
            parent=self.root,
        )
        if not paths:
            return

        for path in paths:
            if path not in self._attached_images:
                self._attached_images.append(path)

        self._update_attach_preview()

    def _remove_image(self, path):
        """Remove an attached image."""
        if path in self._attached_images:
            self._attached_images.remove(path)
        self._update_attach_preview()

    def _make_thumbnail(self, path, size=48):
        """Create a tk PhotoImage thumbnail from an image file."""
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            img.thumbnail((size, size), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except ImportError:
            return None  # Pillow not installed — fall back to text
        except Exception:
            return None

    def _update_attach_preview(self):
        """Show/hide attached image thumbnails."""
        # Clear existing preview and photo references
        for w in self._attach_frame.winfo_children():
            w.destroy()
        self._thumb_refs = []  # Keep references to prevent GC

        if not self._attached_images:
            self._attach_frame.pack_forget()
            return

        self._attach_frame.pack(fill="x", pady=(0, 6))

        for path in self._attached_images:
            chip = tk.Frame(self._attach_frame, bg=C["bg_card"],
                           highlightbackground=C["border"], highlightthickness=1,
                           padx=4, pady=4)
            chip.pack(side="left", padx=(0, 6))

            # Try to show actual thumbnail
            thumb = self._make_thumbnail(path)
            if thumb:
                self._thumb_refs.append(thumb)
                tk.Label(chip, image=thumb, bg=C["bg_card"]).pack(side="left", padx=(0, 4))

            fname = os.path.basename(path)
            if len(fname) > 18:
                fname = fname[:15] + "..."
            tk.Label(chip, text=fname, font=SF("Segoe UI", 8),
                    fg=C["text_secondary"], bg=C["bg_card"]).pack(side="left")

            rm_btn = tk.Label(chip, text=" \u2715", font=SF("Segoe UI", 9, "bold"),
                            fg=C["danger"], bg=C["bg_card"], cursor="hand2")
            rm_btn.pack(side="left")
            rm_btn.bind("<Button-1>", lambda e, p=path: self._remove_image(p))

    def _send(self):
        msg = self.input_text.get("1.0", "end-1c").strip()
        if not msg or self.bridge.is_running:
            return
        self.input_text.delete("1.0", "end")

        # Show attachments in the chat
        display = msg
        if self._attached_images:
            fnames = [os.path.basename(p) for p in self._attached_images]
            display = msg + "\n\U0001f4ce " + ", ".join(fnames)
        self._add_msg(display, "user")

        # Streaming bubble — shows tokens as they arrive
        self._stream_bubble = StreamingBubble(self.msg_frame)
        self._stream_bubble.pack(fill="x")
        self._has_streamed = False

        self.status_bar.set_thinking()

        # Send with images
        images = list(self._attached_images) if self._attached_images else None
        self._attached_images.clear()
        self._update_attach_preview()

        self.bridge.send_message(msg, image_paths=images)
        self._scroll_bottom()

    def _add_msg(self, text, msg_type, tool_name=None):
        w = MessageBubble(self.msg_frame, text, msg_type=msg_type, tool_name=tool_name)
        w.pack(fill="x")
        self._scroll_bottom()

    def _scroll_bottom(self):
        def _do_scroll():
            self.msg_canvas.update_idletasks()
            self.msg_canvas.configure(scrollregion=self.msg_canvas.bbox("all"))
            self.msg_canvas.yview_moveto(1.0)
        self.root.after(10, _do_scroll)

    # ---- Callbacks ----

    def _on_response(self, text):
        if self._stream_bubble:
            # Streaming bubble still alive — finalize it
            if self._stream_bubble.get_text().strip():
                self._stream_bubble.finalize()
            else:
                try:
                    self._stream_bubble.destroy()
                except tk.TclError:
                    pass
                # No streamed content — show full response as regular bubble
                if text and not self._has_streamed:
                    self._add_msg(text, "ai")
            self._stream_bubble = None
        elif text and not self._has_streamed:
            # Only show full response if we never streamed (non-streaming model/fallback)
            self._add_msg(text, "ai")

    def _on_tool_call(self, name, preview):
        if self._thinking_bubble:
            self._thinking_bubble.finalize()
            self._thinking_bubble = None
        self._cleanup_stream_bubble()
        w = ToolCallWidget(self.msg_frame, name, preview)
        w.pack(fill="x")
        self.status_bar.set_tool(name)
        # Start a new streaming bubble for the next response segment
        self._stream_bubble = StreamingBubble(self.msg_frame)
        self._stream_bubble.pack(fill="x")
        self._scroll_bottom()

    def _on_stream_delta(self, text):
        """Append a token to the streaming bubble."""
        if text is None:
            # End-of-turn signal — finalize the current bubble
            if self._thinking_bubble:
                self._thinking_bubble.finalize()
            if self._stream_bubble and self._stream_bubble.get_text().strip():
                self._stream_bubble.finalize()
                self._stream_bubble = None
            return
        if self._thinking_bubble:
            self._thinking_bubble.finalize()
        if self._stream_bubble:
            self._has_streamed = True
            self._stream_bubble.append_text(text)
            self._scroll_bottom()
            self.status_bar.set_thinking("Streaming")

    def _cleanup_stream_bubble(self):
        """Remove or finalize the active streaming bubble."""
        if self._thinking_bubble:
            self._thinking_bubble.finalize()
        if self._stream_bubble:
            if self._stream_bubble.get_text().strip():
                self._stream_bubble.finalize()
            else:
                try:
                    self._stream_bubble.destroy()
                except tk.TclError:
                    pass
            self._stream_bubble = None

    def _on_thinking(self, text):
        if text:
            self.status_bar.set_thinking(text)
        else:
            self.status_bar.set_ready()

    def _on_step(self, n, _):
        self.status_bar.set_iter(n)

    def _on_error(self, msg):
        self._cleanup_stream_bubble()
        self._add_msg(msg, "error")
        self.status_bar.set_error()

    def _on_clarify(self, question, choices=None):
        resp = simpledialog.askstring("Hermes needs input", question, parent=self.root)
        self.bridge.respond_to_clarify(resp or "")

    def _on_approval(self, command, description=None):
        """Dangerous command approval dialog."""
        msg = f"Hermes wants to run this command:\n\n{command}"
        if description:
            msg += f"\n\nReason: {description}"
        msg += "\n\nAllow this command?"
        approved = messagebox.askyesno("Command Approval", msg, parent=self.root)
        self.bridge.respond_to_approval(approved)

    def _on_reasoning(self, text):
        """Show model's reasoning in collapsible thinking box and status bar."""
        if text and text.strip():
            if not self._thinking_bubble or getattr(self._thinking_bubble, "_finalized", False):
                self._cleanup_stream_bubble()
                self._thinking_bubble = ThinkingBubble(self.msg_frame)
                self._thinking_bubble.pack(fill="x")
            self._thinking_bubble.append_reasoning(text)
            self._scroll_bottom()

            preview = text.strip().replace('\n', ' ')[:80]
            self.status_bar.set_thinking(f"Thinking: {preview}")

    def _on_complete(self, result):
        if self._thinking_bubble:
            self._thinking_bubble.finalize()
            self._thinking_bubble = None
        self._cleanup_stream_bubble()
        self.status_bar.set_ready()
        # Update token display if available
        tokens = self.bridge.get_token_usage()
        if tokens.get("total"):
            total = tokens["total"]
            self.status_bar.iter_lbl.configure(
                text=f"{total:,} tokens"
            )
        # Refresh session list
        try:
            self.sidebar.refresh_sessions()
        except Exception:
            pass

    # ---- Commands ----

    def _new_chat(self):
        if self._thinking_bubble:
            self._thinking_bubble = None
        self.bridge.new_session()
        for w in self.msg_frame.winfo_children():
            w.destroy()
        self.chat_title.configure(text="New Chat")
        self.status_bar.set_ready()
        self._add_msg("New session started.", "system")
        self.input_text.focus_set()
        self.sidebar.refresh_sessions()

    def _on_local_models_discovered(self, model_ids):
        """Called when sidebar discovers local models from LM Studio."""
        self.bridge.register_local_models(model_ids)

    def _on_auto_load_status(self, model_id, success, error):
        """Called when a local model auto-load completes."""
        if success:
            self._add_msg(f"Model loaded: {model_id}", "system")
        else:
            self._add_msg(f"Failed to load {model_id}: {error}", "error")

    def _on_model_change(self, model_id):
        """Called when user picks a model from the sidebar dropdown."""
        # Detect if this is a local model (known from LM Studio discovery)
        if model_id in self.bridge._known_local_models:
            url = self.bridge._resolve_lm_studio_url()
            if url:
                self.bridge.set_local_mode(url, model_id)
            else:
                self.bridge.set_model(model_id)
        else:
            self.bridge.set_model(model_id)

        # Persist selected model to config.yaml as default
        try:
            from hermes_cli.config import load_config, save_config
            cfg = load_config()
            if "model" not in cfg or not isinstance(cfg["model"], dict):
                cfg["model"] = {}
            cfg["model"]["default"] = model_id
            save_config(cfg)
        except Exception:
            pass

        # Show friendly name in status bar
        display = model_id
        for mid, name, note in self.sidebar._all_models:
            if mid == model_id:
                display = name
                break
        is_local = self.bridge._active_provider == "local"
        self.status_bar.set_model(f"LM Studio: {display}" if is_local else display)
        self._add_msg(f"Switched to {display}.", "system")

    def _on_session_select(self, session_id):
        """Load a past session into the chat view."""
        try:
            from hermes_state import SessionDB
            with SessionDB() as db:
                messages = db.get_messages_as_conversation(session_id)
            if not messages:
                self._add_msg("Could not load that session.", "error")
                return

            # Clear current chat
            for w in self.msg_frame.winfo_children():
                w.destroy()

            # Load conversation into bridge
            self.bridge.conversation_history = messages
            self.bridge.agent = None  # Force recreation
            self.chat_title.configure(text="Resumed Session")

            # Display messages
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if not content or role == "system":
                    continue
                if isinstance(content, list):
                    # Multi-part content (images, etc.)
                    content = " ".join(
                        p.get("text", "") for p in content
                        if isinstance(p, dict) and p.get("type") == "text"
                    )
                if role == "user":
                    self._add_msg(content, "user")
                elif role == "assistant":
                    if content:
                        self._add_msg(content, "ai")
                elif role == "tool":
                    # Skip tool results in replay
                    pass

            self._add_msg("Session resumed. You can continue the conversation.", "system")
            self.input_text.focus_set()

        except Exception as e:
            self._add_msg(f"Error loading session: {e}", "error")

    def _interrupt(self):
        if self.bridge.is_running:
            self.bridge.interrupt()
            self._cleanup_stream_bubble()
            self._add_msg("Generation stopped.", "system")
            self.status_bar.set_ready()

    def _open_settings(self):
        d = SettingsDialog(self.root, self.bridge)
        self.root.wait_window(d)
        m = self.bridge.get_model()
        self.status_bar.set_model(m)
        self.sidebar.set_model(m)

    def _open_skills(self):
        SkillsBrowser(self.root)

    def _open_permissions(self):
        PermissionsPanel(self.root, on_save=self._on_permissions_saved)

    def _on_permissions_saved(self, perms):
        self.bridge.agent = None  # Force agent recreation with new permissions
        self._add_msg("Permissions updated. Click '+ New Chat' to apply.", "system")

    def _open_extensions(self):
        ExtensionsManager(self.root)

    def _open_lm_studio(self):
        LMStudioPanel(self.root, on_model_ready=self._on_lm_studio_ready)

    def _on_lm_studio_ready(self, base_url, model_id):
        """Switch Hermes to use LM Studio as the LLM provider."""
        if model_id:
            self.bridge.set_local_mode(base_url, model_id)
            short = model_id.split("/")[-1] if "/" in model_id else model_id
            self.status_bar.set_model(f"LM Studio: {short}")
            self.sidebar.set_model(model_id)

        self._add_msg(
            f"Switched to LM Studio (local model).\n"
            f"Model: {model_id or 'default loaded model'}\n"
            f"Click '+ New Chat' to start using it.",
            "system"
        )

    def _show_api_setup(self):
        def on_done(saved_keys):
            if saved_keys:
                names = ", ".join(saved_keys.keys())
                self._add_msg(f"API keys saved: {names}\nNew tools are now available!", "system")
                # Force agent recreation to pick up new tools
                self.bridge.agent = None
            m = self.bridge.get_model()
            self.status_bar.set_model(m)
            self.sidebar.set_model(m)

        w = APISetupWizard(self.root, on_complete=on_done, auto_mode=True)
        self.root.wait_window(w)

    def _toggle_sidebar(self):
        if self.sidebar.winfo_viewable():
            self.sidebar.pack_forget()
        else:
            # Re-pack at left
            children = self.sidebar.master.winfo_children()
            self.sidebar.pack(side="left", fill="y", before=children[1] if len(children) > 1 else None)

    def _change_language(self, code: str):
        set_language(code)

    def update_ui_language(self, lang: str = None):
        """Dynamically update all UI labels to match active language."""
        self.root.title(t("app.title", "Portable Hermes Agent"))
        self._build_menu()

        if hasattr(self, 'sidebar'):
            self.sidebar.update_language()

        if hasattr(self, 'chat_title'):
            # If current chat is the default "New Chat", update its title
            if not getattr(self, '_current_session_id', None):
                self.chat_title.configure(text=t("chat.new_chat_title", "New Chat"))

        if hasattr(self, 'attach_btn'):
            self.attach_btn.configure(text=t("chat.attach", "\U0001f4ce Attach"))
        if hasattr(self, 'attach_tooltip'):
            self.attach_tooltip.text = t("chat.attach_tooltip", "Attach image (Ctrl+Shift+I)")

        if hasattr(self, 'send_btn'):
            self.send_btn.configure(text=t("chat.send", "Send"))
        if hasattr(self, 'send_tooltip'):
            self.send_tooltip.text = t("chat.send_tooltip", "Send message (Enter)")

        if hasattr(self, 'stop_btn'):
            self.stop_btn.configure(text=t("chat.stop", "Stop"))
        if hasattr(self, 'stop_tooltip'):
            self.stop_tooltip.text = t("chat.stop_tooltip", "Stop generation (Escape)")

        if hasattr(self, 'status_bar'):
            self.status_bar.update_language()

    def _about(self):
        AboutDialog(self.root)

    def _on_close(self):
        if self.bridge.is_running:
            if not messagebox.askyesno(t("app.title", "Portable Hermes Agent"),
                                       t("app.exit_confirm", "Agent is still running. Exit anyway?"),
                                       parent=self.root):
                return
        self.bridge.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    HermesGUI().run()


if __name__ == "__main__":
    main()
