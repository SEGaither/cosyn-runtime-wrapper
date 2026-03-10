"""
Phase 3.4 — EDH Embedding Similarity STUB
Uses numpy zeros placeholder — no actual model.
Returns similarity_score=0.0 always.
"""
from __future__ import annotations

import numpy as np

from cgs_runtime_wrapper.models.envelopes import EDHBufferEntry


def embed_text(text: str) -> list[float]:
    """
    STUB: Return a zero-vector embedding.
    In Phase 3+ this will call an embedding model.
    """
    # Placeholder: 768-dimensional zero vector
    return np.zeros(768, dtype=float).tolist()


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    Returns 0.0 if either vector is zero (stub behavior).
    """
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def compute_max_similarity(
    text: str,
    buffer: list[EDHBufferEntry],
) -> tuple[float, list[float]]:
    """
    Compute the maximum cosine similarity between text embedding
    and all entries in the EDH buffer.

    Returns (max_similarity_score, embedding_for_text).
    STUB: always returns (0.0, zero_vector).
    """
    embedding = embed_text(text)
    if not buffer:
        return 0.0, embedding

    max_sim = 0.0
    for entry in buffer:
        sim = cosine_similarity(embedding, entry.conclusion_embedding)
        if sim > max_sim:
            max_sim = sim

    return max_sim, embedding
