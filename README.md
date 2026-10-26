# Crux AI — Executive Video Intelligence & Interactive RAG Chat

[![Repository](https://img.shields.io/badge/GitHub-pragyanshdixit%2FCrux--AI-blue.svg?logo=github)](https://github.com/pragyanshdixit/Crux-AI.git)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/LLM%20%26%20STT-Groq%20Cloud%20LPU-f55036.svg)](https://groq.com)
[![Whisper](https://img.shields.io/badge/STT-Whisper%20Large%20v3%20Turbo-412991.svg)](https://github.com/openai/whisper)
[![Chroma](https://img.shields.io/badge/RAG-ChromaDB%20%2B%20MiniLM-orange.svg)](https://www.trychroma.com)

**Crux AI** transforms videos, local media files, and transcripts into high-density, structured executive intelligence in **under 8 seconds**. It automatically extracts core takeaways, prioritized action checklists, and key strategic decisions, and spins up an interactive, context-grounded RAG chat for follow-up questions.

---

## 🌟 Core Input Modes

Crux AI supports 3 flexible input modalities to ensure 100% reliable processing in any environment:

| Mode | Icon | Description | Ideal For |
| :--- | :---: | :--- | :--- |
| **YouTube URL** | 🔗 | Extracts official YouTube transcripts in ~0.2s or streams audio via `yt-dlp` through Groq Whisper LPU. | Quick analysis of online videos, tutorials, tech talks. |
| **Local Upload** | 📁 | Drag & drop or browse `.mp4`, `.mov`, `.mkv`, `.webm`, `.avi`, `.mp3`, `.wav`, `.m4a` files. Extracted with FFmpeg. | Offline recordings, Zoom meetings, local screen captures. |
| **Paste Transcript** | 📝 | Direct text synthesis without audio processing. Completely bypasses network and IP restrictions. | Meeting minutes, podcast transcripts, YouTube "Show transcript" copies. |

---

## ⚡ Key Architectural Features & Optimizations

### 1. Ultra-Fast Execution Speed (<8s Total)
- **Groq Whisper Large v3 Turbo**: Replaced slow CPU-bound local transcription with cloud-hosted Whisper running on Groq LPUs. Transcribes 30–60 minutes of audio in **~1 to 2 seconds** (50x–100x speedup!).
- **Lightweight Audio Normalization**: Automatically extracts 16kHz mono 96kbps MP3 audio payloads, keeping files well within Groq's 25MB threshold.
- **Zero-Chunk Direct Pipeline**: Single-pass transcription without cutting audio into arbitrary slices for recordings under 24MB.

### 2. High-Capacity Single-Pass Intelligence
- **Unified Insight Synthesis**: Leverages high-capacity Groq LLMs (`openai/gpt-oss-120b`) in native JSON mode. Generates title, executive summary, action checklist, decisions, and questions in **1 single API call**.
- **Context-Grounded Interactive RAG**: Indexes transcript into isolated ChromaDB vector collections with local `all-MiniLM-L6-v2` embeddings ($0 API cost). Prunes retrieval to top `k=3` relevant chunks for fast, hallucination-free answers.

### 3. "Bring Your Own Key" (BYOK) Flexibility
- **Browser-Side Key Storage**: Users can enter their own Groq API key via the top-bar modal. Stored securely in `localStorage` and sent per request.
- **In-App Live Key Verification**: 1-click test button verifies key status directly against Groq Cloud before running any queries.

### 4. Zero Disk Leakage & Auto-Cleanup
- **Temporary Storage Isolation**: Files are saved under `downloads/session_<session_id>/` and automatically purged immediately after Whisper transcription completes.
- **Disk Purge Endpoint**: Includes `/api/purge-downloads` and an in-app "Clean Cache" button to safely free disk space on serverless or container hosts.

---

## 🚀 Step-by-Step Guide to Run Locally

### Prerequisites
Make sure you have the following installed on your machine:
1. **Python 3.10+** (Tested on Python 3.11, 3.12, 3.13)
2. **FFmpeg** (Required for audio extraction from video files):
   - **Windows**: Install via `winget install Gyan.FFmpeg` or `choco install ffmpeg`, or download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to your `PATH`.
   - **macOS**: `brew install ffmpeg`
   - **Linux (Ubuntu/Debian)**: `sudo apt update && sudo apt install -y ffmpeg`
3. **Node.js** (Optional, helps `yt-dlp` solve YouTube JavaScript player challenges)
4. A free **Groq Cloud API Key** from [console.groq.com](https://console.groq.com)

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/pragyanshdixit/Crux-AI.git
cd Crux-AI
```

### Step 2: Set Up a Python Virtual Environment

#### On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### On Windows (Command Prompt):
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

#### On macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

---

### Step 4: Configure Environment Variables
Create a `.env` file in the project root directory:

```env
GROQ_API_KEY=gsk_your_groq_api_key_here
PORT=8000
```

> **Note**: Even if you don't set `GROQ_API_KEY` in `.env`, you can enter your API key directly in the web UI using the "API Key" button at the top right!

---

### Step 5: Start the Crux AI Application

#### Option A: Web Application (FastAPI Server)
```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```
*(Or simply run `python app.py`)*

Now open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

You will see the Crux AI interface with:
- **YouTube Link**: Paste any YouTube URL for instant synthesis.
- **📁 Upload Video / Audio**: Drag and drop any local video or audio file.
- **Paste Transcript / Notes**: Paste transcript text directly.
- **Interactive RAG Chat**: Ask questions grounded in the video context.

---

#### Option B: Terminal CLI Mode
To analyze a video directly from your command line:
```bash
python main.py
```
1. Enter your YouTube link or local file path when prompted.
2. View synthesized executive summary, actionable tasks, and key decisions directly in the terminal.
3. Chat interactively with the video context.

---

#### Option C: Docker / Docker Compose
Run Crux AI in an isolated container with all system dependencies pre-configured:
```bash
# Set your Groq key
echo "GROQ_API_KEY=gsk_your_groq_key_here" > .env

# Build and start container
docker compose up -d
```
Access the application at **`http://localhost:8000`**.

---

## 🔌 API Reference

| Method | Endpoint | Description |
| :---: | :--- | :--- |
| `GET` | `/` | Serves the Crux AI modern web interface. |
| `GET` | `/api/health` | Health check endpoint returning server status and active sessions. |
| `POST` | `/api/verify-key` | Verifies a user-provided Groq API key in real-time. |
| `POST` | `/api/process` | Processes a YouTube URL or direct text transcript. |
| `POST` | `/api/upload-process` | **New**: Uploads a local video/audio file (`multipart/form-data`) and extracts intelligence. |
| `POST` | `/api/chat` | Interactive RAG Q&A grounded strictly in the session transcript. |
| `POST` | `/api/purge-downloads` | Frees disk space by clearing temporary downloads and audio files. |

---

## 🛠️ Project Architecture

```
Crux-AI/
├── app.py                      # FastAPI server & REST API endpoints
├── main.py                     # Interactive Terminal CLI interface
├── index.html                  # Root HTML frontend (Vercel deployment target)
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Production container definition
├── docker-compose.yml          # Container orchestration
├── render.yaml                 # Render cloud configuration
├── vercel.json                 # Vercel deployment & proxy rules
│
├── core/
│   ├── extractor.py            # Single-pass Groq LLM structured insights extractor
│   ├── rag_engine.py           # Context retrieval and conversational Q&A chain
│   ├── transcriber.py          # Groq Whisper LPU speech-to-text integration
│   └── vector_store.py         # ChromaDB client & local embeddings manager
│
├── utils/
│   └── audio_preprocessing.py  # Media conversion, YouTube extraction & audio chunking
│
└── static/
    ├── index.html              # Modern Web Dashboard interface
    ├── css/style.css           # Vanilla CSS styling, light theme & animations
    └── js/app.js               # Frontend application logic, telemetry & state
```

---

## 🛡️ License
MIT License. Built with open-source tools for high-efficiency video intelligence.