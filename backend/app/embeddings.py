from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

from .config import settings


@lru_cache()
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embedding_model()
    # Convert to plain list of floats for Chroma compatibility
    vectors = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return [v.tolist() for v in vectors]


