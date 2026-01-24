# Book Finder Data Pipeline

A robust data pipeline for extracting, cleaning, and storing book information to power an ML-based semantic search system.

## 🎯 Project Objective

Build a data pipeline that collects book data from multiple sources, cleans it, stores it in SQLite, and serves it via FastAPI for downstream semantic search applications.

## 📁 Project Structure

```
book_finder_data/
├── data/
│   ├── raw/                  # Place your CSV files here
│   └── processed/            # SQLite database will be created here
├── src/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── csv_reader.py
│   │   └── api_reader.py
│   ├── transformation/
│   │   ├── __init__.py
│   │   └── cleaner.py
│   ├── storage/
│   │   ├── __init__.py
│   │   └── database.py
│   └── api/
│       ├── __init__.py
│       └── main.py
├── logs/
│   └── llm_usage.md
├── pipeline.py
├── requirements.txt
├── DATA_DICTIONARY.md
└── README.md
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Pipeline

```bash
python pipeline.py
```

This will:
- Read CSV files from `data/raw/` (if any)
- Fetch books from OpenLibrary API
- Clean and normalize all data
- Store in SQLite at `data/processed/books.db`

### 3. Start the API Server

```bash
uvicorn src.api.main:app --reload --port 8000
```

Visit: `http://localhost:8000/docs` for interactive API documentation

## 📡 API Endpoints

### `GET /books`
Fetch the 1,000 most recent books

**Parameters:**
- `limit` (optional): Number of books (default: 1000, max: 1000)

**Example:**
```bash
curl http://localhost:8000/books?limit=100
```

### `GET /books/{isbn}`
Get a specific book by ISBN

**Example:**
```bash
curl http://localhost:8000/books/9780141439518
```

### `POST /sync`
Manually trigger data sync

**Example:**
```bash
curl -X POST http://localhost:8000/sync
```

## 📊 Database Schema

**Table: `books`**

| Column | Type | Description |
|--------|------|-------------|
| isbn | TEXT (PK) | Unique book identifier |
| title | TEXT (NOT NULL) | Book title |
| description | TEXT | Cleaned description (NULL if unavailable) |
| authors | TEXT | Comma-separated author names |
| genres | TEXT | Comma-separated genres |
| publish_date | TEXT | Date in YYYY-MM-DD format |
| created_at | TIMESTAMP | When record was added |

See [DATA_DICTIONARY.md](DATA_DICTIONARY.md) for full details.

## 🧹 Data Cleaning

The pipeline performs:
- ✅ HTML tag removal
- ✅ HTML entity decoding (`&amp;` → `&`)
- ✅ ISBN normalization and validation
- ✅ Duplicate removal (by ISBN)
- ✅ Filtering books without descriptions
- ✅ Date normalization to ISO format

## 📝 Adding CSV Data

Place CSV files in `data/raw/` with any of these column names:

**Supported column variations:**
- **ISBN:** isbn, isbn13, isbn10, ISBN
- **Title:** title, book_name, book_title, Title
- **Description:** description, blurb, summary, desc
- **Authors:** authors, author, author_name
- **Genres:** genres, genre, categories, subjects
- **Date:** publish_date, published, publication_date, year

The pipeline will automatically map these to the standard schema.

## 🎓 Learning Outcomes

1. ✅ **Data Ingestion** - Reading from multiple sources (CSV + API)
2. ✅ **Data Transformation** - Cleaning dirty data, handling edge cases
3. ✅ **Data Storage** - Moving from flat files to relational DB
4. ✅ **Data Serving** - Exposing data via REST API
5. ✅ **Error Handling** - Managing duplicates, missing data, API failures

## 🔍 Testing Your Pipeline

```python
# Test database connection
from src.storage.database import BookDatabase

with BookDatabase() as db:
    print(f"Total books: {db.count_books()}")
    print(f"Books with descriptions: {db.count_books_with_descriptions()}")
```

## 📈 Next Steps

1. **Switch to Data Scientist Role:**
   - Load data from FastAPI endpoint
   - Generate embeddings using Transformer models
   - Implement semantic search for "lonely robot in space"

2. **Enhancements:**
   - Add more data sources (Kaggle, GoodReads)
   - Implement pagination for large datasets
   - Add search filters (genre, author, date range)

## 🤖 LLM Usage

All LLM interactions are logged in `logs/llm_usage.md` as per project requirements.



