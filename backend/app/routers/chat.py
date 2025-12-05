from typing import List

from fastapi import APIRouter, Depends
from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Product
from ..schemas import (
    ChatProductSnippet,
    ChatRequest,
    ChatMessage,
    ChatResponse,
)
from ..vectorstore import query_products


router = APIRouter(prefix="/chat", tags=["chat"])


SYSTEM_PROMPT = """
You are an AI shopping assistant for Hunnit activewear.
You help users discover the best products for their needs.

When answering:
- Interpret abstract, high-level queries (e.g. gym + meetings).
- Use the retrieved products as your source of truth.
- Explain WHY each recommended product is a good fit, referencing activities, fit, fabric, and use-cases.
- If the query is too vague, ask 1-2 short clarifying questions before final recommendations.
- Keep answers concise and friendly (2-4 sentences).
"""


def _rerank_for_query(query: str, snippets: List[ChatProductSnippet]) -> List[ChatProductSnippet]:
    """
    Apply lightweight, deterministic re-ranking on top of vector similarity.

    Intuition:
    - If the user mentions meetings/office/work, prefer more covered / smart-casual
      items (polo, sweatshirt, joggers, pants) and slightly down-rank pure sports bras.
    - Otherwise, keep the vector ranking mostly as-is.
    """
    q = query.lower()
    wants_meeting_ready = any(word in q for word in ["meeting", "office", "work", "formal"])

    adjusted: List[ChatProductSnippet] = []
    for s in snippets:
        title_lower = s.title.lower()
        cat_lower = (s.category or "").lower()
        score = s.relevance_score  # distance: lower is better

        if wants_meeting_ready:
            # Boost more versatile / polished pieces
            if any(k in title_lower for k in ["polo", "sweatshirt", "jogger"]) or any(
                k in cat_lower for k in ["sweatshirts", "joggers", "straight-pants", "flare-pants"]
            ):
                score *= 0.9  # 10% closer

            # Down-rank very sporty-only tops for meetings
            if "sports bra" in title_lower and "set" not in title_lower:
                score *= 1.15  # 15% further

        s.relevance_score = float(score)
        adjusted.append(s)

    # Resort by adjusted score (ascending distance = more relevant)
    adjusted.sort(key=lambda x: x.relevance_score)
    return adjusted


def _fallback_response(message: str, snippets: List[ChatProductSnippet]) -> ChatResponse:
    if not snippets:
        text = (
            "I couldn't find relevant products for that query yet. "
            "Please try rephrasing what you're looking for (e.g. 'gym leggings that work for casual wear')."
        )
        return ChatResponse(
            messages=[ChatMessage(role="assistant", content=text)], products=[]
        )

    intro = "Here are some products that could work for you:"
    details_lines = []
    for p in snippets[:4]:
        line = f"- {p.title} (approx. ₹{p.price or '—'}) – category: {p.category or 'N/A'}; activities: {', '.join(p.activities) or 'N/A'}."
        details_lines.append(line)
    text = intro + "\n" + "\n".join(details_lines)
    return ChatResponse(
        messages=[ChatMessage(role="assistant", content=text)],
        products=snippets,
    )


@router.post("/query", response_model=ChatResponse)
def chat_query(payload: ChatRequest, db: Session = Depends(get_db)):
    query = payload.message.strip()
    if not query:
        return ChatResponse(
            messages=[
                ChatMessage(
                    role="assistant",
                    content="Tell me what you're looking for – for example, 'leggings I can wear to yoga and brunch'.",
                )
            ],
            products=[],
        )

    vector_results = query_products(query, top_k=payload.top_k)

    ids = [int(x) for x in (vector_results.get("ids", [[]])[0] or [])]
    distances = vector_results.get("distances", [[]])[0] or []

    if not ids:
        return _fallback_response(query, [])

    products_map = {
        p.id: p
        for p in db.scalars(select(Product).where(Product.id.in_(ids)))  # type: ignore[arg-type]
    }

    snippets: List[ChatProductSnippet] = []
    for pid, dist in zip(ids, distances):
        p = products_map.get(pid)
        if not p:
            continue
        acts = [a.strip() for a in (p.activities or "").split(",") if a.strip()]
        snippets.append(
            ChatProductSnippet(
                id=p.id,
                title=p.title,
                price=p.price,
                image_url=p.image_url,
                product_url=p.product_url,
                category=p.category,
                activities=acts,
                relevance_score=float(dist),
            )
        )

    # Apply heuristic, query-aware reranking on top of raw vector similarity.
    snippets = _rerank_for_query(query, snippets)

    if not settings.openai_api_key:
        return _fallback_response(query, snippets)

    client = OpenAI(api_key=settings.openai_api_key)

    products_context_lines = []
    for s in snippets:
        line = f"- {s.title} (₹{s.price or '—'}), category={s.category or 'N/A'}, activities={', '.join(s.activities) or 'N/A'}, url={s.product_url}"
        products_context_lines.append(line)

    user_context = (
        f"User query: {query}\n\n"
        f"Candidate products:\n" + "\n".join(products_context_lines)
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_context},
        ],
        temperature=0.4,
    )

    answer = completion.choices[0].message.content or ""

    return ChatResponse(
        messages=[
            ChatMessage(role="user", content=query),
            ChatMessage(role="assistant", content=answer),
        ],
        products=snippets,
    )


