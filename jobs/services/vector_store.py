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
        raise VectorStoreError("ChromaDB is not installed.") from exc

    try:
        return chromadb.PersistentClient(
            path=getattr(settings, 'CHROMA_DB_PATH', 'chroma_db'),
            settings=Settings(anonymized_telemetry=False),
        )
    except Exception as exc:
        logger.exception("Failed to initialize ChromaDB.")
        raise VectorStoreError("Failed to initialize ChromaDB.") from exc


def _get_collection(name: str):
    try:
        return _get_client().get_or_create_collection(name=name)
    except Exception as exc:
        logger.exception("Failed to get ChromaDB collection.")
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
        logger.exception("Failed to retrieve ChromaDB embedding.")
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
        logger.exception("Failed to query ChromaDB embeddings.")
        raise VectorStoreError("Failed to query ChromaDB embeddings.") from exc
