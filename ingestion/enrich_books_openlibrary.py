"""
Parallel Book Enrichment Script
================================
Faster version using concurrent requests for large datasets.
Can process hundreds of books much more quickly.
"""

import requests
import pandas as pd
import time
from typing import Tuple, Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys


# API Configuration
OPENLIBRARY_SEARCH = "https://openlibrary.org/search.json"
OPENLIBRARY_WORK = "https://openlibrary.org"
OPENLIBRARY_ISBN = "https://openlibrary.org/isbn"
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"

# Parallel processing config
MAX_WORKERS = 5  # Number of parallel requests
REQUEST_DELAY = 0.2  # seconds between requests per worker


def detect_columns(df):
    """Detect title and ISBN columns."""
    title_col = None
    isbn_col = None
    
    for col in df.columns:
        if "title" in col.lower() and not title_col:
            title_col = col
        if any(k in col.lower() for k in ['isbn', 'isbn13', 'isbn10']) and not isbn_col:
            isbn_col = col
    
    if not title_col:
        raise ValueError(f"No title column found. Columns: {df.columns.tolist()}")
    
    return title_col, isbn_col


def fetch_openlibrary_work(title: str) -> Tuple[Optional[str], Optional[str]]:
    """Fetch from OpenLibrary by title."""
    try:
        params = {"title": title, "limit": 1}
        r = requests.get(OPENLIBRARY_SEARCH, params=params, timeout=8)
        
        if r.status_code != 200:
            return None, None
        
        docs = r.json().get("docs", [])
        if not docs:
            return None, None
        
        work_key = docs[0].get("key")
        if not work_key:
            return None, None
        
        # Get work details
        work_url = f"{OPENLIBRARY_WORK}{work_key}.json"
        work_r = requests.get(work_url, timeout=8)
        
        if work_r.status_code != 200:
            return None, None
        
        work_data = work_r.json()
        
        # Description
        desc = work_data.get("description")
        if isinstance(desc, dict):
            desc = desc.get("value")
        
        # Genres
        subjects = work_data.get("subjects", [])
        genre = ", ".join(subjects[:5]) if subjects else None
        
        return desc, genre
    
    except:
        return None, None


def fetch_google_books(title: str, isbn: str = None) -> Tuple[Optional[str], Optional[str]]:
    """Fetch from Google Books API."""
    try:
        query = f"isbn:{isbn}" if isbn else f"intitle:{title}"
        params = {"q": query, "maxResults": 1}
        
        r = requests.get(GOOGLE_BOOKS_API, params=params, timeout=8)
        
        if r.status_code != 200:
            return None, None
        
        items = r.json().get("items", [])
        if not items:
            return None, None
        
        vol_info = items[0].get("volumeInfo", {})
        
        desc = vol_info.get("description")
        cats = vol_info.get("categories", [])
        genre = ", ".join(cats[:5]) if cats else None
        
        return desc, genre
    
    except:
        return None, None


def process_single_book(book_data: Dict) -> Dict:
    """
    Process a single book with multiple API attempts.
    Returns enriched book data.
    """
    title = book_data['title']
    isbn = book_data.get('isbn')
    idx = book_data['index']
    
    description = None
    genre = None
    
    # Try OpenLibrary first
    description, genre = fetch_openlibrary_work(title)
    
    # If failed, try Google Books
    if not description or not genre:
        time.sleep(0.1)
        desc2, genre2 = fetch_google_books(title, isbn)
        description = description or desc2
        genre = genre or genre2
    
    return {
        'index': idx,
        'title': title,
        'description': description,
        'genre': genre,
        'success': bool(description)
    }


def enrich_parallel(csv_path: str, output_path: str, max_workers: int = MAX_WORKERS):
    """
    Enrich dataset using parallel processing.
    Much faster for large datasets.
    """
    print("\n" + "="*70)
    print(" PARALLEL BOOK ENRICHMENT ".center(70, "="))
    print("="*70 + "\n")
    
    # Read CSV
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
    except:
        try:
            df = pd.read_csv(csv_path, encoding="latin-1")
        except:
            df = pd.read_csv(csv_path, encoding="iso-8859-1")
    
    print(f"✓ Loaded {len(df)} books from {csv_path}")
    
    # Detect columns
    title_col, isbn_col = detect_columns(df)
    print(f"✓ Title column: '{title_col}'")
    if isbn_col:
        print(f"✓ ISBN column: '{isbn_col}'")
    
    # Prepare book data for processing
    books_to_process = []
    for idx, row in df.iterrows():
        books_to_process.append({
            'index': idx,
            'title': row[title_col],
            'isbn': row[isbn_col] if isbn_col else None
        })
    
    # Process in parallel
    print(f"\n🚀 Starting parallel processing with {max_workers} workers...")
    print(f"{'='*70}\n")
    
    results = []
    completed = 0
    success_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_book = {
            executor.submit(process_single_book, book): book 
            for book in books_to_process
        }
        
        # Process as they complete
        for future in as_completed(future_to_book):
            result = future.result()
            results.append(result)
            completed += 1
            
            if result['success']:
                success_count += 1
            
            # Progress update
            if completed % 20 == 0 or completed == len(books_to_process):
                progress = completed / len(books_to_process) * 100
                success_rate = success_count / completed * 100
                print(f"Progress: {completed}/{len(books_to_process)} ({progress:.1f}%) | "
                      f"Success: {success_count} ({success_rate:.1f}%)")
    
    # Sort results by index
    results.sort(key=lambda x: x['index'])
    
    # Add to dataframe
    df['description'] = [r['description'] for r in results]
    df['genre'] = [r['genre'] for r in results]
    
    # Statistics
    original_count = len(df)
    df = df.dropna(subset=['description'])
    final_count = len(df)
    
    # Save
    df.to_csv(output_path, index=False)
    
    # Final report
    print(f"\n{'='*70}")
    print(" ENRICHMENT COMPLETE ".center(70, "="))
    print(f"{'='*70}\n")
    
    print("📊 Final Statistics:")
    print(f"  Total books processed: {original_count}")
    print(f"  Books with descriptions: {success_count} ({success_count/original_count*100:.1f}%)")
    print(f"  Books saved (with descriptions): {final_count}")
    print(f"  Books removed (no description): {original_count - final_count}")
    
    print(f"\n✓ Saved to: {output_path}")
    print(f"✓ Ready for semantic search!\n")


def enrich_with_retry(csv_path: str, output_path: str, max_retries: int = 2):
    """
    Enrich with automatic retry for failed books.
    Maximizes data coverage.
    """
    print("\n" + "="*70)
    print(" ENRICHMENT WITH RETRY ".center(70, "="))
    print("="*70 + "\n")
    
    # First pass
    print("🔄 Pass 1: Initial enrichment...")
    enrich_parallel(csv_path, output_path, max_workers=MAX_WORKERS)
    
    # Check for failures
    df = pd.read_csv(output_path)
    total = len(df)
    with_desc = df['description'].notna().sum()
    
    print(f"\n📊 After Pass 1: {with_desc}/{total} books have descriptions")
    
    if with_desc < total and max_retries > 0:
        print(f"\n🔄 Retrying {total - with_desc} failed books...")
        
        # Extract failed books
        failed_df = df[df['description'].isna()].copy()
        
        if len(failed_df) > 0:
            # Save failed books
            failed_path = csv_path.replace('.csv', '_retry.csv')
            failed_df.to_csv(failed_path, index=False)
            
            # Retry enrichment
            time.sleep(2)  # Cool down
            enrich_parallel(failed_path, failed_path, max_workers=3)
            
            # Merge results
            retry_df = pd.read_csv(failed_path)
            
            # Update original dataframe
            for idx, row in retry_df.iterrows():
                if pd.notna(row['description']):
                    df.loc[df.index[idx], 'description'] = row['description']
                    df.loc[df.index[idx], 'genre'] = row['genre']
            
            # Save final version
            df = df.dropna(subset=['description'])
            df.to_csv(output_path, index=False)
            
            print(f"\n✓ Final count: {len(df)} books with descriptions")


if __name__ == "__main__":
    INPUT_CSV = "data/books_data.csv"
    OUTPUT_CSV = "data/enriched_books.csv"
    
    # Check for alternative filename
    import os
    if not os.path.exists(INPUT_CSV) and os.path.exists("data/books data.csv"):
        INPUT_CSV = "data/books data.csv"
    
    try:
        # Choose processing mode
        mode = input("\nChoose mode:\n  1. Fast parallel (recommended)\n  2. With automatic retry\n\nEnter 1 or 2: ").strip()
        
        if mode == "2":
            enrich_with_retry(INPUT_CSV, OUTPUT_CSV, max_retries=2)
        else:
            enrich_parallel(INPUT_CSV, OUTPUT_CSV)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
    except FileNotFoundError:
        print(f"\n✗ ERROR: File not found: {INPUT_CSV}")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()