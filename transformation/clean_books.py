"""
Book cleaning and transformation script.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import html
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


INVALID_DESCRIPTIONS = [
    'description not available',
    'no description',
    'coming soon',
    'n/a',
    'tbd',
    '[no description]'
]


def clean_text(text: str) -> Optional[str]:
    """Remove HTML tags and fix encoding."""
    if not text or not isinstance(text, str):
        return None
    
    # Remove HTML tags
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text()
    
    # Decode HTML entities (e.g., &amp; -> &)
    text = html.unescape(text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text if text else None


def clean_description(description: str) -> Optional[str]:
    """Clean and validate book description."""
    cleaned = clean_text(description)
    
    if not cleaned:
        return None
    
    # Check for invalid phrases
    cleaned_lower = cleaned.lower()
    for invalid in INVALID_DESCRIPTIONS:
        if invalid in cleaned_lower:
            return None
    
    # Minimum length check
    if len(cleaned) < 20:
        return None
    
    # Truncate if too long
    if len(cleaned) > 5000:
        cleaned = cleaned[:5000]
    
    return cleaned


def normalize_isbn(isbn: str) -> Optional[str]:
    """Normalize ISBN format."""
    if not isbn or not isinstance(isbn, str):
        return None
    
    # Remove hyphens and spaces
    isbn = str(isbn).replace('-', '').replace(' ', '').strip()
    
    # Validate length
    if not (len(isbn) == 10 or len(isbn) == 13):
        return None
    
    # Check if valid
    if not (isbn.isdigit() or (len(isbn) == 10 and isbn[-1].upper() == 'X')):
        return None
    
    return isbn.upper()


def normalize_authors(authors: any) -> Optional[str]:
    """Normalize author names."""
    if not authors:
        return None
    
    if isinstance(authors, list):
        authors = [clean_text(str(a)) for a in authors if a]
        authors = [a for a in authors if a]
        return ', '.join(authors) if authors else None
    
    if isinstance(authors, str):
        return clean_text(authors)
    
    return None


def normalize_genres(genres: any) -> Optional[str]:
    """Normalize genre names."""
    if not genres:
        return None
    
    if isinstance(genres, list):
        genres = [clean_text(str(g)) for g in genres if g]
        genres = [g for g in genres if g]
        genres = genres[:5]  # Limit to 5
        return ', '.join(genres) if genres else None
    
    if isinstance(genres, str):
        return clean_text(genres)
    
    return None


def normalize_date(date_str: any) -> Optional[str]:
    """Normalize date to YYYY-MM-DD."""
    if not date_str:
        return None
    
    # Handle year as integer or float
    if isinstance(date_str, (int, float)):
        year = int(date_str)
        if 1000 <= year <= 9999:
            return f"{year}-01-01"
        return None
    
    if isinstance(date_str, str):
        date_str = date_str.strip()
        
        # YYYY-MM-DD format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str
        
        # YYYY format
        if re.match(r'^\d{4}$', date_str):
            return f"{date_str}-01-01"
        
        # Extract year
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', date_str)
        if year_match:
            return f"{year_match.group(1)}-01-01"
    
    return None


def clean_book(raw_book: Dict) -> Optional[Dict]:
    """Clean a single book record."""
    # Normalize ISBN (required)
    isbn = normalize_isbn(raw_book.get('isbn'))
    if not isbn:
        return None
    
    # Normalize title (required)
    title = clean_text(raw_book.get('title'))
    if not title or len(title) < 1:
        return None
    
    # Truncate title if too long
    if len(title) > 500:
        title = title[:500]
    
    # Clean description
    description = clean_description(raw_book.get('description'))
    
    # Normalize other fields
    authors = normalize_authors(raw_book.get('authors'))
    genres = normalize_genres(raw_book.get('genres'))
    publish_date = normalize_date(raw_book.get('publish_date'))
    
    return {
        'isbn': isbn,
        'title': title,
        'description': description,
        'authors': authors,
        'genres': genres,
        'publish_date': publish_date
    }


def clean_all_books(raw_books: List[Dict]) -> List[Dict]:
    """Clean multiple book records."""
    print(f"\nCleaning {len(raw_books)} books...")
    
    cleaned = []
    skipped = 0
    
    for raw_book in raw_books:
        clean = clean_book(raw_book)
        if clean:
            cleaned.append(clean)
        else:
            skipped += 1
    
    print(f"✓ Cleaned: {len(cleaned)} books")
    print(f"⚠ Skipped: {skipped} invalid records")
    
    return cleaned


if __name__ == "__main__":
    # Test cleaning
    test_book = {
        'isbn': '978-0-123-45678-9',
        'title': 'Test Book',
        'description': '<p>This is a &amp; test description</p>',
        'authors': ['John Doe', 'Jane Smith'],
        'genres': 'Fiction, Fantasy',
        'publish_date': 2024
    }
    
    cleaned = clean_book(test_book)
    print(f"Test result: {cleaned}")