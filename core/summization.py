import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser

load_dotenv()


def get_model(max_tokens: int = 1024, temperature: float = 0.1):
    return ChatGroq(
        model="openai/gpt-oss-20b",
        api_key=os.getenv("GROQ_API_KEY"),
        max_tokens=max_tokens,
        temperature=temperature,
        max_retries=3,
    )


def text_chunking(text: str) -> list[str]:
    """Function to chunk text into larger 4000-character segments to minimize API calls."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=4000,
        chunk_overlap=300
    )
    return text_splitter.split_text(text)


def summarize_text(text: str) -> str:
    """Optimized summarization:
    - Direct single-call for standard transcripts (<10,000 chars) to minimize tokens and latency.
    - Two-tier chunking only for very long recordings.
    """
    if not text or not text.strip():
        return "No content to summarize."

    clean_text = text.strip()

    # Optimization: If text is standard length, perform in a single fast call
    if len(clean_text) <= 10000:
        model = get_model(max_tokens=512, temperature=0.1)
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are Crux AI. Summarize the key points of this video transcription "
             "clearly and concisely in no more than 150 words."),
            ("human", "{text}")
        ])
        chain = prompt | model | StrOutputParser()
        return chain.invoke({"text": clean_text}).strip()

    # For exceptionally long texts, chunk with larger 4k blocks
    model = get_model(max_tokens=512, temperature=0.1)
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are Crux AI. Summarize this segment of the video transcription concisely in under 80 words."),
        ("human", "{text}")
    ])
    chain = prompt | model | StrOutputParser()

    chunks = text_chunking(clean_text)
    summaries = [s.strip() for s in (chain.invoke({"text": chunk}) for chunk in chunks) if s.strip()]

    if not summaries:
        return "Summary could not be generated."

    if len(summaries) == 1:
        return summaries[0]

    final_input = "\n\n".join(summaries)
    prompt_final = ChatPromptTemplate.from_messages([
        ("system",
         "You are Crux AI. Combine the following summary segments into "
         "one coherent executive summary of no more than 250 words."),
        ("human", "{text}")
    ])
    final_chain = prompt_final | model | StrOutputParser()
    return final_chain.invoke({"text": final_input}).strip()


def generate_title(text: str) -> str:
    """Fast, low-token title generation."""
    model = get_model(max_tokens=64, temperature=0.2)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are Crux AI. Generate a concise title for the transcription. Return ONLY the title in 5 words or less."),
        ("human", "{text}")
    ])

    chain = prompt | model | StrOutputParser()
    # Sending first 1200 characters is more than enough for title context, saving input tokens
    return chain.invoke({"text": text[:1200]}).strip()
