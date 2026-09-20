# 🧪 Intelligent Test Case Generation Agent

An AI-powered tool that automatically generates comprehensive test cases from **code snippets** or **feature descriptions**. Built with **Gradio** for the GUI and **Groq** for blazing-fast LLM inference.

> **CA-3 Mini Project**

---

## ✨ Features

| Feature | Description |
|---|---|
| **Code Analysis** | Paste source code and get executable unit tests |
| **Feature Descriptions** | Describe a feature and get structured manual test cases |
| **Multi-Language** | Supports Python, Java, JavaScript, C++, Go, Rust, and more |
| **Framework Aware** | Generates tests for pytest, JUnit, Jest, Google Test, etc. |
| **Multiple Models** | Choose from Llama 3.3 70B, Mixtral 8x7B, Gemma 2 9B, and more |
| **Secure** | Your API key is never stored — used only for the current session |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- A free [Groq API key](https://console.groq.com/keys)

### Installation

```bash
# Clone or navigate to the project directory
cd test_case_generator

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
python app.py
```

The Gradio interface will open in your default browser at `http://127.0.0.1:7860`.

---

## 🖥️ Usage

1. **Enter your Groq API Key** in the password field.
2. **Select Input Type** — *Code Snippet* or *Feature Description*.
3. **Paste your code** or **describe the feature** in the text area.
4. (For code) Choose the **Programming Language** and **Testing Framework**.
5. Click **🚀 Generate Test Cases**.
6. View and copy the generated test cases from the output panel.

---

## 🛠️ Tech Stack

- **Frontend / GUI**: [Gradio](https://www.gradio.app/)
- **LLM Backend**: [Groq Cloud API](https://console.groq.com/)
- **Language**: Python

---

## 📁 Project Structure

```
test_case_generator/
├── app.py              # Main Gradio application
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation (this file)
```

---

## 📄 License

This project is for educational purposes (CA-3 Mini Project).
