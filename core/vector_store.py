"""Crux AI Semantic Vector Store.
Indexes transcript segments into ChromaDB using cached local MiniLM embeddings.
Supports session-isolated collections to avoid cross-video context contamination.
"""

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import os

CHROMA_DIR="chroma_db"
Collection="transcripts"
model="all-MiniLM-L6-v2"

_CACHED_EMBEDDINGS = None

def get_embeddings():
    """Singleton cached embeddings to eliminate repeated model loading latency."""
    global _CACHED_EMBEDDINGS
    if _CACHED_EMBEDDINGS is None:
        _CACHED_EMBEDDINGS = HuggingFaceEmbeddings(model_name=model, model_kwargs={"device": "cpu"})
    return _CACHED_EMBEDDINGS


def get_vector_store(transcripts: str, session_id: str | None = None) -> Chroma:
    """Split transcript into optimal chunks and index into isolated Chroma collection."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(transcripts)
    
    docs = [Document(page_content=chunk) for chunk in chunks]
    embeddings = get_embeddings()
    
    coll_name = f"transcripts_{session_id}" if session_id else Collection
    
    vector_store = Chroma.from_documents(
        docs, 
        embeddings, 
        persist_directory=CHROMA_DIR, 
        collection_name=coll_name
    )
    
    return vector_store


def load_vector_store(session_id: str | None = None) -> Chroma:
    embeddings = get_embeddings()
    coll_name = f"transcripts_{session_id}" if session_id else Collection
    
    vector_store = Chroma(
        persist_directory=CHROMA_DIR, 
        embedding_function=embeddings, 
        collection_name=coll_name
    )
    
    return vector_store


def retrieve_vector_store(vector_store: Chroma, k: int = 3):
    """Retrieve top k (default 3) relevant chunks to minimize prompt tokens."""
    return vector_store.as_retriever(
        search_kwargs={"k": k},
        search_type="similarity"
    )


    
    
    