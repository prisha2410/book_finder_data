# 📚 Book Finder Data Pipeline

> A production-ready ETL pipeline that extracts, transforms, and loads book metadata from multiple sources into a queryable SQLite database, designed to power ML-based semantic search applications.

## 🎯 Overview

This project implements a complete data engineering solution for book metadata aggregation. It combines data from CSV files and the OpenLibrary API, applies robust data cleaning transformations, and serves the processed data through a FastAPI REST interface.

**Key Features:**
- Multi-source data ingestion (CSV + REST API)
- Intelligent data cleaning and normalization
- Relational database storage with SQLite
- RESTful API for downstream consumption
- Comprehensive error handling and logging

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────┐     ┌─────────┐
│   CSV Files │────▶│  Ingestion   │────▶│  Clean   │────▶│ SQLite  │
│ OpenLibrary │     │   Layer      │     │Transform │     │   DB    │
└─────────────┘     └──────────────┘     └──────────┘     └────┬────┘
                                                                 │
                                                                 ▼
                                                          ┌──────────┐
                                                          │ FastAPI  │
                                                          │   REST   │
                                                          └──────────┘
```

## 📂 Project Structure

```
book_finder_data/
├── data/
│   ├── raw/                       # Source CSV files
│   ├── processed/                 # Generated SQLite database
│   ├── books_data.csv            # Primary dataset
│   └── enriched_books.csv        # API-enriched dataset
├── ingestion/
│   ├── ingest_books.py           # CSV ingestion logic
│   └── enrich_books_openlibrary.py  # API enrichment
├── transformation/
│   └── clean_books.py            # Data cleaning pipeline
├── storage/
│   └── db.py                     # SQLite ORM layer
├── api/
│   └── main.py                   # FastAPI application
├── logs/
│   └── llm_usage.md              # LLM assistance log
├── run_pipeline.py               # Main orchestrator
├── requirements.txt              # Python dependencies
├── DATA_DICTIONARY.md            # Schema documentation
└── README.md                     # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd book_finder_data
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare data directory**
   ```bash
   mkdir -p data/raw data/processed
   ```

### Running the Pipeline

**Execute the complete ETL pipeline:**
```bash
python run_pipeline.py
```

**Pipeline execution flow:**
1. ✅ Reads books from `data/books_data.csv` and `data/enriched_books.csv`
2. ✅ Cleans HTML entities, normalizes ISBNs, validates dates
3. ✅ Removes duplicates and entries without descriptions
4. ✅ Stores cleaned data in `data/books.db`
5. ✅ Displays comprehensive statistics

### Starting the API Server

```bash
uvicorn api.main:app --reload --port 8000
```

**Interactive API documentation:** http://localhost:8000/docs

## 📡 API Reference

### Fetch Books
```http
GET /books?limit=100
```
**Parameters:**
- `limit` (optional): Number of records to return (default: 1000, max: 1000)

**Response:**
```json
[
  {
    "isbn": "9780141439518",
    "title": "Pride and Prejudice",
    "description": "A classic novel of manners...",
    "authors": "Jane Austen",
    "genres": "Fiction, Romance, Classics",
    "publish_date": "1813-01-28",
    "created_at": "2025-01-24T10:30:00"
  }
]
```

### Get Book by ISBN
```http
GET /books/{isbn}
```

**Example:**
```bash
curl http://localhost:8000/books/9780141439518
```

### Trigger Data Sync
```http
POST /sync
```
Manually re-runs the ETL pipeline to update the database.

## 🗄️ Database Schema

**Table:** `books`

| Column        | Type      | Constraints    | Description                     |
|---------------|-----------|----------------|---------------------------------|
| isbn          | TEXT      | PRIMARY KEY    | Unique ISBN-13 or ISBN-10       |
| title         | TEXT      | NOT NULL       | Book title                      |
| description   | TEXT      | NULLABLE       | Cleaned book description        |
| authors       | TEXT      | NULLABLE       | Comma-separated author names    |
| genres        | TEXT      | NULLABLE       | Comma-separated genre tags      |
| publish_date  | TEXT      | NULLABLE       | ISO 8601 format (YYYY-MM-DD)   |
| created_at    | TIMESTAMP | DEFAULT NOW    | Record insertion timestamp      |

**Indexes:**
- `idx_created_at` on `created_at DESC` for efficient recent book queries

Refer to [DATA_DICTIONARY.md](DATA_DICTIONARY.md) for detailed schema documentation.

## 🧹 Data Transformation

The pipeline applies the following transformations:

| Transformation         | Description                                          |
|------------------------|------------------------------------------------------|
| HTML Cleaning          | Removes `<p>`, `<br>`, `<div>` and other tags       |
| Entity Decoding        | Converts `&amp;` → `&`, `&quot;` → `"`             |
| ISBN Validation        | Ensures 10 or 13 digit ISBNs, removes hyphens       |
| Duplicate Removal      | Deduplicates by ISBN                                |
| Description Filtering  | Drops books without descriptions                    |
| Date Normalization     | Standardizes to YYYY-MM-DD format                   |

## 📥 Adding New Data Sources

### CSV Files

Place CSV files in `data/raw/` with flexible column naming:

| Standard Field | Accepted Variations                          |
|----------------|---------------------------------------------|
| isbn           | isbn, isbn13, isbn10, ISBN                  |
| title          | title, book_name, book_title, Title         |
| description    | description, blurb, summary, desc           |
| authors        | authors, author, author_name                |
| genres         | genres, genre, categories, subjects         |
| publish_date   | publish_date, published, publication_date, year |

The ingestion module automatically maps these variants to the standard schema.

### API Enrichment

Use the OpenLibrary enrichment script to add descriptions and genres:

```bash
python ingestion/enrich_books_openlibrary.py
```

This fetches metadata for books in `data/books_data.csv` and outputs to `data/enriched_books.csv`.

## 🧪 Testing & Validation

**Test database connectivity:**
```python
from storage.db import BookDatabase

with BookDatabase() as db:
    stats = db.get_statistics()
    print(f"Total books: {stats['total_books']}")
    print(f"Books with descriptions: {stats['books_with_descriptions']}")
    print(f"Database size: {stats['database_size_mb']:.2f} MB")
```

**Validate API endpoints:**
```bash
# Health check
curl http://localhost:8000/books?limit=1

# ISBN lookup
curl http://localhost:8000/books/9780141439518
```

## 📊 Sample Output

```
======================================================================
                   BOOK FINDER DATA PIPELINE                         
======================================================================

STEP 1: INGESTION
----------------------------------------------------------------------
✓ Loaded 500 rows from data/books_data.csv
✓ Loaded 300 rows from data/enriched_books.csv
✓ Total books ingested: 800

======================================================================
STEP 2: TRANSFORMATION
----------------------------------------------------------------------
✓ Cleaned 800 books
✓ Removed 50 duplicates
✓ Filtered 100 books without descriptions
✓ Valid books after cleaning: 650

======================================================================
STEP 3: STORAGE
----------------------------------------------------------------------
✓ Database schema created
✓ Inserted: 650 books
⚠ Skipped: 0 duplicates

📊 Database Statistics:
  Total books: 650
  Books with descriptions: 650
  Database size: 2.34 MB

======================================================================
                 PIPELINE COMPLETED SUCCESSFULLY ✓                  
======================================================================
```

## 🎓 Learning Objectives Achieved

- ✅ **Multi-source Data Ingestion** - CSV files + REST API integration
- ✅ **Data Quality Engineering** - Cleaning, validation, normalization
- ✅ **Relational Database Design** - SQLite schema with proper indexing
- ✅ **API Development** - RESTful endpoints with FastAPI
- ✅ **Error Handling** - Graceful handling of missing data, duplicates, API failures
- ✅ **Pipeline Orchestration** - End-to-end ETL workflow automation

## 🔮 Next Steps

### For Data Scientists
1. Load data from FastAPI endpoint: `GET /books?limit=1000`
2. Generate embeddings using sentence-transformers
3. Implement semantic search for queries like "lonely robot in space"
4. Build recommendation system using cosine similarity

### Potential Enhancements
- [ ] Add pagination for datasets > 1000 books
- [ ] Implement search filters (genre, author, date range)
- [ ] Integrate additional data sources (Kaggle, GoodReads API)
- [ ] Add book cover image URLs
- [ ] Implement incremental updates (delta sync)
- [ ] Add data validation with Pydantic models
- [ ] Deploy API with Docker containerization

## 📝 LLM Usage Documentation

All LLM assistance used during development is transparently documented in [logs/llm_usage.md](logs/llm_usage.md) as per project requirements.

## 📄 License

This project is created for educational purposes as part of a data engineering learning module.

## 🤝 Contributing

This is a learning project. Feel free to fork and experiment with your own data sources and transformations!

---

**Built with:** Python • SQLite • FastAPI • Pandas • OpenLibrary API
