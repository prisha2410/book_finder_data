# LLM Usage Log

This document tracks all AI assistance used during the development of the Book Finder Data Pipeline project, in compliance with project transparency requirements.

---

## Session 1: Project Structure Guidance
**Date:** January 20, 2025  
**Tool:** ChatGPT (GPT-4)  
**Duration:** ~15 minutes

### Prompt 1: Project Structure
```
I need to build a data pipeline for book metadata. Can you suggest a modular 
folder structure that separates ingestion, transformation, and storage layers?
```

### Response:
```
For a modular data pipeline, I'd recommend this structure:

book_finder_data/
├── data/
│   ├── raw/              # Store original CSV files here
│   └── processed/        # Cleaned data and database
├── ingestion/
│   ├── __init__.py
│   └── csv_reader.py     # Read from CSV files
├── transformation/
│   ├── __init__.py
│   └── cleaner.py        # Data cleaning logic
├── storage/
│   ├── __init__.py
│   └── database.py       # SQLite operations
├── pipeline.py           # Main orchestrator
└── requirements.txt

Key principles:
- Separation of concerns: Each layer has a specific responsibility
- Use __init__.py to make folders proper Python packages
- Keep raw and processed data separate
- Have a central orchestrator (pipeline.py) that calls each stage

This makes it easy to test individual components and maintain the codebase.
```

**What I Implemented:**
- Used this general structure but renamed some folders (`transformation/` → my own naming)
- Added `api/` folder for FastAPI endpoints (not in original suggestion)
- Created `run_pipeline.py` as the main orchestrator
- Added `logs/` directory for LLM usage tracking

---

## Session 2: CSV Reading with Flexible Columns
**Date:** January 20, 2025  
**Tool:** Claude (Sonnet)  
**Duration:** ~10 minutes

### Prompt 1: Handling Different Column Names
```
How can I make my CSV reader handle different column names for the same field? 
For example, some CSVs have "isbn" while others have "ISBN" or "isbn13"
```

### Response:
```python
You can use dictionary.get() with fallback values to handle column name variations:

import pandas as pd

def read_books_from_csv(csv_path):
    df = pd.read_csv(csv_path)
    
    books = []
    for _, row in df.iterrows():
        book = {
            'isbn': row.get('isbn') or row.get('ISBN') or row.get('isbn13'),
            'title': row.get('title') or row.get('Title') or row.get('book_name'),
            'description': row.get('description') or row.get('desc'),
            # ... more fields
        }
        books.append(book)
    
    return books

The .get() method returns None if the key doesn't exist, so you can chain 
multiple attempts with 'or' operators. This gracefully handles different 
naming conventions without throwing KeyErrors.
```

**What I Implemented:**
- Applied the `.get()` chaining pattern in my `ingest_books.py`
- Extended to cover more variations: `authors/author/Author`, `genres/categories/subjects`
- Added my own variations based on actual CSV column names I encountered

---

### Prompt 2: Handling Missing CSV Files
```
What's the best way to handle missing CSV files gracefully without crashing 
the pipeline?
```

### Response:
```python
Use try-except blocks with specific exception handling:

def read_books_from_csv(csv_path):
    try:
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} rows from {csv_path}")
        # ... process data
        return books
        
    except FileNotFoundError:
        print(f"⚠ Warning: File not found: {csv_path}")
        return []  # Return empty list, don't crash
        
    except Exception as e:
        print(f"✗ Error reading {csv_path}: {e}")
        return []

This way:
- FileNotFoundError is expected for optional files
- Other exceptions are caught but logged
- Returning [] lets the pipeline continue
- The caller can check if books list is empty
```

**What I Implemented:**
- Added exact try-except structure to my CSV reader
- Used emoji indicators (✓, ✗, ⚠) for visual clarity
- Pipeline continues even if one CSV is missing

---

## Session 3: Data Cleaning
**Date:** January 21, 2025  
**Tool:** ChatGPT (GPT-4)  
**Duration:** ~20 minutes

### Prompt 1: Cleaning HTML from Descriptions
```
I have book descriptions with HTML tags like <p> and entities like &amp;. 
What's the cleanest way to remove these in Python?
```

### Response:
```python
import re
import html

def clean_description(text):
    if not text:
        return None
    
    # Decode HTML entities (&amp; -> &, &quot; -> ")
    text = html.unescape(text)
    
    # Remove HTML tags using regex
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up extra whitespace
    text = ' '.join(text.split())
    
    return text.strip()

The html.unescape() function handles all HTML entities automatically.
The regex pattern <[^>]+> matches any HTML tag (anything between < and >).
The .split() and join() trick normalizes all whitespace to single spaces.
```

**What I Implemented:**
- Used `html.unescape()` in my cleaning function
- Modified regex to match my specific HTML patterns
- Added check for empty/None values before processing

---

### Prompt 2: ISBN Validation
```
How can I validate that an ISBN is properly formatted? Should be 10 or 13 digits.
```

### Response:
```python
def is_valid_isbn(isbn):
    if not isbn:
        return False
    
    # Remove common separators
    isbn = isbn.replace('-', '').replace(' ', '').strip()
    
    # Check if all characters are digits
    if not isbn.isdigit():
        return False
    
    # Valid ISBNs are either 10 or 13 digits
    return len(isbn) in [10, 13]

ISBN-10: 10 digits
ISBN-13: 13 digits (starts with 978 or 979)

You could add more sophisticated validation (check digit verification),
but for most use cases, this length + digit check is sufficient.
```

**What I Implemented:**
- Created `is_valid_isbn()` function based on this
- Added it to my data cleaning pipeline
- Filters out invalid ISBNs before database insertion

---

## Session 4: SQLite Database Design
**Date:** January 21, 2025  
**Tool:** Claude (Sonnet)  
**Duration:** ~25 minutes

### Prompt 1: Database Schema
```
I need to design a SQLite table for storing book metadata. Fields include 
isbn, title, description, authors, genres, and publish_date. What's a good schema?
```

### Response:
```sql
CREATE TABLE books (
    isbn TEXT PRIMARY KEY,           -- Unique identifier
    title TEXT NOT NULL,              -- Required field
    description TEXT,                 -- Can be NULL
    authors TEXT,                     -- Comma-separated
    genres TEXT,                      -- Comma-separated
    publish_date TEXT,                -- ISO format YYYY-MM-DD
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for efficient queries on recent books
CREATE INDEX idx_created_at ON books(created_at DESC);

Design decisions:
- ISBN as PRIMARY KEY ensures uniqueness
- TEXT type for most fields (SQLite doesn't have native string types)
- created_at tracks when record was inserted
- Index on created_at helps with "recent books" queries
- Authors/genres as TEXT with comma-separation (simple, no joins needed)

For a more normalized design, you could create separate tables for authors 
and genres with many-to-many relationships, but this adds complexity.
```

**What I Implemented:**
- Used exact schema structure in `storage/db.py`
- Added the `idx_created_at` index for performance
- Kept comma-separated authors/genres (simpler for this project)

---

### Prompt 2: Batch Insertion Pattern
```
What's the efficient way to insert multiple books into SQLite? Should I commit 
after each insert or batch them?
```

### Response:
```python
def insert_books_batch(self, books):
    inserted = 0
    duplicates = 0
    
    for book in books:
        try:
            self.cursor.execute("""
                INSERT INTO books (isbn, title, description, authors, genres, publish_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (book['isbn'], book['title'], book['description'], 
                  book['authors'], book['genres'], book['publish_date']))
            inserted += 1
        except sqlite3.IntegrityError:
            # Duplicate ISBN (primary key violation)
            duplicates += 1
    
    # Commit once after all inserts
    self.conn.commit()
    
    return inserted, duplicates

Key points:
- Loop through all records first
- Catch IntegrityError for duplicates (don't crash)
- Commit ONCE at the end (much faster than commit per insert)
- Return statistics for logging
```

**What I Implemented:**
- Used this exact pattern in my `insert_books_batch()` method
- Added tracking for inserted and duplicate counts
- Single commit after loop

---

## Session 5: FastAPI Implementation
**Date:** January 22, 2025  
**Tool:** ChatGPT (GPT-4)  
**Duration:** ~15 minutes

### Prompt 1: Creating REST Endpoints
```
I need to create REST API endpoints to serve book data from SQLite. 
How do I structure a FastAPI app with routes for fetching books?
```

### Response:
```python
from fastapi import FastAPI, HTTPException
from typing import List, Optional

app = FastAPI(title="Book Finder API")

@app.get("/books")
def get_books(limit: int = 1000):
    """Fetch recent books"""
    with BookDatabase() as db:
        books = db.get_recent_books(limit=min(limit, 1000))
    return books

@app.get("/books/{isbn}")
def get_book_by_isbn(isbn: str):
    """Get specific book by ISBN"""
    with BookDatabase() as db:
        book = db.get_book_by_isbn(isbn)
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return book

@app.post("/sync")
def sync_data():
    """Trigger data sync"""
    # Run your pipeline here
    return {"status": "sync completed"}

Key features:
- @app.get() decorator for GET endpoints
- Path parameters: {isbn}
- Query parameters: limit with default value
- HTTPException for 404 errors
- Automatic OpenAPI docs at /docs
```

**What I Implemented:**
- Created `api/main.py` with these endpoints
- Added limit parameter with max value check
- Used context manager pattern for database connections

---

## Session 6: OpenLibrary API Integration
**Date:** January 22, 2025  
**Tool:** Claude (Sonnet)  
**Duration:** ~30 minutes

### Prompt 1: Using OpenLibrary Search API
```
How do I use the OpenLibrary API to search for books by title and get descriptions?
I need to understand the JSON structure of their responses.
```

### Response:
```python
import requests

def fetch_book_data(title):
    # Step 1: Search for book by title
    search_url = "https://openlibrary.org/search.json"
    params = {"title": title, "limit": 1}
    
    response = requests.get(search_url, params=params, timeout=10)
    data = response.json()
    
    docs = data.get("docs", [])
    if not docs:
        return None, None
    
    # Step 2: Get work key from search results
    work_key = docs[0].get("key")  # e.g., "/works/OL45804W"
    
    # Step 3: Fetch detailed work information
    work_url = f"https://openlibrary.org{work_key}.json"
    work_response = requests.get(work_url, timeout=10)
    work_data = work_response.json()
    
    # Extract description (can be string or dict)
    description = work_data.get("description")
    if isinstance(description, dict):
        description = description.get("value")
    
    # Extract genres from subjects
    subjects = work_data.get("subjects", [])
    genres = ", ".join(subjects[:5]) if subjects else None
    
    return description, genres

The API returns:
- search.json: List of matching books with basic info
- /works/{key}.json: Detailed information including description
- description can be plain string OR {"type": "...", "value": "..."}
```

**What I Implemented:**
- Used this two-step approach in `enrich_books_openlibrary.py`
- Added error handling for both API calls
- Limited genres to first 5 subjects

---

### Prompt 2: API Rate Limiting
```
Should I add delays between API calls to OpenLibrary? What's respectful?
```

### Response:
```python
import time

for title in titles:
    description, genre = fetch_book_data(title)
    # ... store data
    
    time.sleep(0.2)  # 200ms delay between requests

Best practices for free APIs:
- 0.2-0.5 seconds between requests is respectful
- Prevents overwhelming the server
- OpenLibrary doesn't publish explicit rate limits
- Better to be conservative with free services
- Add timeout parameter to requests (e.g., timeout=10)
- Use try-except for network errors

Also consider:
- Caching results to avoid repeated calls
- Batch processing during off-peak hours
- Exponential backoff if you get rate limited
```

**What I Implemented:**
- Added `time.sleep(0.2)` between API calls
- Set 10-second timeout on all requests
- Wrapped in try-except for error handling

---

## Session 7: Pipeline Orchestration
**Date:** January 23, 2025  
**Tool:** ChatGPT (GPT-4)  
**Duration:** ~10 minutes

### Prompt 1: Error Handling Strategy
```
If one part of my pipeline fails, should the whole thing crash or continue?
How do I handle partial failures?
```

### Response:
```python
def run_pipeline():
    # Step 1: Ingestion
    try:
        books = ingest_all_books()
        if not books:
            print("ERROR: No books found, stopping pipeline")
            return  # Critical failure, must stop
    except Exception as e:
        print(f"CRITICAL ERROR in ingestion: {e}")
        return
    
    # Step 2: Transformation
    try:
        cleaned_books = clean_all_books(books)
        if not cleaned_books:
            print("WARNING: No valid books after cleaning")
            return
    except Exception as e:
        print(f"ERROR in transformation: {e}")
        return
    
    # Step 3: Storage
    try:
        with BookDatabase() as db:
            db.create_schema()
            inserted, duplicates = db.insert_books_batch(cleaned_books)
            print(f"Success: {inserted} inserted, {duplicates} duplicates")
    except Exception as e:
        print(f"CRITICAL ERROR in storage: {e}")
        return

Guidelines:
- Stop for CRITICAL errors (no data, database failure)
- Continue for OPTIONAL errors (missing one CSV file)
- Log everything with clear severity (ERROR vs WARNING)
- Return statistics to show partial success
```

**What I Implemented:**
- Used this error handling pattern in `run_pipeline.py`
- Added visual indicators (✓, ✗, ⚠) to error messages
- Pipeline stops only for critical failures

---

## Session 8: Documentation
**Date:** January 24, 2025  
**Tool:** Claude (Sonnet)  
**Duration:** ~12 minutes

### Prompt 1: README Best Practices
```
What sections should I include in a README for a data pipeline project?
```

### Response:
```markdown
Essential README sections for a data pipeline:

1. **Project Title & Description**
   - One-line summary of what it does
   - Key features/capabilities

2. **Architecture Diagram**
   - Visual representation of data flow
   - Can be ASCII art or embedded image

3. **Quick Start**
   - Installation steps
   - Minimal example to run pipeline

4. **API Documentation**
   - Endpoint descriptions
   - Request/response examples
   - curl commands for testing

5. **Database Schema**
   - Table structure
   - Column descriptions
   - Indexes

6. **Data Sources**
   - Where data comes from
   - How to add new sources

7. **Configuration**
   - Environment variables
   - Config files

8. **Testing**
   - How to validate the pipeline works
   - Sample outputs

9. **Next Steps**
   - Future enhancements
   - How others can extend it

10. **Troubleshooting**
    - Common issues and solutions

Use tables, code blocks, and clear hierarchy for readability.
```

**What I Implemented:**
- Created comprehensive README with these sections
- Added ASCII architecture diagram
- Included code examples and curl commands
- Made it beginner-friendly with detailed explanations

---

## Summary Statistics

**Total Sessions:** 8  
**Total Prompts:** 11  
**Tools Used:**
- ChatGPT (GPT-4): 5 sessions
- Claude (Sonnet): 3 sessions

**Code Implementation Approach:**
- Received code examples and patterns from LLM
- Understood the logic and best practices
- Implemented in my own style with modifications
- Added project-specific features and error handling
- Modified variable names and structure to fit my needs

**Key Learnings:**
1. Modular architecture with separation of concerns
2. Context managers for resource management
3. Graceful error handling and recovery
4. RESTful API design principles
5. Database indexing for performance
6. Rate limiting etiquette for external APIs
