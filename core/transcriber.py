import os
from dotenv import load_dotenv

load_dotenv()

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
model_eng = None


def load_local_model():
    """Lazy loader for local Whisper fallback."""
    global model_eng
    if model_eng is None:
        import whisper
        print(f"[Crux AI] Loading local Whisper model ({WHISPER_MODEL})...")
        model_eng = whisper.load_model(WHISPER_MODEL)
    return model_eng


def transcribe_audio_local(audio_path: str, language: str = "en") -> str:
    """Local fallback transcription using OpenAI Whisper on CPU."""
    model = load_local_model()
    kwargs = {"language": language} if language else {}
    result = model.transcribe(audio_path, **kwargs)
    return result["text"].strip()


def transcribe_audio_groq(audio_path: str, api_key: str | None = None, language: str = "en") -> str:
    """Ultra-fast cloud transcription via Groq LPU (whisper-large-v3-turbo).
    Processes audio in ~1-2 seconds instead of minutes.
    """
    from groq import Groq
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("Groq API key is missing.")

    client = Groq(api_key=key)
    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f),
            model="whisper-large-v3-turbo",
            response_format="text",
            language=language if language else None
        )
    return str(response).strip()


def transcribe_audio(audio_path: str, api_key: str | None = None, language: str = "en") -> str:
    """Transcribe a single audio file, prioritizing ultra-fast Groq LPU transcription
    with automatic graceful fallback to local Whisper.
    """
    key = api_key or os.getenv("GROQ_API_KEY")
    if key:
        try:
            print("[Crux AI] Transcribing via Groq Whisper LPU (ultra-fast)...")
            return transcribe_audio_groq(audio_path, api_key=key, language=language)
        except Exception as e:
            print(f"[Crux AI] Groq Whisper failed ({e}). Falling back to local Whisper...")
            return transcribe_audio_local(audio_path, language=language)
    else:
        return transcribe_audio_local(audio_path, language=language)


def transcribe_chunks(chunks: list, api_key: str | None = None, language: str = "en") -> str:
    """Transcribe a list of audio chunks (or single file) and concatenate results."""
    full_transcription = ""
    total = len(chunks)

    for i, chunk in enumerate(chunks):
        if total > 1:
            print(f"[Crux AI] Transcribing segment {i+1}/{total}: {chunk}")
        transcription = transcribe_audio(chunk, api_key=api_key, language=language)
        full_transcription += transcription + " "

    return full_transcription.strip()

    
    

        
