from typing import Iterable, List, Sequence

import chromadb
from chromadb.utils import embedding_functions

from .config import settings
from .embeddings import embed_texts


def get_chroma_client():
    return chromadb.PersistentClient(path=settings.chroma_db_dir)


COLLECTION_NAME = "products"


def get_products_collection():
    client = get_chroma_client()

    # We plug in a dummy embedding function because we provide embeddings directly
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=settings.embedding_model
    )
    coll = client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=ef)
    return coll


def build_product_document(
    title: str,
    description: str | None,
    features: str | None,
    category: str | None,
    activities: Sequence[str] | None,
) -> str:
    activities_str = ", ".join(activities or [])

    # Derive a simple natural-language usage summary to help the embedding model.
    usage_fragments: List[str] = []
    if "meeting-friendly" in (activities or []):
        usage_fragments.append("works for both meetings and casual settings")
    if "casual" in (activities or []):
        usage_fragments.append("great for everyday casual wear")
    if "gym" in (activities or []):
        usage_fragments.append("suitable for gym and training")
    if "travel" in (activities or []):
        usage_fragments.append("comfortable for travel and long days")

    usage_summary = ""
    if usage_fragments:
        usage_summary = "Usage: " + "; ".join(usage_fragments)

    parts = [
        f"Title: {title}",
        f"Category: {category or 'N/A'}",
        f"Activities: {activities_str or 'N/A'}",
    ]
    if usage_summary:
        parts.append(usage_summary)
    if description:
        parts.append(f"Description: {description}")
    if features:
        parts.append(f"Features: {features}")
    return "\n".join(parts)


def upsert_products(
    product_ids: Iterable[int],
    titles: Iterable[str],
    descriptions: Iterable[str | None],
    features_list: Iterable[str | None],
    categories: Iterable[str | None],
    activities_list: Iterable[Sequence[str] | None],
):
    collection = get_products_collection()

    docs: List[str] = []
    ids: List[str] = []

    for pid, title, desc, feats, cat, acts in zip(
        product_ids, titles, descriptions, features_list, categories, activities_list
    ):
        doc = build_product_document(title, desc, feats, cat, acts or [])
        docs.append(doc)
        ids.append(str(pid))

    vectors = embed_texts(docs)

    collection.upsert(
        ids=ids,
        documents=docs,
        embeddings=vectors,
        metadatas=None,
    )


def query_products(query: str, top_k: int = 8):
    collection = get_products_collection()
    query_vec = embed_texts([query])[0]
    results = collection.query(
        query_embeddings=[query_vec],
        n_results=top_k,
    )
    return results


