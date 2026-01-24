"""
FastAPI service for serving book data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
from pydantic import BaseModel

from storage.db import BookDatabase
from ingestion.ingest_books import ingest_all_books
from transformation.clean_books import clean_all_books


# FastAPI app
app = FastAPI(
    title="Book Finder Data API",
    description="API for accessing cleaned book data for semantic search",
    version="1.0.0"
)


# Models
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


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Book Finder Data API",
        "version": "1.0.0",
        "endpoints": {
            "/books": "Get recent books",
            "/books/{isbn}": "Get book by ISBN",
            "/sync": "Trigger data sync",
            "/stats": "Get database statistics",
            "/docs": "API documentation"
        }
    }


# Get books endpoint
@app.get("/books", response_model=BooksResponse)
async def get_books(
    limit: int = Query(default=1000, ge=1, le=1000, description="Number of books to return")
):
    """
    Fetch the most recent books.
    
    Args:
        limit: Number of books to return (max 1000)
    
    Returns:
        JSON with count and list of books
    """
    try:
        with BookDatabase() as db:
            books = db.get_recent_books(limit=limit)
            
        return {
            "count": len(books),
            "books": books
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching books: {str(e)}")


# Get book by ISBN
@app.get("/books/{isbn}")
async def get_book(isbn: str):
    """
    Fetch a specific book by ISBN.
    
    Args:
        isbn: Book ISBN
    
    Returns:
        Book data or 404 if not found
    """
    try:
        with BookDatabase() as db:
            book = db.get_book_by_isbn(isbn)
        
        if not book:
            raise HTTPException(status_code=404, detail=f"Book with ISBN {isbn} not found")
        
        return book
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching book: {str(e)}")


# Sync endpoint
@app.post("/sync", response_model=SyncResponse)
async def sync_data():
    """
    Trigger a manual data sync/refresh.
    Re-ingests and processes data from CSV files.
    
    Returns:
        Sync status and statistics
    """
    try:
        # Ingest raw data
        raw_books = ingest_all_books()
        
        if not raw_books:
            return {
                "status": "warning",
                "message": "No books found to sync",
                "books_added": 0,
                "books_updated": 0
            }
        
        # Clean data
        cleaned_books = clean_all_books(raw_books)
        
        # Store in database
        with BookDatabase() as db:
            inserted, duplicates = db.insert_books_batch(cleaned_books)
        
        return {
            "status": "success",
            "message": "Data sync completed",
            "books_added": inserted,
            "books_updated": duplicates
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# Stats endpoint
@app.get("/stats")
async def get_statistics():
    """
    Get database statistics.
    
    Returns:
        Statistics about the database
    """
    try:
        with BookDatabase() as db:
            stats = db.get_statistics()
        
        return {
            "database": "books.db",
            "statistics": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "book-finder-api"}


if __name__ == "__main__":
    import uvicorn
    print("Starting Book Finder API server...")
    print("API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)