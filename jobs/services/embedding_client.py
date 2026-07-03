import logging
from functools import lru_cache

from django.conf import settings

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


@lru_cache(maxsize=2)
def _load_model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise EmbeddingError("Sentence Transformers is not installed.") from exc

    try:
        return SentenceTransformer(model_name)
    except Exception as exc:
        logger.exception("Failed to load embedding model.")
        raise EmbeddingError("Failed to load embedding model.") from exc


def get_embedding_model_name() -> str:
    return getattr(settings, 'EMBEDDING_MODEL', 'all-MiniLM-L6-v2')


def generate_embedding(text: str) -> list[float]:
    if not text or not text.strip():
        raise EmbeddingError("Cannot generate an embedding for empty text.")

    model_name = get_embedding_model_name()
    model = _load_model(model_name)

    try:
        embedding = model.encode(text, normalize_embeddings=True)
    except Exception as exc:
        logger.exception("Embedding generation failed.")
        raise EmbeddingError("Embedding generation failed.") from exc

    return [float(value) for value in embedding]
