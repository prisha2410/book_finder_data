"""
FastAPI service for serving book data + semantic search UI.
"""

import os
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Optional
from pydantic import BaseModel

from storage.db import BookDatabase
from ingestion.ingest_books import ingest_all_books
from transformation.clean_books import clean_all_books
from search.semantic_search import SemanticSearchEngine


# -------------------- Paths --------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# -------------------- App Setup --------------------

app = FastAPI(
    title="Book Finder Data API",
    description="API for accessing cleaned book data and semantic search",
    version="1.0.0"
)

print("🔍 Loading semantic search engine...")
search_engine = SemanticSearchEngine()
print("✅ Search engine ready!")


# -------------------- Models --------------------

class Book(BaseModel):
    isbn: str
    title: str
    description: Optional[str]
    authors: Optional[str]
    genres: Optional[str]
    publish_date: Optional[str]
    created_at: str


class BooksResponse(BaseModel):
    count: int
    books: List[Dict]


class SyncResponse(BaseModel):
    status: str
    message: str
    books_added: int
    books_updated: int


# -------------------- Root --------------------

@app.get("/")
async def root():
    return {
        "message": "Book Finder Data API",
        "version": "1.0.0",
        "endpoints": {
            "/books": "Get recent books",
            "/books/{isbn}": "Get book by ISBN",
            "/search": "Semantic book search",
            "/search-demo": "Web UI for search",
            "/sync": "Trigger data sync",
            "/stats": "Get database statistics",
            "/docs": "API documentation"
        }
    }


# -------------------- Book Data --------------------

@app.get("/books", response_model=BooksResponse)
async def get_books(
    limit: int = Query(default=1000, ge=1, le=1000)
):
    try:
        with BookDatabase() as db:
            books = db.get_recent_books(limit=limit)
        return {"count": len(books), "books": books}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/books/{isbn}")
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


# -------------------- Semantic Search --------------------

@app.get("/search")
async def semantic_search(q: str, top_k: int = 10):
    try:
        return search_engine.search(query=q, top_k=top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# -------------------- Search UI --------------------

@app.get("/search-demo", response_class=HTMLResponse)
async def search_demo(request: Request):
    return templates.TemplateResponse("search.html", {"request": request})


# -------------------- Sync --------------------

@app.post("/sync", response_model=SyncResponse)
async def sync_data():
    try:
        raw_books = ingest_all_books()
        if not raw_books:
            return {
                "status": "warning",
                "message": "No books found",
                "books_added": 0,
                "books_updated": 0
            }

        cleaned_books = clean_all_books(raw_books)

        with BookDatabase() as db:
            inserted, duplicates = db.insert_books_batch(cleaned_books)

        return {
            "status": "success",
            "message": "Sync completed",
            "books_added": inserted,
            "books_updated": duplicates
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- Stats --------------------

@app.get("/stats")
async def get_statistics():
    try:
        with BookDatabase() as db:
            stats = db.get_statistics()
        return {"database": "books.db", "statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- Health --------------------

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
