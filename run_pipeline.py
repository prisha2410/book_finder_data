"""
Main pipeline orchestration script.
Runs the complete ETL pipeline: Ingestion -> Transformation -> Storage
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ingestion.ingest_books import ingest_all_books
from transformation.clean_books import clean_all_books
from storage.db import BookDatabase


def run_pipeline():
    """Execute the complete data pipeline."""
    
    print("\n" + "="*70)
    print(" BOOK FINDER DATA PIPELINE ".center(70, "="))
    print("="*70 + "\n")
    
    # STEP 1: INGESTION
    print("STEP 1: INGESTION")
    print("-" * 70)
    raw_books = ingest_all_books()
    
    if not raw_books:
        print("\n✗ No books found. Please add CSV files to data/ directory.")
        print("  Expected files: data/books_data.csv or data/enriched_books.csv")
        return
    
    # STEP 2: TRANSFORMATION
    print("\n" + "="*70)
    print("STEP 2: TRANSFORMATION")
    print("-" * 70)
    cleaned_books = clean_all_books(raw_books)
    
    if not cleaned_books:
        print("\n✗ No valid books after cleaning.")
        return
    
    # STEP 3: STORAGE
    print("\n" + "="*70)
    print("STEP 3: STORAGE")
    print("-" * 70)
    
    with BookDatabase() as db:
        # Create schema
        db.create_schema()
        
        # Insert books
        print(f"\nInserting {len(cleaned_books)} books into database...")
        inserted, duplicates = db.insert_books_batch(cleaned_books)
        
        print(f"✓ Inserted: {inserted} books")
        print(f"⚠ Skipped: {duplicates} duplicates")
        
        # Show statistics
        stats = db.get_statistics()
        print(f"\n📊 Database Statistics:")
        print(f"  Total books: {stats['total_books']}")
        print(f"  Books with descriptions: {stats['books_with_descriptions']}")
        print(f"  Database size: {stats['database_size_mb']:.2f} MB")
    
    # COMPLETION
    print("\n" + "="*70)
    print(" PIPELINE COMPLETED SUCCESSFULLY ✓ ".center(70, "="))
    print("="*70)
    print("\nNext steps:")
    print("  1. Start the API server: uvicorn api.main:app --reload")
    print("  2. Test the API: http://localhost:8000/books")
    print("  3. View docs: http://localhost:8000/docs")
    print()


if __name__ == "__main__":
    try:
        run_pipeline()
    except KeyboardInterrupt:
        print("\n\n⚠ Pipeline interrupted by user.")
    except Exception as e:
        print(f"\n\n✗ Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()