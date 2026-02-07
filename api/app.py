"""
Simplified FastAPI app - Single page application
Serves one HTML page that does everything: search, browse, stats
"""

import sys
import os
import time
from pathlib import Path
from typing import List, Dict

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ======================================================
# PROJECT ROOT (DO NOT CHANGE DIRECTORY STRUCTURE)
# ======================================================

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# ======================================================
# IMPORT PIPELINE COMPONENTS
# ======================================================

from storage.db import BookDatabase
from ingestion.ingest_books import ingest_all_books
from transformation.clean_books import clean_all_books

# ======================================================
# OPTIONAL SEARCH ENGINE
# ======================================================

SEARCH_AVAILABLE = False
search_engine = None

try:
    from search.semantic_search import SemanticSearchEngine
    SEARCH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Semantic search not available: {e}")

# ======================================================
# FASTAPI SETUP
# ======================================================

app = FastAPI(
    title="Book Finder",
    description="AI-powered semantic book search",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# TEMPLATES (FIXED)
# ======================================================

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

# ======================================================
# MODELS
# ======================================================

class SearchQuery(BaseModel):
    query: str
    top_k: int = Field(20, ge=1, le=50)
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3

# ======================================================
# SEARCH INITIALIZATION
# ======================================================

def init_search_engine():
    global search_engine

    if not SEARCH_AVAILABLE:
        return None

    try:
        print("🔍 Loading search engine...")
        engine = SemanticSearchEngine()
        stats = engine.get_statistics()

        if stats.get("indexed"):
            print(f"✅ Search ready: {stats['total_books']} books indexed")
        else:
            print("⚠️ Search index not built")

        return engine
    except Exception as e:
        print(f"⚠️ Search init failed: {e}")
        return None


search_engine = init_search_engine()

# ======================================================
# ROUTES
# ======================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "search_indexed": (
            search_engine.get_statistics().get("indexed", False)
            if search_engine else False
        )
    }

# ======================================================
# API ENDPOINTS
# ======================================================

@app.get("/api/stats")
async def get_stats():
    try:
        with BookDatabase() as db:
            db_stats = db.get_statistics()

        search_stats = (
            search_engine.get_statistics()
            if search_engine
            else {
                "total_books": 0,
                "embedding_dimension": 0,
                "model_name": "not_loaded",
                "indexed": False,
            }
        )

        return {
            "database": db_stats,
            "search_engine": search_stats,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/books")
async def get_books(limit: int = Query(50, ge=1, le=100)):
    try:
        with BookDatabase() as db:
            books = db.get_recent_books(limit=limit)
        return {"count": len(books), "books": books}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/books/{isbn}")
async def get_book(isbn: str):
    try:
        with BookDatabase() as db:
            book = db.get_book_by_isbn(isbn)

        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        return book

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
async def search(query: SearchQuery):
    if not search_engine:
        raise HTTPException(
            status_code=503,
            detail="Search engine not initialized",
        )

    start = time.time()

    try:
        results = search_engine.search(
            query=query.query,
            top_k=query.top_k,
            semantic_weight=query.semantic_weight,
            keyword_weight=query.keyword_weight,
        )

        return {
            "query": query.query,
            "count": len(results),
            "results": results,
            "search_time_ms": (time.time() - start) * 1000,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rebuild-index")
async def rebuild_index():
    if not SEARCH_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Search dependencies not installed",
        )

    try:
        with BookDatabase() as db:
            books = db.get_recent_books(limit=100000)

        if not books:
            return {"status": "warning", "indexed": 0}

        global search_engine
        search_engine = SemanticSearchEngine()
        search_engine.index_books(books, force_reindex=True)

        stats = search_engine.get_statistics()

        return {
            "status": "success",
            "indexed": stats["total_books"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sync")
async def sync_data():
    try:
        raw_books = ingest_all_books()
        cleaned_books = clean_all_books(raw_books)

        with BookDatabase() as db:
            inserted, duplicates = db.insert_books_batch(cleaned_books)

        return {
            "status": "success",
            "books_added": inserted,
            "duplicates": duplicates,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# STARTUP LOGS
# ======================================================

@app.on_event("startup")
async def startup():
    print("\n" + "=" * 70)
    print(" Book Finder API ".center(70, "="))
    print("=" * 70)

    try:
        with BookDatabase() as db:
            stats = db.get_statistics()
            print(f"📚 Database books: {stats['total_books']}")
    except Exception as e:
        print(f"⚠️ Database error: {e}")

    if search_engine and search_engine.get_statistics().get("indexed"):
        print("🔍 Semantic search ready")
    else:
        print("⚠️ Semantic search not indexed")

    print("🌐 http://localhost:8000")
    print("📘 http://localhost:8000/docs")
    print("=" * 70 + "\n")


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)
