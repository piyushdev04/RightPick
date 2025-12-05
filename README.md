# AI Product Discovery Assistant – Hunnit.com

A full-stack AI-powered product discovery system that scrapes athletic wear from Hunnit.com, indexes products with vector embeddings, and provides intelligent product recommendations through a RAG (Retrieval-Augmented Generation) pipeline.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture & Design Decisions](#architecture--design-decisions)
- [Scraping Approach](#scraping-approach)
- [RAG Pipeline Design](#rag-pipeline-design)
- [Challenges & Trade-offs](#challenges--trade-offs)
- [Future Improvements](#future-improvements)

---

## Quick Start

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **PostgreSQL** 13+ (with a database created, e.g., `product_assist`)
- **OpenAI API Key** (optional, for LLM-powered responses)

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@localhost:5432/product_assist
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHROMA_DB_DIR=./chroma_db
BACKEND_CORS_ORIGINS=http://localhost:5173
```

Start the backend:

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The FastAPI server will auto-create PostgreSQL tables on startup.

### Scraping & Indexing

Using the FastAPI Swagger UI at `http://localhost:8000/docs`:

1. **POST `/scrape/run`** – Scrapes all configured product collections from Hunnit.com and upserts into PostgreSQL
2. **POST `/scrape/index`** – Vectorizes all products and stores embeddings in Chroma

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

### Docker

```bash
docker-compose up
```

This will spin up PostgreSQL, the FastAPI backend, and the React frontend in containers.

---

## Architecture & Design Decisions

### System Overview

```
┌─────────────┐      ┌─────────────────┐      ┌──────────────┐
│ Hunnit.com  │─────▶│   Web Scraper   │─────▶│ PostgreSQL   │
│ (source)    │      │   (BeautifulSoup)      │ (structured) │
└─────────────┘      └─────────────────┘      └──────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │  Embeddings     │
                     │  (Chroma DB)    │
                     └─────────────────┘
                              ▲
         ┌────────────────────┘
         │
    ┌────────────┐      ┌──────────────┐      ┌─────────────┐
    │   React    │◀────▶│   FastAPI    │◀────▶│ Chroma +    │
    │  Frontend  │      │   Backend    │      │ PostgreSQL  │
    └────────────┘      └──────────────┘      └─────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   OpenAI LLM    │
                       │                 │
                       └─────────────────┘
```



### Design Decisions

| Decision | Rationale |
|----------|-----------|
| **PostgreSQL + Chroma** | Separate concerns: PostgreSQL for transactional data integrity, Chroma for fast semantic search |
| **Sentence-Transformers** | Lightweight, fast embeddings without requiring API calls (unlike OpenAI embeddings) |
| **BeautifulSoup** | Simple, sufficient for Hunnit's structured HTML (vs. Selenium for dynamic content) |
| **FastAPI** | Modern, async-ready, automatic OpenAPI/Swagger documentation |
| **React + Vite** | Fast HMR, minimal config, excellent for rapid prototyping |
| **Docker Compose** | Easy local development and production deployment |

---

## Scraping Approach

### Collections Targeted

The scraper targets 13 product collections:

```python
COLLECTIONS = [
    "half-sleeve-tops",
    "tank-top",
    "sweatshirts",
    "leggings",
    "skorts-for-women-1",
    "shorts",
    "joggers",
    "flare-pants",
    "capris",
    "straight-pants",
    "co-ord-set",
    "sports-bra",
    "jackets-hoodies"
]
```

Base URL: `https://hunnit.com/collections/{collection_slug}`

### Activity Mapping

Products are tagged with activities by mapping product details to Hunnit's activity taxonomy:

- Source: `https://hunnit.com/pages/shop-by-activity`
- Activities: `gym`, `yoga`, `travel`, `pilates`, `running`, `everyday`, etc.
- Mapping logic: fuzzy text matching against product title, description, and category

### Extraction Strategy

1. **Per-collection pagination** – Iterate through product pages
2. **Product data extraction**:
   - Name, price, description
   - Product images (first image selected)
   - Features/attributes from product metadata
   - Activity tags via fuzzy matching
3. **Upsert to PostgreSQL** – Insert or update products by `product_id` from Hunnit

### Robustness Measures

- **Retry logic** – Exponential backoff for network failures
- **User-Agent rotation** – Avoid blocking
- **Pagination handling** – Detect end of product list dynamically
- **Error logging** – Log failures without breaking the entire scrape job

**Code location**: [backend/app/scraper.py](backend/app/scraper.py)

---

## RAG Pipeline Design

### Overview

The RAG pipeline enables conversational product discovery by combining semantic search with LLM reasoning.

### Step-by-Step Flow

```
User Query
    ▼
[1. Embed Query]
    │ Input: "Looking for something I can wear in the gym and also in meetings."
    │ Model: sentence-transformers/all-MiniLM-L6-v2
    ▼
[2. Semantic Search in Chroma]
    │ Retrieve: top-k (default 8) most similar products
    │ Similarity: cosine distance on embeddings
    ▼
[3. Format Retrieved Products]
    │ Build context with product name, price, description, activities
    ▼
[4. LLM Reasoning (Optional)]
    │ If OPENAI_API_KEY is set:
    │   - Pass query + product context to ChatGPT
    │   - Prompt asks for personalized recommendations
    │ Else:
    │   - Return top products with simple heuristic ranking
    ▼
Response to User
    │ - Interpreted query intent
    │ - Top recommended products with explanations
    │ - Optional follow-up clarifying questions
```

### Implementation Details

**Endpoint**: `POST /chat/query`

**Request**:
```json
{
  "message": "Looking for something I can wear in the gym and also in meetings.",
  "top_k": 8
}
```

**Response**:
```json
{
  "response": "Based on your request, I recommend these versatile pieces...",
  "recommended_products": [
    {
      "id": 1,
      "name": "Urban Jogger",
      "price": 89.99,
      "activities": ["gym", "everyday"],
      "reason": "Perfect for both gym and casual office settings"
    }
  ]
}
```

**Key Code**: [backend/app/routers/chat.py](backend/app/routers/chat.py)

### Embedding Strategy

- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
  - Lightweight (22M params), fast inference
  - 384-dimensional vectors
  - Strong performance on semantic similarity tasks
- **Input**: Product name + description + activity tags concatenated
- **Storage**: Local Chroma SQLite (persistent, no external dependencies)
- **Update**: Re-index on `/scrape/index` call

---

## Challenges & Trade-offs

### Challenge 1: Dynamic Website Content

**Issue**: Hunnit.com may use JavaScript for rendering product details.

**Solution**: Used BeautifulSoup (static parsing) instead of Selenium.
- **Trade-off**: Cannot scrape fully client-rendered content; works for current Hunnit structure but may break if they switch to client-side rendering.
- **Mitigation**: Monitor for scraping failures; add Selenium/Playwright fallback if needed.

### Challenge 2: Embedding Quality vs. Performance

**Issue**: Better embeddings (e.g., OpenAI) cost money and require API calls; fast local models may be lower quality.

**Solution**: Using `sentence-transformers/all-MiniLM-L6-v2`.
- **Trade-off**: Lighter weight and free but potentially less nuanced than larger models.
- **Mitigation**: Tuned `top_k` retrieval count to 8 to ensure good options; LLM refinement helps rank results.

### Challenge 3: Activity Tag Mapping

**Issue**: Hunnit doesn't consistently tag products with activities; requires fuzzy matching.

**Solution**: Manual collection of activity taxonomy + fuzzy string matching.
- **Trade-off**: Imperfect mapping; may miss activities or assign incorrect tags.
- **Mitigation**: Fallback to category-based activity inference if fuzzy match fails.


### Challenge 4: LLM Dependency

**Issue**: LLM-powered responses require OpenAI API (costs + latency).

**Solution**: Fallback to rule-based ranking if API key is missing.
- **Trade-off**: Degraded UX without LLM, but system still functional.
- **Mitigation**: Use cheaper models (e.g., Ollama, Mistral) for self-hosted LLM.

### Challenge 6: Data Freshness

**Issue**: Scraped data can become stale; Chroma embeddings may not reflect product updates.

**Solution**: Manual trigger `/scrape/run` and `/scrape/index` endpoints.
- **Trade-off**: Manual process, not automatic.
- **Mitigation**: Implement scheduled background jobs (Celery, APScheduler) for continuous updates.

---

## Future Improvements

1. **Better Activity Tagging**
   - Use a classification model to predict activities from product text
   - Maintain a curated activity-product mapping in the database
   - Allow admins to manually override tags

2. **Product Filtering & Sorting**
   - Add API endpoints for filtering by price, activity, rating
   - Implement full-text search alongside vector search
   - Add sorting by relevance, price, popularity

3. **Advanced RAG Features**
   - Multi-turn conversation history
   - User feedback loop (thumbs up/down on recommendations) to fine-tune ranking
   - Context-aware follow-up questions
   - Support for multiple LLM backends (Ollama, Claude, etc.)

4. **Analytics Dashboard**
   - Track search queries and click-through rates
   - Monitor embedding quality and retrieval performance
   - Identify trending searches and popular products

5. **User Personalization**
    - Store user preferences and search history
    - Personalized recommendations based on past interactions
    - Wishlist functionality
---

## Future Deployment Improvement

### Production Checklist

- [ ] Use managed PostgreSQL (AWS RDS, DigitalOcean) instead of local DB
- [ ] Use managed vector DB (Pinecone) instead of Chroma SQLite