"""Crux AI FastAPI Application.
Exposes endpoints for video intelligence processing, RAG chat, Groq key verification,
and production storage lifecycle maintenance.
"""

import os
import sys
import uuid
import time
from typing import Optional
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from utils.audio_preprocessing import process_input, purge_all_downloads
from core.transcriber import transcribe_chunks
from core.extractor import extract_all_insights
from core.rag_engine import build_rag_chain, ask_question

app = FastAPI(
    title="Crux AI API",
    description="Crux AI — Executive intelligence, summaries, decisions, action items, and interactive RAG Q&A from video streams.",
    version="2.1.0"
)

# In-memory store for video sessions (stores RAG chain and extracted metadata)
SESSIONS: dict[str, dict] = {}


class ProcessRequest(BaseModel):
    url: str
    auto_cleanup: bool = True
    api_key: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str
    api_key: Optional[str] = None


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "Crux AI",
        "active_sessions": len(SESSIONS)
    }


@app.post("/api/verify-key")
def verify_api_key(payload: dict):
    """Test and validate a user-provided Groq API key."""
    key = payload.get("api_key", "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="API key is empty.")
    try:
        from groq import Groq
        client = Groq(api_key=key)
        client.models.list()
        return {"valid": True, "message": "Groq API key verified successfully."}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"valid": False, "message": f"Invalid key or Groq error: {str(e)}"}
        )


@app.post("/api/process")
def process_video(req: ProcessRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Please provide a valid YouTube URL.")

    effective_api_key = (req.api_key.strip() if req.api_key else None) or os.getenv("GROQ_API_KEY")
    if not effective_api_key:
        raise HTTPException(
            status_code=400,
            detail="Groq API key required. Please enter your API key via the settings button or configure GROQ_API_KEY in .env"
        )

    session_id = uuid.uuid4().hex[:10]
    start_time = time.time()

    try:
        # Step 1: Download & Preprocess (ultrafast lightweight mp3)
        chunks = process_input(url, session_id=session_id)
        if not chunks:
            raise HTTPException(status_code=500, detail="Audio extraction failed: No audio chunks were produced.")

        chunk_count = len(chunks)

        # Step 2: Transcribe via Groq Whisper LPU (lightning fast, ~1-2s)
        transcription = transcribe_chunks(chunks, api_key=effective_api_key)
        if not transcription.strip():
            raise HTTPException(status_code=500, detail="Speech-to-text produced an empty transcription.")

        # Step 3: Immediate audio cleanup to prevent disk bloat
        audio_cleaned = False
        if req.auto_cleanup and hasattr(chunks, "cleanup"):
            chunks.cleanup()
            audio_cleaned = True

        # Step 4: High-efficiency unified extraction (1 single API call for all insights)
        insights = extract_all_insights(transcription, api_key=effective_api_key)

        # Step 5: Build RAG vector store for interactive chat (isolated collection per session)
        rag_chain = build_rag_chain(transcription, session_id=session_id, api_key=effective_api_key)

        processing_time = round(time.time() - start_time, 1)

        result_data = {
            "session_id": session_id,
            "title": insights.get("title", "Crux AI Video Analysis"),
            "summary": insights.get("summary", ""),
            "actionable_items": insights.get("actionable_items", ""),
            "decisions": insights.get("decisions", ""),
            "questions": insights.get("questions", ""),
            "transcription": transcription,
            "chunk_count": chunk_count,
            "word_count": len(transcription.split()),
            "processing_time": processing_time,
            "audio_cleaned": audio_cleaned
        }

        # Store session in memory for follow-up Q&A
        SESSIONS[session_id] = {
            "rag_chain": rag_chain,
            "data": result_data,
            "api_key": effective_api_key,
            "created_at": time.time()
        }

        return result_data

    except Exception as e:
        if 'chunks' in locals() and hasattr(chunks, "cleanup"):
            try:
                chunks.cleanup()
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
def chat_with_video(req: ChatRequest):
    session = SESSIONS.get(req.session_id)
    if not session or "rag_chain" not in session:
        raise HTTPException(
            status_code=404,
            detail="Session expired or not found. Please re-process your video to begin a new chat."
        )

    question = req.message.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        answer = ask_question(session["rag_chain"], question)
        return {
            "session_id": req.session_id,
            "question": question,
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying Crux AI: {str(e)}")


@app.post("/api/purge-downloads")
def purge_downloads_endpoint():
    """Manual or automated endpoint to purge all temporary files from disk."""
    try:
        purge_all_downloads()
        return {"status": "success", "message": "All downloads and temporary audio files purged."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount Static Frontend
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Crux AI API is running. Static frontend not yet initialized."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"Starting Crux AI server on http://localhost:{port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
