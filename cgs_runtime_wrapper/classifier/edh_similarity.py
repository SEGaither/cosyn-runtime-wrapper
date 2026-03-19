"""
Phase 3.4 - EDH Embedding Similarity - Production Implementation
Uses sentence-transformers all-MiniLM-L6-v2 for real semantic similarity.
Caches the model instance per process. Caches embeddings per session.

References:
- cosyn_wrapper_classifier_specification.md S5
- cosyn_wrapper_gate_specifications.md EDH gate
- cosyn_wrapper_interface_contracts.json EDHBufferEntry
"""
from __future__ import annotations

import logging
import threading
from typing import Optional

import numpy as np

from cgs_runtime_wrapper.models.envelopes import EDHBufferEntry

logger = logging.getLogger(__name__)

_MODEL_NAME = "all-MiniLM-L6-v2"
_EMBEDDING_DIM = 384
_SIMILARITY_THRESHOLD = 0.85
_BUFFER_MAX = 10

_model_lock = threading.Lock()
_model_instance = None


def _get_model():
    """
    Load and cache the SentenceTransformer model. Thread-safe.
    Raises ImportError if sentence-transformers is not installed.
    """
    global _model_instance
    if _model_instance is not None:
        return _model_instance
    with _model_lock:
        if _model_instance is not None:
            return _model_instance
        try:
            from sentence_transformers import SentenceTransformer
            _model_instance = SentenceTransformer(_MODEL_NAME)
            logger.info("EDH: SentenceTransformer model loaded: %s", _MODEL_NAME)
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for EDH similarity. "
                "Install: pip install sentence-transformers>=2.2.0"
            ) from exc
        return _model_instance


_session_cache: dict[str, dict[int, list[float]]] = {}
_cache_lock = threading.Lock()


def _cache_get(session_id: str, turn_index: int) -> Optional[list[float]]:
    with _cache_lock:
        return _session_cache.get(session_id, {}).get(turn_index)


def _cache_set(session_id: str, turn_index: int, embedding: list[float]) -> None:
    with _cache_lock:
        if session_id not in _session_cache:
            _session_cache[session_id] = {}
        _session_cache[session_id][turn_index] = embedding


def invalidate_session_cache(session_id: str) -> None:
    """Remove cached embeddings for a session. Call on session reset."""
    with _cache_lock:
        _session_cache.pop(session_id, None)


def embed_text(
    text: str,
    session_id: Optional[str] = None,
    turn_index: Optional[int] = None,
) -> list[float]:
    """
    Encode text into a sentence embedding using all-MiniLM-L6-v2.

    Caches the result keyed by (session_id, turn_index) when provided.
    Returns a list[float] of dimension 384 (normalized).

    Spec ref: cosyn_wrapper_classifier_specification.md S5 step 1
    """
    if session_id is not None and turn_index is not None:
        cached = _cache_get(session_id, turn_index)
        if cached is not None:
            return cached

    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    result: list[float] = embedding.tolist()

    if session_id is not None and turn_index is not None:
        _cache_set(session_id, turn_index, result)

    return result


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    For normalize_embeddings=True output, similarity equals dot product.
    Returns float in [0.0, 1.0]. Returns 0.0 on zero-magnitude vectors.
    """
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    similarity = float(np.dot(a, b) / (norm_a * norm_b))
    return float(np.clip(similarity, 0.0, 1.0))


def compute_max_similarity(
    text: str,
    buffer: list[EDHBufferEntry],
    session_id: Optional[str] = None,
    turn_index: Optional[int] = None,
) -> tuple[float, list[float]]:
    """
    Compute the maximum cosine similarity between text embedding and EDH buffer.

    Per spec S5 steps 1-4:
    - Encodes the current turn conclusion text
    - Compares against each buffer entry stored embedding
    - Returns max similarity across buffer
    - Returns the embedding for the current text for buffer append by caller

    Returns: (max_similarity_score, embedding_for_text)
    """
    embedding = embed_text(text, session_id=session_id, turn_index=turn_index)

    if not buffer:
        return 0.0, embedding

    max_sim = 0.0
    for entry in buffer:
        if not entry.conclusion_embedding:
            continue
        sim = cosine_similarity(embedding, entry.conclusion_embedding)
        if sim > max_sim:
            max_sim = sim

    return max_sim, embedding


def is_echo(
    similarity_score: float,
    threshold: float = _SIMILARITY_THRESHOLD,
) -> bool:
    """
    Return True if similarity_score exceeds echo detection threshold.
    Threshold per spec S5 step 4: 0.85.
    """
    return similarity_score > threshold


def get_similarity_threshold() -> float:
    """Return the configured similarity threshold for echo detection."""
    return _SIMILARITY_THRESHOLD
