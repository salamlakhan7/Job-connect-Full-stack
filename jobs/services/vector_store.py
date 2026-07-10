import logging
import os
from functools import lru_cache

from django.conf import settings

logger = logging.getLogger(__name__)

CANDIDATE_COLLECTION = 'candidate_embeddings'
JOB_COLLECTION = 'job_embeddings'


class VectorStoreError(Exception):
    """Raised when ChromaDB operations fail."""


@lru_cache(maxsize=1)
def _get_client():
    os.environ.setdefault('ANONYMIZED_TELEMETRY', 'False')
    os.environ.setdefault('CHROMA_TELEMETRY', 'False')

    try:
        import chromadb
        from chromadb.config import Settings
    except ImportError as exc:
        logger.exception("ChromaDB import failed. exception_type=%s exception_message=%s", exc.__class__.__name__, str(exc))
        raise VectorStoreError("ChromaDB is not installed.") from exc

    try:
        chroma_path = getattr(settings, 'CHROMA_DB_PATH', 'chroma_db')
        logger.info("Initializing ChromaDB PersistentClient. path=%s", chroma_path)
        return chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False),
        )
    except Exception as exc:
        logger.exception(
            "Failed to initialize ChromaDB. path=%s exception_type=%s exception_message=%s",
            getattr(settings, 'CHROMA_DB_PATH', 'chroma_db'),
            exc.__class__.__name__,
            str(exc),
        )
        raise VectorStoreError("Failed to initialize ChromaDB.") from exc


def _get_collection(name: str):
    try:
        return _get_client().get_or_create_collection(name=name)
    except Exception as exc:
        logger.exception(
            "Failed to get ChromaDB collection. collection=%s exception_type=%s exception_message=%s",
            name,
            exc.__class__.__name__,
            str(exc),
        )
        raise VectorStoreError("Failed to get ChromaDB collection.") from exc


def upsert_embedding(collection_name: str, item_id: str, embedding: list[float], metadata: dict | None = None):
    collection = _get_collection(collection_name)
    try:
        collection.upsert(
            ids=[item_id],
            embeddings=[embedding],
            metadatas=[metadata or {}],
        )
    except Exception as exc:
        logger.exception("Failed to upsert ChromaDB embedding.")
        raise VectorStoreError("Failed to upsert ChromaDB embedding.") from exc


def get_embedding(collection_name: str, item_id: str):
    collection = _get_collection(collection_name)
    try:
        result = collection.get(ids=[item_id], include=['embeddings', 'metadatas'])
    except Exception as exc:
        logger.exception(
            "Failed to retrieve ChromaDB embedding. collection=%s item_id=%s exception_type=%s exception_message=%s",
            collection_name,
            item_id,
            exc.__class__.__name__,
            str(exc),
        )
        raise VectorStoreError("Failed to retrieve ChromaDB embedding.") from exc

    if not result.get('ids'):
        return None
    return result


def delete_embedding(collection_name: str, item_id: str):
    collection = _get_collection(collection_name)
    try:
        collection.delete(ids=[item_id])
    except Exception as exc:
        logger.exception("Failed to delete ChromaDB embedding.")
        raise VectorStoreError("Failed to delete ChromaDB embedding.") from exc


def query_embeddings(collection_name: str, query_embedding: list[float], n_results: int = 10):
    collection = _get_collection(collection_name)
    try:
        return collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=['distances', 'metadatas'],
        )
    except Exception as exc:
        logger.exception(
            "Failed to query ChromaDB embeddings. collection=%s n_results=%s embedding_dimensions=%s exception_type=%s exception_message=%s",
            collection_name,
            n_results,
            len(query_embedding) if hasattr(query_embedding, '__len__') else 'unknown',
            exc.__class__.__name__,
            str(exc),
        )
        raise VectorStoreError("Failed to query ChromaDB embeddings.") from exc
