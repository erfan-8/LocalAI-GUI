import sys
import os
import json
import requests
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QComboBox, QFrame,
    QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import  QFont, QTextCursor


from PyQt6.QtWidgets import QTextEdit
OLLAMA_URL = "http://localhost:11434"
SAVE_DIR = "chats"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QKeyEvent

class InputTextEdit(QTextEdit):
    send_requested = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (
                event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.send_requested.emit()
        else:
            super().keyPressEvent(event)


class StreamWorker(QThread):
    chunk_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    finished_cleanly = pyqtSignal(object)

    def __init__(self, model: str, prompt: str):
        super().__init__()
        self.model = model
        self.prompt = prompt
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def run(self):
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": self.model, "prompt": self.prompt, "stream": True},
                stream=True,
                timeout=10  # زمان انتظار برای جلوگیری از گیر کردن
            )
            if response.status_code != 200:
                self.error_occurred.emit(response.text)
                return

            for line in response.iter_lines():
                if self._stop_flag:
                    break
                if line:
                    data = json.loads(line.decode('utf-8'))
                    content = data.get("response", "")
                    self.chunk_received.emit(content)
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.finished_cleanly.emit(self)


class ChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Erfan's ChatGPT (Enhanced)")
        self.resize(1100, 700)
        self.setStyleSheet("background-color: #0d1117; color: white;")

        self.chats = {}
        self.current_chat = None
        self.active_workers = []

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #d29922; padding: 4px;")

        self.init_ui()
        self.load_saved_chats()


    def init_ui(self):
        main = QWidget()
        self.setCentralWidget(main)
        layout = QHBoxLayout(main)

        # Sidebar (لیست گفتگوها)
        sidebar = QVBoxLayout()
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("background-color: #161b22; color: white; border: none;")
        self.chat_list.itemClicked.connect(self.load_chat)

        self.new_chat_btn = QPushButton("+ New Chat")
        self.new_chat_btn.clicked.connect(self.new_chat)
        self.new_chat_btn.setStyleSheet(self.button_style())

        self.delete_chat_btn = QPushButton("🗑 Delete Chat")
        self.delete_chat_btn.clicked.connect(self.delete_chat)
        self.delete_chat_btn.setStyleSheet(self.button_style())

        sidebar.addWidget(QLabel("  💬 Conversations"))
        sidebar.addWidget(self.chat_list)
        sidebar.addWidget(self.new_chat_btn)
        sidebar.addWidget(self.delete_chat_btn)


        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setStyleSheet("background-color: #30363d;")
        line.setLineWidth(1)

        # Right pane
        right = QVBoxLayout()

        # مدل انتخاب
        self.model_selector = QComboBox()
        self.model_selector.addItems(self.get_models())
        self.model_selector.setStyleSheet("""
            QComboBox {
                background-color: #161b22;
                color: #58a6ff;
                padding: 6px;
                border-radius: 5px;
            }
        """)


        self.font_selector = QComboBox()
        self.font_selector.addItems(["10", "11", "12", "13", "14", "15"])
        self.font_selector.setCurrentText("11")
        self.font_selector.currentTextChanged.connect(self.change_font_size)
        self.font_selector.setStyleSheet("background-color: #161b22; color: white; padding: 4px;")

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Model:"))
        top_bar.addWidget(self.model_selector)
        top_bar.addStretch()
        top_bar.addWidget(QLabel("Font Size:"))
        top_bar.addWidget(self.font_selector)

        # نمایش چت(show chat)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background-color: #0d1117; color: white; padding: 10px; border: none;")
        self.chat_display.setFont(QFont("Consolas", 11))

        self.input = InputTextEdit()
        self.input.send_requested.connect(self.send_message)
        self.input.setPlaceholderText("Ask something...")
        self.input.setFixedHeight(100)
        self.input.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.input.setStyleSheet(
            "background-color: #161b22; color: white; padding: 10px; border-radius: 5px;"
        )

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setStyleSheet(self.button_style())

        bottom_bar = QHBoxLayout()
        bottom_bar.addWidget(self.input)
        bottom_bar.addWidget(self.send_btn)

        self.stop_btn = QPushButton("🛑 Stop")
        self.stop_btn.clicked.connect(self.stop_all_workers)
        self.stop_btn.setStyleSheet(self.button_style())
        bottom_bar.addWidget(self.stop_btn)

        right.addWidget(self.status_label)
        right.addLayout(top_bar)
        right.addWidget(self.chat_display)
        right.addLayout(bottom_bar)

        layout.addLayout(sidebar, 2)
        layout.addWidget(line)
        layout.addLayout(right, 5)

    def button_style(self):
        return """
            QPushButton {
                background-color: #238636;
                color: white;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2ea043;
                color: #ffffff;
            }
        """

    def change_font_size(self, size):
        self.chat_display.setFont(QFont("Consolas", int(size)))

    def new_chat(self):
        name, ok = QInputDialog.getText(self, "New Chat", "Enter a name for this chat:")
        if not ok or not name.strip():
            return
        if name in self.chats:
            QMessageBox.warning(self, "Duplicate", "Chat name already exists.")
            return
        self.chats[name] = []
        self.chat_list.addItem(name)
        self.chat_list.setCurrentRow(self.chat_list.count() - 1)
        self.current_chat = name
        self.chat_display.clear()
        self.save_chat(name)

    def delete_chat(self):
        row = self.chat_list.currentRow()
        if row < 0:
            return
        name = self.chat_list.currentItem().text()
        confirm = QMessageBox.question(self, "Delete Chat", f"Delete '{name}'?")
        if confirm == QMessageBox.StandardButton.Yes:
            self.chat_list.takeItem(row)
            del self.chats[name]
            path = os.path.join(SAVE_DIR, f"{name}.json")
            if os.path.exists(path):
                os.remove(path)
            self.chat_display.clear()
            self.current_chat = None

    def load_chat(self, item):
        name = item.text()
        self.current_chat = name
        self.chat_display.clear()
        for role, msg in self.chats.get(name, []):
            if role == "user":
                self.display_message("user", msg)
            elif role == "ai":
                self.temp_ai_message = msg  # این لازم نیست ولی برای هماهنگی خوبه
                cursor = self.chat_display.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)

                if msg.count("```") % 2 == 0 and "```" in msg:
                    html = self.format_code_blocks(msg)
                    cursor.insertHtml(f"<p style='color:#ffa657'><b>AI:</b> {html}</p>")
                else:
                    self.display_message("ai", msg)

    def send_message(self):
        prompt = self.input.toPlainText().strip()
        if not prompt or not self.current_chat:
            return
        self.input.clear()

        if self.current_chat not in self.chats:
            self.chats[self.current_chat] = []
        self.chats[self.current_chat].append(("user", prompt))
        self.save_chat(self.current_chat)  # ✅ ذخیره فوری

        self.display_message("user", prompt)
        self.display_message("ai", "")

        model = self.model_selector.currentText()
        self.temp_ai_message = ""  # برای ذخیره پیام کامل AI

        worker = StreamWorker(model, prompt)
        worker.chunk_received.connect(self.append_stream_chunk)
        worker.error_occurred.connect(self.handle_error)
        worker.finished_cleanly.connect(self.clean_worker)
        self.active_workers.append(worker)
        worker.start()

        self.stop_btn.setEnabled(True)
        self.status_label.setText("🧠 Model is running...")

    def display_message(self, role, msg):
        if role == "user":
            self.chat_display.append(f"<p style='color:#58a6ff'><b>You:</b> {msg}</p>")
        elif role == "ai":
            self.chat_display.append(f"<p style='color:#ffa657'><b>AI:</b> </p>")
        else:
            self.chat_display.append(f"<p>{msg}</p>")

    def append_stream_chunk(self, text):
        self.temp_ai_message += text
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)

        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # اگر بلاک کد کامل شده (تعداد ``` زوج شده)
        if self.temp_ai_message.count("```") % 2 == 0 and "```" in self.temp_ai_message:
            # پاک کردن آخرین پیام AI در چت‌ویو
            self.remove_last_ai_message()

            # درج نسخه HTML شده
            html = self.format_code_blocks(self.temp_ai_message)
            cursor.insertHtml(f"<p style='color:#ffa657'><b>AI:</b> {html}</p>")
        else:
            cursor.insertText(text)

        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )
        self.chats[self.current_chat][-1] = ("ai", self.temp_ai_message)
        self.save_chat(self.current_chat)

    def format_code_blocks(self, text):
        # جدا کردن کد بلاک‌ها و خط‌شکنی
        parts = re.split(r"(```.*?```)", text, flags=re.DOTALL)
        out = ""
        for part in parts:
            if part.startswith("```") and part.endswith("```"):
                code = part.strip("```")
                code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                code = code.replace("\n", "<br>")
                out += f"<pre style='background:#161b22;padding:10px;border-radius:5px;color:#dcdcdc;'>{code}</pre>"
            else:
                safe = part.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                safe = safe.replace("\n", "<br>")
                out += safe
        return out

    def handle_error(self, error):
        self.chat_display.append(f"<p style='color:red'>[Error] {error}</p>")

    def remove_last_ai_message(self):
        doc = self.chat_display.document()
        block = doc.lastBlock()

        # عقب می‌ریم تا جایی که پیام AI قبلی تمام شده
        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # چند خط آخر رو پاک می‌کنیم چون پیام موقتی AI اینجاست
        for _ in range(20):
            cursor.movePosition(QTextCursor.MoveOperation.PreviousBlock, QTextCursor.MoveMode.KeepAnchor)
            if "<b>AI:</b>" in cursor.selection().toHtml():
                break

        cursor.removeSelectedText()
        cursor.deletePreviousChar()

    def clean_worker(self, worker):
        self.status_label.setText("")
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        if not self.active_workers:
            self.stop_btn.setEnabled(False)

    def get_models(self):
        try:
            res = requests.get(f"{OLLAMA_URL}/api/tags")
            if res.status_code == 200:
                return [m["name"] for m in res.json().get("models", [])]
        except:
            pass
        return ["mistral"]

    def save_chat(self, name):
        path = os.path.join(SAVE_DIR, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.chats[name], f, indent=2, ensure_ascii=False)

    def load_saved_chats(self):
        for filename in os.listdir(SAVE_DIR):
            if filename.endswith(".json"):
                name = filename[:-5]
                path = os.path.join(SAVE_DIR, filename)
                with open(path, "r", encoding="utf-8") as f:
                    self.chats[name] = json.load(f)
                    self.chat_list.addItem(name)

        # 👇 بعد از لود همه چت‌ها، اولین چت رو لود کن
        if self.chat_list.count() > 0:
            self.chat_list.setCurrentRow(0)
            self.load_chat(self.chat_list.item(0))

    def stop_all_workers(self):
        for worker in self.active_workers:
            worker.stop()
            worker.wait()  # صبر کن تا thread کامل بسته بشه
        self.active_workers.clear()

    def closeEvent(self, event):
        self.stop_all_workers()
        event.accept()


if __name__ == "__main__":
    os.environ["QT_OPENGL"] = "software"
    app = QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec())

