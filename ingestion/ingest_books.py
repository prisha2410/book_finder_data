"""
Main ingestion script for reading books from CSV files.
This reads from data/books_data.csv and data/enriched_books.csv
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from typing import List, Dict


def read_books_from_csv(csv_path: str) -> List[Dict]:
    """
    Read books from a CSV file.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        List of book dictionaries
    """
    try:
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} rows from {csv_path}")
        
        # Convert to list of dictionaries
        books = []
        for _, row in df.iterrows():
            book = {
                'isbn': row.get('isbn') or row.get('ISBN') or row.get('isbn13'),
                'title': row.get('title') or row.get('Title'),
                'description': row.get('description') or row.get('Description'),
                'authors': row.get('authors') or row.get('author') or row.get('Author'),
                'genres': row.get('genres') or row.get('genre') or row.get('categories') or row.get('subjects'),
                'publish_date': row.get('publish_date') or row.get('published') or row.get('year')
            }
            books.append(book)
            
        return books
        
    except FileNotFoundError:
        print(f"⚠ File not found: {csv_path}")
        return []
    except Exception as e:
        print(f"✗ Error reading {csv_path}: {e}")
        return []


def ingest_all_books() -> List[Dict]:
    """
    Ingest books from all available CSV files.
    
    Returns:
        Combined list of all books
    """
    print("\n" + "="*60)
    print("INGESTION: Reading book data from CSV files")
    print("="*60)
    
    all_books = []
    
    # Read from books_data.csv
    books_data_path = "data/books_data.csv"
    if os.path.exists(books_data_path):
        books = read_books_from_csv(books_data_path)
        all_books.extend(books)
        print(f"  Added {len(books)} books from books_data.csv")
    
    # Read from enriched_books.csv
    enriched_path = "data/enriched_books.csv"
    if os.path.exists(enriched_path):
        books = read_books_from_csv(enriched_path)
        all_books.extend(books)
        print(f"  Added {len(books)} books from enriched_books.csv")
    
    print(f"\n✓ Total books ingested: {len(all_books)}")
    return all_books


if __name__ == "__main__":
    books = ingest_all_books()
    print(f"\nSample book: {books[0] if books else 'No books found'}")