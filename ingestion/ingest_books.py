"""
Main ingestion script for reading books from CSV files.
Scans the data/ directory and ingests every .csv file it finds —
no hardcoded filenames, just drop a file in and run.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import glob
import pandas as pd
from typing import List, Dict

# Root directory that gets scanned for CSV files
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _pick(row, *keys):
    """Return the first non-null value from a row for the given key list."""
    for k in keys:
        val = row.get(k)
        if val is not None and str(val).strip() not in ("", "nan", "NaN", "None"):
            return val
    return None


def read_books_from_csv(csv_path: str) -> List[Dict]:
    """
    Read books from a CSV file.

    Supports both the original simple schema AND the enriched
    FINAL_MASTER schema produced by the OpenLibrary / OpenAlex
    enrichment pipelines.  Priority order for each field:

        isbn            -> ISBN, isbn, isbn13
        title           -> Title, title, book_title
        authors         -> Author/Editor, ol_authors, authors, author
        description     -> final_description, ol_description, oa_abstract, description
        genres/subjects -> final_subjects, ol_subjects, subjects, genres, categories
        publish_date    -> Year, ol_publish_date, oa_year, publish_date, published

    Args:
        csv_path: Path to CSV file

    Returns:
        List of book dictionaries
    """
    try:
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} rows from {csv_path}")
        print(f"  Columns detected: {df.columns.tolist()}\n")

        books = []
        for _, row in df.iterrows():
            book = {
                'isbn': _pick(row,
                              'ISBN', 'isbn', 'isbn13', 'isbn10'),

                'title': _pick(row,
                               'Title', 'title', 'book_title', 'book_name'),

                'authors': _pick(row,
                                 'Author/Editor', 'ol_authors',
                                 'authors', 'author', 'Author'),

                'description': _pick(row,
                                     'final_description', 'ol_description',
                                     'oa_abstract', 'description', 'Description'),

                'genres': _pick(row,
                                'final_subjects', 'ol_subjects',
                                'subjects', 'genres', 'genre', 'categories'),

                'publish_date': _pick(row,
                                      'Year', 'ol_publish_date', 'oa_year',
                                      'publish_date', 'published', 'year'),
            }
            books.append(book)

        return books

    except FileNotFoundError:
        print(f"⚠ File not found: {csv_path}")
        return []
    except Exception as e:
        print(f"✗ Error reading {csv_path}: {e}")
        return []


def ingest_all_books(data_dir: str = None) -> List[Dict]:
    """
    Ingest books from every .csv file found in the data directory.

    Args:
        data_dir: Path to the directory to scan (default: project's data/ folder).
                  Pass any other path to override.

    Returns:
        Combined list of all books across all CSV files
    """
    if data_dir is None:
        data_dir = DATA_DIR
    data_dir = os.path.abspath(data_dir)

    print("\n" + "=" * 60)
    print("INGESTION: Reading book data from CSV files")
    print("=" * 60)
    print(f"  Scanning: {data_dir}")

    # Find every .csv in data_dir (non-recursive, top-level only)
    pattern   = os.path.join(data_dir, "*.csv")
    csv_files = sorted(glob.glob(pattern))

    if not csv_files:
        print(f"\n⚠ No .csv files found in {data_dir}")
        return []

    print(f"  Found {len(csv_files)} CSV file(s):\n")

    all_books = []
    for csv_path in csv_files:
        books = read_books_from_csv(csv_path)
        all_books.extend(books)
        print(f"  Added {len(books)} books from {os.path.basename(csv_path)}")

    print(f"\n✓ Total books ingested: {len(all_books)}")
    return all_books


def print_stats(data_dir: str = None):
    """
    Print detailed statistics about every CSV in the data directory.
    Useful for generating the Pipeline Statistics section of the README.

    Args:
        data_dir: Path to the directory to scan (default: project's data/ folder).
    """
    if data_dir is None:
        data_dir = DATA_DIR
    data_dir = os.path.abspath(data_dir)

    pattern   = os.path.join(data_dir, "*.csv")
    csv_files = sorted(glob.glob(pattern))

    if not csv_files:
        print(f"\n⚠ No .csv files found in {data_dir}")
        return

    grand_total = 0

    for csv_path in csv_files:
        print("\n" + "=" * 70)
        print(f" {os.path.basename(csv_path)}")
        print("=" * 70)

        df = pd.read_csv(csv_path)
        total = len(df)
        grand_total += total

        print(f"  Total rows          : {total}")
        print(f"  Total columns       : {len(df.columns)}")

        # --- per-field coverage using the same priority chains as ingestion ---
        fields = {
            'isbn':         ['ISBN', 'isbn', 'isbn13', 'isbn10'],
            'title':        ['Title', 'title', 'book_title', 'book_name'],
            'authors':      ['Author/Editor', 'ol_authors', 'authors', 'author', 'Author'],
            'description':  ['final_description', 'ol_description', 'oa_abstract', 'description'],
            'genres':       ['final_subjects', 'ol_subjects', 'subjects', 'genres', 'categories'],
            'publish_date': ['Year', 'ol_publish_date', 'oa_year', 'publish_date', 'published'],
        }

        print(f"\n  {'Field':<15} {'Non-null':<10} {'% Coverage':<12} {'Source column'}")
        print(f"  {'-'*15} {'-'*10} {'-'*12} {'-'*25}")

        for field, candidates in fields.items():
            # walk the priority list; first column that exists and has data wins
            for col in candidates:
                if col in df.columns:
                    count = df[col].apply(
                        lambda v: v is not None and str(v).strip() not in ("", "nan", "NaN", "None")
                    ).sum()
                    if count > 0:
                        pct = count / total * 100
                        print(f"  {field:<15} {count:<10} {pct:<12.1f} {col}")
                        break
            else:
                print(f"  {field:<15} {'0':<10} {'0.0':<12} (none found)")

        # --- duplicate ISBNs ---
        isbn_col = next((c for c in ['ISBN', 'isbn', 'isbn13'] if c in df.columns), None)
        if isbn_col:
            dupes = df[isbn_col].notna().sum() - df[isbn_col].nunique()
            print(f"\n  Duplicate ISBNs     : {dupes}")

        # --- flag columns if present (from enrichment pipeline) ---
        if 'has_final_description' in df.columns:
            print(f"  has_final_description=1 : {(df['has_final_description'] == 1).sum()}")
        if 'has_final_subjects' in df.columns:
            print(f"  has_final_subjects=1    : {(df['has_final_subjects'] == 1).sum()}")

    print("\n" + "=" * 70)
    print(f"  GRAND TOTAL rows across all CSVs: {grand_total}")
    print("=" * 70)


if __name__ == "__main__":
    import fire
    fire.Fire({
        "ingest_all_books":    ingest_all_books,
        "read_books_from_csv": read_books_from_csv,
        "print_stats":         print_stats,
    })