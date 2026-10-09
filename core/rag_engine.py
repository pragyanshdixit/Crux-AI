import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.vector_store import (
    get_vector_store,
    load_vector_store,
    retrieve_vector_store
)

load_dotenv()


def get_llm(api_key: str | None = None, max_tokens: int = 768):
    """Optimized low-latency, token-capped LLM for fast RAG responses."""
    effective_key = api_key or os.getenv("GROQ_API_KEY")
    if not effective_key:
        raise ValueError("Groq API key is missing. Please provide your API key in settings or set GROQ_API_KEY.")

    return ChatGroq(
        model="openai/gpt-oss-20b",
        api_key=effective_key,
        temperature=0,
        max_tokens=max_tokens
    )


def format_docs(docs):
    return "\n\n".join(
        doc.page_content
        for doc in docs
    )


def create_rag_chain(vector_store, api_key: str | None = None):
    # Retrieve top 3 relevant chunks to conserve prompt tokens
    retriever = retrieve_vector_store(vector_store, k=3)
    model = get_llm(api_key=api_key, max_tokens=768)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are Crux AI, an executive assistant answering questions directly from the video context.

Guidelines:
- Speech-to-text context may contain phonetic variations (e.g., "Jeff" / "Jev", "Versal" / "Vercel", "Cloud Code" / "Claude Code"). Connect concepts accurately.
- Answer the user's question clearly, informatively, and concisely.
- Only respond with "I don't know" if the topic is completely absent from the context.

Context:
{context}
"""
        ),
        (
            "human",
            "{question}"
        )
    ])

    chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough()
        }
        | prompt
        | model
        | StrOutputParser()
    )

    return chain


def build_rag_chain(transcripts: str, session_id: str | None = None, api_key: str | None = None):
    vector_store = get_vector_store(transcripts, session_id=session_id)
    return create_rag_chain(vector_store, api_key=api_key)


def load_rag_chain(session_id: str | None = None, api_key: str | None = None):
    vector_store = load_vector_store(session_id=session_id)
    return create_rag_chain(vector_store, api_key=api_key)


def ask_question(chain, question: str):
    return chain.invoke(question)