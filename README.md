# 🚀 Getting Started

## Prerequisites

Before running the project, ensure you have installed:

- Python 3.10 or later
- Git
- Tesseract OCR
- PyTorch (Required by EasyOCR; automatically installed via pip)

### Install Tesseract OCR

**Windows**

Download and install from:

https://github.com/UB-Mannheim/tesseract/wiki

After installation, update the path in `frontend.py` if necessary:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

For Linux:

```bash
sudo apt update
sudo apt install tesseract-ocr
```

For macOS:

```bash
brew install tesseract
```

---

# 📥 Clone the Repository

```bash
git clone https://github.com/shaunbny/PhishShield-AI.git

cd PhishShield-AI
```

---

# 🐍 Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

# 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

If a `requirements.txt` file is not available, install the required packages manually:

```bash
pip install fastapi uvicorn gradio requests pillow pytesseract easyocr python-dotenv groq langchain langchain-core langchain-community langchain-huggingface langchain-text-splitters langchain-groq faiss-cpu sentence-transformers
```

> **Note on EasyOCR:** The very first time you process an image, EasyOCR will automatically download its pre-trained detection and recognition model weights. This might take a few moments depending on your network speed.

---

# 🔑 Configure Environment Variables

Create a file named `.env` in the project root.

```env
GROQ_API_KEY=YOUR_GROQ_API_KEY
BACKEND_URL=http://127.0.0.1:8000/api/analyze
```

You can obtain a free Groq API key from:

https://console.groq.com/keys

---

# ▶ Running the Application

## Step 1 — Start the Backend

Open a terminal inside the project folder.

```bash
python backend.py
```

If successful, you should see something similar to:

SUCCESS: Balanced RAG core pipeline built successfully!Uvicorn running on http://127.0.0.1:8000

Leave this terminal running.

---

## Step 2 — Start the Frontend

Open another terminal.

Navigate to the project folder.

Activate the virtual environment again if necessary.

Run:
```bash
python frontend.py
```

The application will launch at:

http://127.0.0.1:7860
Open the URL in your browser.
# 🧪 Using PhiShield AI

The application accepts multiple input types:

- Paste suspicious URLs
- Paste email or SMS text
- Upload screenshots for OCR analysis (Powered by EasyOCR and Tesseract)
- Upload or record voice notes

Click **Analyze Security Legitimacy** to receive:

- Threat classification
- AI reasoning
- Recommended actions
- Official reporting channels
- ---

# 🛑 Stopping the Application

To stop the application, press:

CTRL + C
in both terminal windows.
---

# 🔄 Updating the Project

```bash
git pull

pip install -r requirements.txt
```
