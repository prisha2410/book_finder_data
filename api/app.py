"""
Memory-Optimized FastAPI App with Semantic Search
Works on Render FREE tier (under 512MB RAM)
"""

import sys
import os
import time
import gc
from pathlib import Path
from typing import List, Dict

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from storage.db import BookDatabase
from ingestion.ingest_books import ingest_all_books
from transformation.clean_books import clean_all_books

# Import OPTIMIZED search engine
SEARCH_AVAILABLE = False
search_engine = None

try:
    from search.semantic_search_optimized import MemoryOptimizedSearchEngine
    SEARCH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Search not available: {e}")

# FastAPI
app = FastAPI(
    title="Book Finder (Memory Optimized)",
    description="AI-powered book search - Optimized for Render Free Tier",
    version="2.0.0-optimized"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Models
class SearchQuery(BaseModel):
    query: str
    top_k: int = Field(20, ge=1, le=50)
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3

# Initialize search engine (LAZY LOAD)
def init_search_engine():
    """Initialize search engine with aggressive memory optimization."""
    global search_engine

    if not SEARCH_AVAILABLE:
        return None

    try:
        print("🔍 Initializing memory-optimized search...")
        engine = MemoryOptimizedSearchEngine()
        
        stats = engine.get_statistics()
        
        if stats.get("indexed"):
            print(f"✅ Search ready: {stats['total_books']} books")
            print(f"✅ Memory optimized: float16, small model")
        else:
            print("⚠️ No index found - will build on first search")
        
        # Force garbage collection
        gc.collect()
        
        return engine
    except Exception as e:
        print(f"⚠️ Search init failed: {e}")
        return None

# Don't load search engine at startup - lazy load on first request
# This saves ~100MB at startup
search_engine = None

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "search_indexed": (
            search_engine.get_statistics().get("indexed", False)
            if search_engine else False
        ),
        "memory_optimized": True
    }

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
                "memory_optimized": True
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
    """Optimized search with lazy loading."""
    global search_engine
    
    # Lazy load search engine on first use
    if search_engine is None:
        if not SEARCH_AVAILABLE:
            raise HTTPException(503, "Search dependencies not installed")
        
        print("🔍 First search request - loading engine...")
        search_engine = init_search_engine()
        
        if not search_engine:
            raise HTTPException(503, "Search engine failed to initialize")
    
    start = time.time()

    try:
        results = search_engine.search(
            query=query.query,
            top_k=query.top_k,
            semantic_weight=query.semantic_weight,
            keyword_weight=query.keyword_weight,
        )

        # Force garbage collection after search
        gc.collect()

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
        raise HTTPException(503, "Search dependencies not installed")

    try:
        with BookDatabase() as db:
            books = db.get_recent_books(limit=100000)

        if not books:
            return {"status": "warning", "indexed": 0}

        global search_engine
        search_engine = MemoryOptimizedSearchEngine()
        search_engine.index_books(books, force_reindex=True)

        # Force garbage collection
        gc.collect()

        stats = search_engine.get_statistics()

        return {
            "status": "success",
            "indexed": stats["total_books"],
            "memory_optimized": True
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

@app.on_event("startup")
async def startup():
    print("\n" + "=" * 70)
    print(" Book Finder API (Memory Optimized) ".center(70, "="))
    print("=" * 70)
    print("🔧 Optimized for Render FREE tier (<512MB RAM)")
    print("⚡ Features: float16 embeddings, lazy loading, tiny model")

    try:
        with BookDatabase() as db:
            stats = db.get_statistics()
            print(f"\n📚 Database books: {stats['total_books']}")
    except Exception as e:
        print(f"⚠️ Database error: {e}")

    print("🔍 Search: Lazy load (loads on first search request)")
    print("\n🌐 http://localhost:7860")
    print("📘 http://localhost:7860/docs")
    print("=" * 70 + "\n")
    
    # Force garbage collection
    gc.collect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app_optimized:app", host="0.0.0.0", port=7860, reload=True)