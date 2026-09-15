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


if __name__ == "__main__":
    unittest.main()
