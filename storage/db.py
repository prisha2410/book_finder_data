"""
Database module for SQLite operations.
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Optional
import fire


class BookDatabase:
    """Manages SQLite database operations for books."""
    
    def __init__(self, db_path: str = "data/books.db"):
        """Initialize database connection."""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def create_schema(self):
        """Create books table."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                isbn TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                authors TEXT,
                genres TEXT,
                publish_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on created_at
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON books(created_at DESC)
        """)
        
        self.conn.commit()
        print("✓ Database schema created")
    
    def insert_book(self, book: Dict) -> bool:
        """Insert a single book."""
        try:
            self.cursor.execute("""
                INSERT INTO books (isbn, title, description, authors, genres, publish_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                book.get('isbn'),
                book.get('title'),
                book.get('description'),
                book.get('authors'),
                book.get('genres'),
                book.get('publish_date')
            ))
            return True
        except sqlite3.IntegrityError:
            return False
    
    def insert_books_batch(self, books: List[Dict]) -> tuple:
        """Insert multiple books."""
        inserted = 0
        duplicates = 0
        
        for book in books:
            if self.insert_book(book):
                inserted += 1
            else:
                duplicates += 1
        
        self.conn.commit()
        return inserted, duplicates
    
    def get_recent_books(self, limit: int = 1000) -> List[Dict]:
        """Fetch recent books."""
        self.cursor.execute("""
            SELECT isbn, title, description, authors, genres, publish_date, created_at
            FROM books
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_book_by_isbn(self, isbn: str) -> Optional[Dict]:
        """Fetch book by ISBN."""
        self.cursor.execute("""
            SELECT isbn, title, description, authors, genres, publish_date, created_at
            FROM books
            WHERE isbn = ?
        """, (isbn,))
        
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def count_books(self) -> int:
        """Get total book count."""
        self.cursor.execute("SELECT COUNT(*) FROM books")
        return self.cursor.fetchone()[0]
    
    def count_books_with_descriptions(self) -> int:
        """Count books with descriptions."""
        self.cursor.execute("""
            SELECT COUNT(*) FROM books 
            WHERE description IS NOT NULL AND description != ''
        """)
        return self.cursor.fetchone()[0]
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        return {
            'total_books': self.count_books(),
            'books_with_descriptions': self.count_books_with_descriptions(),
            'database_size_mb': Path(self.db_path).stat().st_size / (1024 * 1024) if os.path.exists(self.db_path) else 0
        }


if __name__ == "__main__":
    # Test database
    with BookDatabase() as db:
        db.create_schema()
        print(f"Statistics: {db.get_statistics()}")
    
    fire.Fire(BookDatabase)