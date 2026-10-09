import sys
import os
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

from utils.audio_preprocessing import process_input
from core.transcriber import transcribe_chunks
from core.extractor import extract_all_insights
from core.rag_engine import build_rag_chain, ask_question


def load_pipeline(link: str, api_key: str | None = None):
    effective_key = api_key or os.getenv("GROQ_API_KEY")
    if not effective_key:
        raise ValueError("Groq API key is missing. Please set GROQ_API_KEY in .env or provide it interactively.")

    print("\n[Crux AI] Fetching and preparing audio stream...")
    chunks = process_input(link)

    print(f"[Crux AI] Transcribing audio with Groq Whisper LPU (ultra-fast)...")
    transcription = transcribe_chunks(chunks, api_key=effective_key)

    # Immediately free disk space
    if hasattr(chunks, "cleanup"):
        chunks.cleanup()
        print("[Crux AI] Temporary audio artifacts cleaned up.")

    # High-efficiency unified extraction: 1 API call for all insights
    print("[Crux AI] Synthesizing insights with optimized single-pass extraction...")
    insights = extract_all_insights(transcription, api_key=effective_key)

    print("[Crux AI] Indexing context into vector store for RAG Q&A...")
    rag_chain = build_rag_chain(transcription, api_key=effective_key)

    return {
        "title": insights.get("title", "Crux AI Video Analysis"),
        "summary": insights.get("summary", ""),
        "actionable_items": insights.get("actionable_items", ""),
        "decisions": insights.get("decisions", ""),
        "questions": insights.get("questions", ""),
        "rag_chain": rag_chain
    }


if __name__ == "__main__":
    print("\n" + "="*50)
    print("        CRUX AI — Executive Video Intelligence")
    print("="*50 + "\n")

    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        groq_key = input("Enter your Groq API Key (gsk_...): ").strip()
        if not groq_key:
            print("Groq API key is required to run Crux AI. Exiting.")
            sys.exit(1)

    link = input("Enter YouTube link or audio file: ").strip()
    if not link:
        print("No input provided. Exiting.")
        sys.exit(0)

    pipeline_output = load_pipeline(link, api_key=groq_key)

    print("\n" + "="*50)
    print(f"Title: {pipeline_output['title']}")
    print("="*50 + "\n")

    print(f"Summary:\n{pipeline_output['summary']}\n\n")
    print(f"Actionable Items:\n{pipeline_output['actionable_items']}\n\n")
    print(f"Decisions:\n{pipeline_output['decisions']}\n\n")
    print(f"Questions:\n{pipeline_output['questions']}\n\n")

    print("="*50)
    print("Ask questions directly to Crux AI. Type 'exit' to quit.")
    print("="*50)
    while True:
        user_question = input("\n[Crux AI] Enter question: ").strip()
        if not user_question:
            continue
        if user_question.lower() in ('exit', 'quit', 'q'):
            print("Session ended.")
            break
        answer = ask_question(pipeline_output['rag_chain'], user_question)
        print(f"\nAnswer: {answer}")