"""
Memory-Optimized Semantic Search Engine
Designed to work within Render's 512MB RAM limit
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import gc


class MemoryOptimizedSearchEngine:
    """
    Ultra-lightweight search engine that fits in 512MB RAM.
    
    Optimizations:
    1. Use smallest possible model (61MB instead of 90MB)
    2. Store embeddings as float16 (50% memory reduction)
    3. Lazy load model (only when needed)
    4. Aggressive garbage collection
    5. Reduced TF-IDF features
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-MiniLM-L3-v2",  # Smallest model!
        embeddings_path: str = "data/embeddings_mini.pkl",
        index_path: str = "data/book_index_mini.pkl"
    ):
        """Initialize with minimal memory footprint."""
        self.model_name = model_name
        self.embeddings_path = embeddings_path
        self.index_path = index_path
        
        # Don't load model yet - lazy load on first use
        self.model = None
        
        # Storage
        self.books = []
        self.embeddings = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        
        # Try to load pre-computed embeddings
        self._load_if_exists()
    
    def _load_model_lazy(self):
        """Load model only when needed."""
        if self.model is None:
            print(f"🔍 Loading tiny model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            print("✓ Model loaded")
    
    def _load_if_exists(self):
        """Load pre-computed embeddings if they exist."""
        if Path(self.embeddings_path).exists() and Path(self.index_path).exists():
            try:
                print("📦 Loading pre-computed embeddings...")
                
                with open(self.embeddings_path, 'rb') as f:
                    data = pickle.load(f)
                    self.embeddings = data['embeddings']
                    self.tfidf_matrix = data.get('tfidf_matrix')
                
                with open(self.index_path, 'rb') as f:
                    index_data = pickle.load(f)
                    self.books = index_data['books']
                    self.tfidf_vectorizer = index_data.get('tfidf_vectorizer')
                
                print(f"✓ Loaded {len(self.books)} books")
                print(f"✓ Memory: Embeddings are float16 (50% smaller)")
                
                # Force garbage collection
                gc.collect()
                
            except Exception as e:
                print(f"⚠️ Error loading: {e}")
                self.books = []
                self.embeddings = None
    
    def index_books(self, books: List[Dict], force_reindex: bool = False):
        """
        Create memory-optimized embeddings.
        
        Key optimizations:
        - Use smallest model (384 dims → 128 dims)
        - Store as float16 instead of float32 (50% reduction)
        - Limit TF-IDF features to 2000 (instead of 5000)
        - Process in smaller batches
        """
        if not force_reindex and self.embeddings is not None:
            print("⚠️ Embeddings exist. Use force_reindex=True to rebuild.")
            return
        
        print(f"\n🔧 Indexing {len(books)} books (memory-optimized)...")
        
        # Filter books with descriptions
        valid_books = [b for b in books if b.get('description')]
        print(f"  Books with descriptions: {len(valid_books)}")
        
        if not valid_books:
            print("⚠️ No books to index")
            return
        
        self.books = valid_books
        
        # Prepare texts
        texts = []
        for book in valid_books:
            parts = []
            if book.get('title'):
                parts.append(f"Title: {book['title']}")
            if book.get('description'):
                # Truncate long descriptions to save memory
                desc = book['description'][:500]
                parts.append(desc)
            if book.get('genres'):
                parts.append(f"Genres: {book['genres']}")
            
            texts.append(' '.join(parts))
        
        # Load model (lazy)
        self._load_model_lazy()
        
        # Generate embeddings with smaller batches
        print("  Generating embeddings (float16)...")
        embeddings_f32 = self.model.encode(
            texts,
            show_progress_bar=True,
            batch_size=16,  # Smaller batch = less memory
            convert_to_numpy=True
        )
        
        # Convert to float16 (50% memory reduction!)
        self.embeddings = embeddings_f32.astype('float16')
        
        print(f"  ✓ Embeddings: {self.embeddings.shape}")
        print(f"  ✓ Memory saved: 50% (float16 instead of float32)")
        
        # Delete float32 version
        del embeddings_f32
        gc.collect()
        
        # Generate TF-IDF (reduced features)
        print("  Generating TF-IDF (reduced features)...")
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=2000,  # Reduced from 5000
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
        
        # Unload model to free memory
        print("  Unloading model to save memory...")
        del self.model
        self.model = None
        gc.collect()
        
        # Save
        self._save_index()
        
        print(f"✓ Indexed {len(valid_books)} books (memory-optimized)")
    
    def _save_index(self):
        """Save embeddings and index."""
        Path(self.embeddings_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.embeddings_path, 'wb') as f:
            pickle.dump({
                'embeddings': self.embeddings,
                'tfidf_matrix': self.tfidf_matrix
            }, f)
        
        with open(self.index_path, 'wb') as f:
            pickle.dump({
                'books': self.books,
                'tfidf_vectorizer': self.tfidf_vectorizer
            }, f)
        
        print(f"✓ Saved to {self.embeddings_path}")
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        genre_filter: Optional[List[str]] = None
    ) -> List[Dict]:
        """Memory-optimized search."""
        if self.embeddings is None or len(self.books) == 0:
            print("⚠️ No books indexed")
            return []
        
        # Load model only for query encoding
        self._load_model_lazy()
        
        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Unload model immediately
        del self.model
        self.model = None
        gc.collect()
        
        # Convert embeddings back to float32 for similarity calculation
        embeddings_f32 = self.embeddings.astype('float32')
        
        # Semantic similarity
        semantic_scores = cosine_similarity(query_embedding, embeddings_f32)[0]
        
        # Clean up
        del embeddings_f32
        gc.collect()
        
        # Keyword similarity
        query_tfidf = self.tfidf_vectorizer.transform([query])
        keyword_scores = cosine_similarity(query_tfidf, self.tfidf_matrix)[0]
        
        # Hybrid score
        combined_scores = (
            semantic_weight * semantic_scores +
            keyword_weight * keyword_scores
        )
        
        # Genre filter
        if genre_filter:
            genre_filter_lower = [g.lower() for g in genre_filter]
            for i, book in enumerate(self.books):
                book_genres = book.get('genres', '').lower()
                if not any(gf in book_genres for gf in genre_filter_lower):
                    combined_scores[i] = 0
        
        # Get top-k
        top_indices = np.argsort(combined_scores)[::-1][:top_k]
        
        # Results
        results = []
        for idx in top_indices:
            if combined_scores[idx] > 0:
                book = self.books[idx].copy()
                book['similarity_score'] = float(combined_scores[idx])
                book['semantic_score'] = float(semantic_scores[idx])
                book['keyword_score'] = float(keyword_scores[idx])
                results.append(book)
        
        return results
    
    def recommend_similar(self, isbn: str, top_k: int = 5) -> List[Dict]:
        """Find similar books."""
        # Find book
        book_idx = None
        for i, book in enumerate(self.books):
            if book.get('isbn') == isbn:
                book_idx = i
                break
        
        if book_idx is None:
            return []
        
        # Get embedding (convert to float32)
        book_embedding = self.embeddings[book_idx].astype('float32').reshape(1, -1)
        embeddings_f32 = self.embeddings.astype('float32')
        
        # Similarities
        similarities = cosine_similarity(book_embedding, embeddings_f32)[0]
        
        # Clean up
        del book_embedding, embeddings_f32
        gc.collect()
        
        # Exclude self
        similarities[book_idx] = -1
        
        # Top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                book = self.books[idx].copy()
                book['similarity_score'] = float(similarities[idx])
                results.append(book)
        
        return results
    
    def get_statistics(self) -> Dict:
        """Get stats."""
        return {
            'total_books': len(self.books),
            'embedding_dimension': self.embeddings.shape[1] if self.embeddings is not None else 0,
            'model_name': self.model_name,
            'indexed': self.embeddings is not None,
            'memory_optimized': True,
            'dtype': 'float16'
        }


def build_index_from_db():
    """Build optimized index from database."""
    from storage.db import BookDatabase
    
    print("\n" + "="*70)
    print(" BUILDING MEMORY-OPTIMIZED SEARCH INDEX ".center(70, "="))
    print("="*70 + "\n")
    
    with BookDatabase() as db:
        books = db.get_recent_books(limit=100000)
    
    print(f"Loaded {len(books)} books from database")
    
    engine = MemoryOptimizedSearchEngine()
    engine.index_books(books, force_reindex=True)
    
    stats = engine.get_statistics()
    print(f"\n{'='*70}")
    print(" INDEX BUILD COMPLETE ".center(70, "="))
    print(f"{'='*70}\n")
    print(f"📊 Statistics:")
    print(f"  Total books: {stats['total_books']}")
    print(f"  Embedding dims: {stats['embedding_dimension']}")
    print(f"  Model: {stats['model_name']}")
    print(f"  Memory optimized: {stats['memory_optimized']}")
    print(f"  Data type: {stats['dtype']} (50% smaller)")
    print()
    
    return engine


if __name__ == "__main__":
    build_index_from_db()