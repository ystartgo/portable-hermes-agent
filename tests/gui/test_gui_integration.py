"""
Integration test for HermesGUI multi-language switching.
"""
import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk
from gui.i18n import t, set_language, get_language


class TestGuiIntegration(unittest.TestCase):

    def test_gui_texts_on_language_change(self):
        root = tk.Tk()
        root.withdraw()

        try:
            # Check switching to zh-hant
            set_language("zh-hant", persist=False)
            self.assertEqual(t("menu.file"), "檔案")
            self.assertEqual(t("menu.view"), "檢視")
            self.assertEqual(t("menu.language"), "語言")
            self.assertEqual(t("menu.help"), "說明")
            self.assertEqual(t("menu.new_chat"), "新對話")
            self.assertEqual(t("menu.settings"), "設定")
            self.assertEqual(t("menu.exit"), "結束")
            self.assertEqual(t("sidebar.new_chat"), "+ 新對話")
            self.assertEqual(t("sidebar.recent_sessions"), "最近對話")
            self.assertEqual(t("chat.attach"), "📎 附件")
            self.assertEqual(t("chat.send"), "發送")
            self.assertEqual(t("chat.stop"), "停止")
            self.assertEqual(t("status.ready"), "就緒")
            self.assertEqual(t("settings.title"), "設定")
            self.assertEqual(t("settings.language"), "介面語言")

            # Check switching to zh
            set_language("zh", persist=False)
            self.assertEqual(t("menu.file"), "文件")
            self.assertEqual(t("menu.view"), "视图")
            self.assertEqual(t("menu.language"), "语言")
            self.assertEqual(t("menu.help"), "帮助")
            self.assertEqual(t("menu.new_chat"), "新建对话")
            self.assertEqual(t("menu.settings"), "设置")
            self.assertEqual(t("menu.exit"), "退出")
            self.assertEqual(t("sidebar.new_chat"), "+ 新建对话")
            self.assertEqual(t("sidebar.recent_sessions"), "最近对话")
            self.assertEqual(t("chat.attach"), "📎 附件")
            self.assertEqual(t("chat.send"), "发送")
            self.assertEqual(t("chat.stop"), "停止")
            self.assertEqual(t("status.ready"), "就绪")
            self.assertEqual(t("settings.title"), "设置")
            self.assertEqual(t("settings.language"), "界面语言")

            # Check switching to en
            set_language("en", persist=False)
            self.assertEqual(t("menu.file"), "File")
            self.assertEqual(t("menu.view"), "View")
            self.assertEqual(t("menu.language"), "Language")
            self.assertEqual(t("menu.help"), "Help")
            self.assertEqual(t("menu.new_chat"), "New Chat")
            self.assertEqual(t("menu.settings"), "Settings")
            self.assertEqual(t("menu.exit"), "Exit")
            self.assertEqual(t("sidebar.new_chat"), "+ New Chat")
            self.assertEqual(t("sidebar.recent_sessions"), "Recent Sessions")
            self.assertEqual(t("chat.attach"), "📎 Attach")
            self.assertEqual(t("chat.send"), "Send")
            self.assertEqual(t("chat.stop"), "Stop")
            self.assertEqual(t("status.ready"), "Ready")
            self.assertEqual(t("settings.title"), "Settings")
            self.assertEqual(t("settings.language"), "Interface Language")
        finally:
            root.destroy()

    def test_custom_models_crud(self):
        from gui.app import add_custom_model, update_custom_model, remove_custom_model, get_custom_models
        model_test = "test-model-xyz"
        model_renamed = "test-model-abc"

        # Add
        added = add_custom_model(model_test)
        self.assertTrue(added)
        self.assertIn(model_test, get_custom_models())

        # Update
        updated = update_custom_model(model_test, model_renamed)
        self.assertTrue(updated)
        self.assertIn(model_renamed, get_custom_models())
        self.assertNotIn(model_test, get_custom_models())

        # Remove
        removed = remove_custom_model(model_renamed)
        self.assertTrue(removed)
        self.assertNotIn(model_renamed, get_custom_models())

    def test_custom_endpoints_crud(self):
        from gui.app import (
            add_custom_endpoint,
            delete_custom_endpoint,
            activate_custom_endpoint,
            get_custom_endpoints,
        )
        ep = add_custom_endpoint("Test Endpoint", "https://api.test.com/v1", "sk-test", "auto")
        self.assertEqual(ep["name"], "Test Endpoint")
        self.assertEqual(ep["base_url"], "https://api.test.com/v1")

        endpoints = get_custom_endpoints()
        self.assertTrue(any(e.get("name") == "Test Endpoint" for e in endpoints))

        activated = activate_custom_endpoint(ep)
        self.assertTrue(activated)
        self.assertEqual(os.environ.get("OPENAI_BASE_URL"), "https://api.test.com/v1")
        self.assertEqual(os.environ.get("OPENAI_API_KEY"), "sk-test")

        deleted = delete_custom_endpoint(ep["id"])
        self.assertTrue(deleted)
        self.assertFalse(any(e.get("id") == ep["id"] for e in get_custom_endpoints()))

    def test_thinking_bubble_and_tool_call_widgets(self):
        root = tk.Tk()
        root.withdraw()
        try:
            from gui.app import ThinkingBubble, ToolCallWidget
            frame = tk.Frame(root)
            frame.pack()

            # ThinkingBubble
            tb = ThinkingBubble(frame)
            tb.pack()
            self.assertTrue(tb._expanded)
            tb.append_reasoning("Step 1: analyzing user query.\n")
            tb.append_reasoning("Step 2: evaluating available tools.\n")
            self.assertIn("Step 1", tb.get_text())

            # Toggle collapse
            tb.toggle()
            self.assertFalse(tb._expanded)
            tb.toggle()
            self.assertTrue(tb._expanded)
            tb.finalize()
            self.assertTrue(tb._finalized)

            # ToolCallWidget
            tw = ToolCallWidget(frame, "web_search", "query='Hermes Agent'")
            tw.pack()
            self.assertFalse(tw._expanded)
            tw.toggle()
            self.assertTrue(tw._expanded)
            tw.toggle()
            self.assertFalse(tw._expanded)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()

