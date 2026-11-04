import hashlib
import json
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer(MODEL_NAME)


def make_embedding(text: str) -> list[float]:
    vector = get_model().encode(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vector.astype(float).tolist()


def embedding_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def serialize_embedding(vector: list[float]) -> str:
    return json.dumps(vector)


def deserialize_embedding(value: str) -> np.ndarray:
    return np.asarray(json.loads(value), dtype=np.float32)


def cosine_similarity(first, second) -> float:
    first = np.asarray(first, dtype=np.float32)
    second = np.asarray(second, dtype=np.float32)

    denominator = np.linalg.norm(first) * np.linalg.norm(second)
    if denominator == 0:
        return 0.0

    return float(np.dot(first, second) / denominator)
