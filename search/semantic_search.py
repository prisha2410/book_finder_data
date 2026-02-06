"""
Semantic Search Engine for Book Recommendations
================================================
Uses sentence-transformers to create embeddings and perform similarity search.

Key Features:
- Generates embeddings for book descriptions
- Performs cosine similarity search
- Hybrid search combining semantic + keyword matching
- Re-ranking based on multiple factors
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import json


class SemanticSearchEngine:
    """
    Semantic search engine for book recommendations.
    
    Uses a hybrid approach:
    1. Semantic similarity (sentence-transformers)
    2. Keyword matching (TF-IDF)
    3. Metadata boosting (genres, authors, popularity)
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        embeddings_path: str = "data/embeddings.pkl",
        index_path: str = "data/book_index.pkl"
    ):
        """
        Initialize the search engine.
        
        Args:
            model_name: HuggingFace model name for embeddings
            embeddings_path: Where to save/load embeddings
            index_path: Where to save/load book index
        """
        self.model_name = model_name
        self.embeddings_path = embeddings_path
        self.index_path = index_path
        
        # Load or initialize model
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # Storage
        self.books = []
        self.embeddings = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        
        # Load if exists
        self._load_if_exists()
    
    def _load_if_exists(self):
        """Load pre-computed embeddings if they exist."""
        if Path(self.embeddings_path).exists() and Path(self.index_path).exists():
            print("Loading pre-computed embeddings...")
            try:
                with open(self.embeddings_path, 'rb') as f:
                    data = pickle.load(f)
                    self.embeddings = data['embeddings']
                    self.tfidf_matrix = data.get('tfidf_matrix')
                
                with open(self.index_path, 'rb') as f:
                    index_data = pickle.load(f)
                    self.books = index_data['books']
                    self.tfidf_vectorizer = index_data.get('tfidf_vectorizer')
                
                print(f"✓ Loaded {len(self.books)} books with embeddings")
            except Exception as e:
                print(f"⚠ Error loading embeddings: {e}")
                self.books = []
                self.embeddings = None
    
    def index_books(self, books: List[Dict], force_reindex: bool = False):
        """
        Create embeddings for all books.
        
        Args:
            books: List of book dictionaries with isbn, title, description, etc.
            force_reindex: Re-create embeddings even if they exist
        """
        if not force_reindex and self.embeddings is not None:
            print("Embeddings already exist. Use force_reindex=True to rebuild.")
            return
        
        print(f"\nIndexing {len(books)} books...")
        
        # Filter books with descriptions
        valid_books = [b for b in books if b.get('description')]
        print(f"  Books with descriptions: {len(valid_books)}")
        
        if not valid_books:
            print("⚠ No books with descriptions to index")
            return
        
        self.books = valid_books
        
        # Prepare texts for embedding
        # Combine title + description + genres for richer embeddings
        texts = []
        for book in valid_books:
            text_parts = []
            
            # Title (weighted higher)
            if book.get('title'):
                text_parts.append(f"Title: {book['title']}")
            
            # Description
            if book.get('description'):
                text_parts.append(book['description'])
            
            # Genres (for domain context)
            if book.get('genres'):
                text_parts.append(f"Genres: {book['genres']}")
            
            texts.append(' '.join(text_parts))
        
        # Generate embeddings
        print("  Generating semantic embeddings...")
        self.embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            batch_size=32,
            convert_to_numpy=True
        )
        
        # Generate TF-IDF for keyword matching
        print("  Generating TF-IDF vectors...")
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
        
        # Save
        self._save_index()
        
        print(f"✓ Indexed {len(valid_books)} books")
        print(f"  Embedding dimension: {self.embeddings.shape[1]}")
    
    def _save_index(self):
        """Save embeddings and index to disk."""
        Path(self.embeddings_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save embeddings
        with open(self.embeddings_path, 'wb') as f:
            pickle.dump({
                'embeddings': self.embeddings,
                'tfidf_matrix': self.tfidf_matrix
            }, f)
        
        # Save book index
        with open(self.index_path, 'wb') as f:
            pickle.dump({
                'books': self.books,
                'tfidf_vectorizer': self.tfidf_vectorizer
            }, f)
        
        print(f"✓ Saved embeddings to {self.embeddings_path}")
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        genre_filter: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search for books matching the query.
        
        Args:
            query: User's search query (natural language description)
            top_k: Number of results to return
            semantic_weight: Weight for semantic similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)
            genre_filter: Optional list of genres to filter by
        
        Returns:
            List of books with similarity scores
        """
        if self.embeddings is None or len(self.books) == 0:
            print("⚠ No books indexed. Call index_books() first.")
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Semantic similarity
        semantic_scores = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Keyword similarity
        query_tfidf = self.tfidf_vectorizer.transform([query])
        keyword_scores = cosine_similarity(query_tfidf, self.tfidf_matrix)[0]
        
        # Hybrid score
        combined_scores = (
            semantic_weight * semantic_scores +
            keyword_weight * keyword_scores
        )
        
        # Apply genre filter if specified
        if genre_filter:
            genre_filter_lower = [g.lower() for g in genre_filter]
            for i, book in enumerate(self.books):
                book_genres = book.get('genres', '').lower()
                if not any(gf in book_genres for gf in genre_filter_lower):
                    combined_scores[i] = 0
        
        # Get top-k indices
        top_indices = np.argsort(combined_scores)[::-1][:top_k]
        
        # Prepare results
        results = []
        for idx in top_indices:
            if combined_scores[idx] > 0:  # Only include matches with positive scores
                book = self.books[idx].copy()
                book['similarity_score'] = float(combined_scores[idx])
                book['semantic_score'] = float(semantic_scores[idx])
                book['keyword_score'] = float(keyword_scores[idx])
                results.append(book)
        
        return results
    
    def recommend_similar(
        self,
        isbn: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find books similar to a given book (by ISBN).
        
        Args:
            isbn: ISBN of the reference book
            top_k: Number of recommendations
        
        Returns:
            List of similar books
        """
        # Find the book
        book_idx = None
        for i, book in enumerate(self.books):
            if book.get('isbn') == isbn:
                book_idx = i
                break
        
        if book_idx is None:
            print(f"⚠ Book with ISBN {isbn} not found in index")
            return []
        
        # Get embedding
        book_embedding = self.embeddings[book_idx].reshape(1, -1)
        
        # Compute similarities
        similarities = cosine_similarity(book_embedding, self.embeddings)[0]
        
        # Get top-k (excluding the book itself)
        similarities[book_idx] = -1  # Exclude self
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Prepare results
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                book = self.books[idx].copy()
                book['similarity_score'] = float(similarities[idx])
                results.append(book)
        
        return results
    
    def get_statistics(self) -> Dict:
        """Get index statistics."""
        return {
            'total_books': len(self.books),
            'embedding_dimension': self.embeddings.shape[1] if self.embeddings is not None else 0,
            'model_name': self.model_name,
            'indexed': self.embeddings is not None
        }


def build_index_from_db():
    """
    Build search index from the SQLite database.
    Convenience function for the pipeline.
    """
    from storage.db import BookDatabase
    
    print("\n" + "="*70)
    print(" BUILDING SEARCH INDEX ".center(70, "="))
    print("="*70 + "\n")
    
    # Load books from database
    with BookDatabase() as db:
        books = db.get_recent_books(limit=100000)  # Get all books
    
    print(f"Loaded {len(books)} books from database")
    
    # Create search engine
    engine = SemanticSearchEngine()
    
    # Index books
    engine.index_books(books, force_reindex=True)
    
    # Show stats
    stats = engine.get_statistics()
    print(f"\n{'='*70}")
    print(" INDEX BUILD COMPLETE ".center(70, "="))
    print(f"{'='*70}\n")
    print(f"📊 Statistics:")
    print(f"  Total books indexed: {stats['total_books']}")
    print(f"  Embedding dimension: {stats['embedding_dimension']}")
    print(f"  Model: {stats['model_name']}")
    print()
    
    return engine


if __name__ == "__main__":
    build_index_from_db()


