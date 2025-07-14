# LocalAI-GUI
A sleek PyQt6-powered local ChatGPT UI using Ollama, with support for streaming, code highlighting, and persistent conversations.
# 💻 LocalAI-GUI

A sleek, offline ChatGPT-style desktop app using **Ollama** and **PyQt6**.  
This app lets you interact with local LLMs in real-time with chat history, markdown/code highlighting, and full control over UI.

---

## ✨ Features

- ✅ PyQt6-based modern GUI
- ✅ Local LLM inference via [Ollama](https://ollama.com)
- ✅ Real-time streaming of model responses
- ✅ Syntax highlighting for code blocks
- ✅ Persistent multi-chat storage (as JSON)
- ✅ Font size settings & dark theme
- ✅ "Stop" button to interrupt long replies
- ✅ Lightweight and private (no cloud dependency)

---

## 🧰 Technologies Used

- Python 3.10+
- PyQt6
- Ollama (local LLM backend)
- HTML formatting & JSON storage

---

## 📸 Screenshot

*(Insert screenshot of your app UI here)*

---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/erfan-8/LocalAI-GUI.git
cd LocalAI-GUI
```

# 2. Create and Activate a Virtual Environment
python -m venv .venv
# Activate it:
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

#3. Install Dependencies
pip install -r requirements.txt

# Or manually:
pip install PyQt6 requests

# **🧠 Setting up Ollama
To run local models like Mistral, LLaMA2, etc., install and use Ollama:

# Install and run a model:
ollama run mistral
Make sure Ollama is running at http://localhost:11434 (default port).

# ▶️ Run the App
python main10.py

# 💾 Chat History
##All conversations are saved as .json files inside the chats/ directory.
##They will be reloaded when the app is opened again.

# 📁 Project Structure
LocalAI-GUI/
├── main.py              # Main PyQt6 application
├── chats/               # Saved chat sessions
├── README.md
└── requirements.txt     # Project dependencies
#🔮 Future Plans (Optional Ideas)
Chat export to PDF/Markdown

Whisper integration (voice input)

Plugin system (calculator, browser, etc.)

Light/Dark mode toggle

Token/usage counter

#🧑‍💻 Author
Developed with ❤️ by @erfan-8
Feel free to fork, contribute, and customize.
