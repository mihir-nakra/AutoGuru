import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

_embeddings = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            cache_folder=os.path.join(os.path.dirname(__file__), "embedding"),
        )
    return _embeddings


def load_vectordbs(db_id: str):
    """Load the summary and full ChromaDB vector stores for a vehicle.

    Args:
        db_id: Path-style identifier like 'honda/odyssey/2009'

    Returns:
        Tuple of (sum_db, full_db) Chroma vector stores.
    """
    embeddings = get_embeddings()
    base_path = os.path.join(os.path.dirname(__file__), "vectordbs", db_id)

    if not os.path.isdir(base_path):
        raise FileNotFoundError(f"Vector DB not found at {base_path}")

    full_db = Chroma(
        persist_directory=os.path.join(base_path, "full_db"),
        embedding_function=embeddings,
    )
    sum_db = Chroma(
        persist_directory=os.path.join(base_path, "sum_db"),
        embedding_function=embeddings,
    )
    return sum_db, full_db
