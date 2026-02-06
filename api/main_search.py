"""
Enhanced FastAPI service with semantic search capabilities.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from storage.db import BookDatabase
from search.semantic_search import SemanticSearchEngine


# FastAPI app
app = FastAPI(
    title="Book Finder Semantic Search API",
    description="Intelligent book search and recommendation system using semantic embeddings",
    version="2.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize search engine
search_engine = SemanticSearchEngine()


# Models
class SearchQuery(BaseModel):
    query: str = Field(..., description="Natural language search query")
    top_k: int = Field(10, ge=1, le=50, description="Number of results")
    semantic_weight: float = Field(0.7, ge=0.0, le=1.0)
    keyword_weight: float = Field(0.3, ge=0.0, le=1.0)
    genre_filter: Optional[List[str]] = Field(None, description="Filter by genres")


class SearchResult(BaseModel):
    isbn: str
    title: str
    description: Optional[str]
    authors: Optional[str]
    genres: Optional[str]
    publish_date: Optional[str]
    similarity_score: float
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    count: int
    results: List[SearchResult]
    search_time_ms: float


# Root endpoint with documentation
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API documentation."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Book Finder Semantic Search API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            code { background: #e0e0e0; padding: 2px 6px; border-radius: 3px; }
            .method { color: #0066cc; font-weight: bold; }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>📚 Book Finder Semantic Search API</h1>
        <p><strong>Version:</strong> 2.0.0</p>
        
        <h2>Features</h2>
        <ul>
            <li>🔍 Semantic search using natural language</li>
            <li>🤖 AI-powered book recommendations</li>
            <li>🎯 Hybrid search (semantic + keyword matching)</li>
            <li>🏷️ Genre-based filtering</li>
            <li>📊 Similarity scoring</li>
        </ul>
        
        <h2>API Endpoints</h2>
        
        <div class="endpoint">
            <p><span class="method">POST</span> <code>/search</code></p>
            <p>Semantic search for books based on natural language description</p>
        </div>
        
        <div class="endpoint">
            <p><span class="method">GET</span> <code>/recommend/{isbn}</code></p>
            <p>Get books similar to a specific book</p>
        </div>
        
        <div class="endpoint">
            <p><span class="method">POST</span> <code>/rebuild-index</code></p>
            <p>Rebuild search index (admin)</p>
        </div>
        
        <div class="endpoint">
            <p><span class="method">GET</span> <code>/stats</code></p>
            <p>Get search engine statistics</p>
        </div>
        
        <div class="endpoint">
            <p><span class="method">GET</span> <code>/health</code></p>
            <p>Health check endpoint</p>
        </div>
        
        <h2>Interactive Documentation</h2>
        <p>📖 <a href="/docs">Swagger UI Documentation</a></p>
        <p>📖 <a href="/redoc">ReDoc Documentation</a></p>
        
        <h2>Example Usage</h2>
        <pre>
curl -X POST "http://localhost:8000/search" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "A book about artificial intelligence and machine learning for beginners",
    "top_k": 5
  }'
        </pre>
        
        <h2>Quick Test</h2>
        <p><a href="/search-demo">Try the search demo</a></p>
    </body>
    </html>
    """


@app.get("/search-demo", response_class=HTMLResponse)
async def search_demo():
    """Simple search demo page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Book Search Demo</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            input, button { padding: 10px; margin: 5px 0; font-size: 16px; }
            #query { width: 600px; }
            button { background: #0066cc; color: white; border: none; cursor: pointer; border-radius: 5px; }
            button:hover { background: #0052a3; }
            .result { background: #f9f9f9; padding: 15px; margin: 15px 0; border-left: 4px solid #0066cc; }
            .score { color: #666; font-size: 14px; }
            .description { margin-top: 10px; color: #555; }
        </style>
    </head>
    <body>
        <h1>📚 Book Finder - Search Demo</h1>
        
        <div>
            <input type="text" id="query" placeholder="Describe the book you're looking for..." />
            <button onclick="search()">Search</button>
        </div>
        
        <div id="results"></div>
        
        <script>
            async function search() {
                const query = document.getElementById('query').value;
                if (!query) return;
                
                document.getElementById('results').innerHTML = '<p>Searching...</p>';
                
                try {
                    const response = await fetch('/search', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: query, top_k: 10 })
                    });
                    
                    const data = await response.json();
                    displayResults(data);
                } catch (error) {
                    document.getElementById('results').innerHTML = '<p>Error: ' + error.message + '</p>';
                }
            }
            
            function displayResults(data) {
                if (data.count === 0) {
                    document.getElementById('results').innerHTML = '<p>No results found.</p>';
                    return;
                }
                
                let html = '<h2>Found ' + data.count + ' results in ' + data.search_time_ms.toFixed(2) + ' ms</h2>';
                
                data.results.forEach((book, index) => {
                    html += '<div class="result">';
                    html += '<h3>' + (index + 1) + '. ' + book.title + '</h3>';
                    html += '<p class="score">Similarity: ' + (book.similarity_score * 100).toFixed(1) + '%</p>';
                    if (book.authors) html += '<p><strong>Authors:</strong> ' + book.authors + '</p>';
                    if (book.genres) html += '<p><strong>Genres:</strong> ' + book.genres + '</p>';
                    if (book.publish_date) html += '<p><strong>Published:</strong> ' + book.publish_date + '</p>';
                    if (book.description) {
                        const desc = book.description.length > 300 ? 
                            book.description.substring(0, 300) + '...' : book.description;
                        html += '<p class="description">' + desc + '</p>';
                    }
                    html += '<p><strong>ISBN:</strong> ' + book.isbn + '</p>';
                    html += '</div>';
                });
                
                document.getElementById('results').innerHTML = html;
            }
            
            // Allow Enter key to search
            document.getElementById('query').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') search();
            });
        </script>
    </body>
    </html>
    """


@app.post("/search")
async def search_books(search_query: SearchQuery):
    """
    Semantic search for books.
    
    Accepts natural language queries like:
    - "A thrilling mystery novel set in Victorian London"
    - "Books about machine learning for beginners"
    - "Science fiction with strong female protagonists"
    """
    import time
    
    start_time = time.time()
    
    try:
        results = search_engine.search(
            query=search_query.query,
            top_k=search_query.top_k,
            semantic_weight=search_query.semantic_weight,
            keyword_weight=search_query.keyword_weight,
            genre_filter=search_query.genre_filter
        )
        
        search_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "query": search_query.query,
            "count": len(results),
            "results": results,
            "search_time_ms": search_time
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/recommend/{isbn}")
async def recommend_similar(isbn: str, top_k: int = Query(5, ge=1, le=20)):
    """
    Get books similar to a specific book.
    
    Args:
        isbn: ISBN of the reference book
        top_k: Number of recommendations to return
    """
    try:
        results = search_engine.recommend_similar(isbn=isbn, top_k=top_k)
        
        if not results:
            raise HTTPException(status_code=404, detail=f"No recommendations found for ISBN {isbn}")
        
        return {
            "isbn": isbn,
            "count": len(results),
            "recommendations": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


@app.post("/rebuild-index")
async def rebuild_index():
    """
    Rebuild the search index from the database.
    
    This is an admin endpoint that should be called after:
    - Adding new books to the database
    - Updating book metadata
    - Initial setup
    """
    try:
        # Load books from database
        with BookDatabase() as db:
            books = db.get_recent_books(limit=100000)
        
        if not books:
            return {
                "status": "warning",
                "message": "No books found in database",
                "indexed": 0
            }
        
        # Rebuild index
        global search_engine
        search_engine = SemanticSearchEngine()
        search_engine.index_books(books, force_reindex=True)
        
        stats = search_engine.get_statistics()
        
        return {
            "status": "success",
            "message": "Search index rebuilt successfully",
            "indexed": stats['total_books']
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index rebuild failed: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Get search engine and database statistics."""
    try:
        # Search engine stats
        search_stats = search_engine.get_statistics()
        
        # Database stats
        with BookDatabase() as db:
            db_stats = db.get_statistics()
        
        return {
            "search_engine": search_stats,
            "database": db_stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    is_indexed = search_engine.get_statistics()['indexed']
    
    return {
        "status": "healthy" if is_indexed else "not_indexed",
        "service": "book-finder-semantic-search",
        "indexed": is_indexed
    }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print(" Starting Book Finder Semantic Search API ".center(70, "="))
    print("="*70)
    print("\n🚀 Server starting on http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🔍 Try it: http://localhost:8000/search-demo")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)