# 📚 Book Finder Data Pipeline

> A production-ready ETL pipeline that extracts, transforms, and loads book metadata from a 44-column enriched master CSV into a queryable SQLite database, designed to power ML-based semantic search applications.

---

## 🎯 Overview

This project ingests a library-catalogue dataset that has already been enriched by three upstream sources — the raw catalogue, OpenLibrary, and OpenAlex — and consolidates it into a clean, deduplicated SQLite database served over a FastAPI REST layer.

**Key Features:**
- Ingests any CSV dropped into `data/` — no hardcoded file names
- Smart column-priority mapping handles the full 44-column enriched schema
- Intelligent data cleaning: HTML stripping, ISBN validation, date normalisation
- Duplicate removal and description-quality filtering
- SQLite database with indexed queries
- FastAPI REST API for downstream consumption
- Full CLI via `python-fire` with `--help` on every script

---

## 🏗️ Architecture

```
┌──────────────────────┐
│  FINAL_MASTER CSV    │   ← 32,040 rows · 44 columns
│  (library catalogue  │
│   + OL + OA merged)  │
└──────────┬───────────┘
           │  glob("data/*.csv")
           ▼
┌──────────────────────┐
│   Ingestion Layer    │   ingest_books.py
│   _pick() priority   │   maps 44 cols → 6 fields
└──────────┬───────────┘
           │  32,040 raw dicts
           ▼
┌──────────────────────┐
│  Clean & Transform   │   clean_books.py
│  ISBN · HTML · dates │   drops invalid / dupes / no-desc
└──────────┬───────────┘
           │  ~20,819 clean dicts
           ▼
┌──────────────────────┐     ┌──────────────┐
│   SQLite  books.db   │────▶│  FastAPI     │
│   (indexed)          │     │  REST API    │
└──────────────────────┘     └──────────────┘
```

---

## 📂 Project Structure

```
book_finder_data/
├── data/
│   └── FINAL_MASTER_WITH_FINAL_TEXT_FIXED.csv   # 32,040-row enriched master
├── ingestion/
│   ├── ingest_books.py                          # CSV ingestion + stats
│   └── enrich_books_openlibrary.py             # Parallel OL/Google enrichment
├── transformation/
│   └── clean_books.py                          # Cleaning pipeline
├── storage/
│   └── db.py                                   # SQLite ORM layer
├── api/
│   └── main.py                                 # FastAPI application
├── diag.py                                     # CSV diagnostic tool
├── run_pipeline.py                             # Main ETL orchestrator
├── logs/
│   └── llm_usage.md                            # LLM assistance log
├── requirements.txt
├── DATA_DICTIONARY.md
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
git clone <your-repo-url>
cd book_finder_data
pip install -r requirements.txt
mkdir -p data
```

Place your CSV into `data/`. The pipeline picks up **every** `.csv` it finds there automatically.

### Run the full pipeline

```bash
python run_pipeline.py run_pipeline
```

### Start the API

```bash
uvicorn api.main:app --reload --port 8000
```

Docs live at http://localhost:8000/docs

---

## 📊 Pipeline Statistics (real numbers)

All numbers below come from the actual dataset (`FINAL_MASTER_WITH_FINAL_TEXT_FIXED.csv`) and the pipeline logic in `clean_books.py`.

### Source CSV — raw coverage

| Field | Non-null | Coverage | Source column |
|---|---|---|---|
| ISBN | 31,631 | 98.7 % | `ISBN` |
| Title | 32,040 | 100.0 % | `Title` |
| Authors | 32,008 | 99.9 % | `Author/Editor` |
| Description | 21,313 | 66.5 % | `final_description` |
| Genres / Subjects | 29,903 | 93.3 % | `final_subjects` |
| Publish Date | 31,873 | 99.5 % | `Year` |

### Pipeline stage-by-stage

| Stage | Action | Count | Notes |
|---|---|---|---|
| **Ingestion** | Rows loaded from CSV | 32,040 | single file, 44 columns |
| **Validation** | Dropped — no / invalid ISBN | 409 | ISBN is the primary key, required |
| **Deduplication** | Dropped — duplicate ISBN | 85 | 0.27 % of rows with ISBN |
| **Description filter** | Dropped — no description | 10,727 | `clean_books` requires description |
| **Storage** | **Estimated valid inserts** | **≈ 20,819** | after all filters |

### Enrichment flag coverage

These flags were set by the upstream enrichment pipeline before ingestion.

| Flag | Count | % of total |
|---|---|---|
| `has_final_description = 1` | 21,313 | 66.5 % |
| `has_final_subjects = 1` | 29,903 | 93.3 % |

### Key ratios

| Metric | Value |
|---|---|
| Net retention rate | 65.0 % (≈20,819 / 32,040) |
| Duplicate-ISBN rate | 0.27 % (85 / 31,631) |
| Missing-ISBN rate | 1.3 % (409 / 32,040) |
| Description-gap rate | 33.5 % (10,727 / 32,040) |

> **Tip:** Run `python ingestion/ingest_books.py print_stats` at any time to regenerate these numbers off whatever CSV is in `data/`.

---

## 📂 Source CSV Schema (44 columns)

The master CSV is produced by three upstream enrichment passes. Columns are grouped by origin below.

### Raw library catalogue

| Column | Description |
|---|---|
| `row_id` | Sequential row identifier |
| `Date` | Accession date (DD-MM-YYYY) |
| `Acc. No.` | Library accession number |
| `Title` | Book title |
| `Author/Editor` | Author or editor name(s) |
| `Ed./Vol.` | Edition / volume info |
| `Place & Publisher` | Publisher and city |
| `ISBN` | ISBN (10 or 13) |
| `Year` | Publication year |
| `Page(s)` | Page count string |
| `Source` | Source system identifier |
| `Class No./Book No.` | Library classification code |
| `status` | Catalogue status |
| `detail_url` | Link to catalogue record |
| `subjects` | Raw subjects from catalogue |
| `description` | Raw description from catalogue |

### OpenLibrary enrichment (`ol_*`)

| Column | Description |
|---|---|
| `ol_status` | Lookup result status |
| `ol_title` | Title as returned by OpenLibrary |
| `ol_authors` | Authors from OpenLibrary |
| `ol_publisher` | Publisher from OpenLibrary |
| `ol_publish_date` | Publish date from OpenLibrary |
| `ol_number_of_pages` | Page count from OpenLibrary |
| `ol_work_key` | OpenLibrary work key (e.g. `/works/OL…`) |
| `ol_description` | Description from OpenLibrary |
| `ol_subjects` | Subjects from OpenLibrary |

### OpenAlex enrichment (`oa_*`)

| Column | Description |
|---|---|
| `oa_row_id` | Row matched in OpenAlex |
| `oa_Title` | Title used for the lookup |
| `oa_openalex_id` | OpenAlex work ID |
| `oa_openalex_title` | Title returned by OpenAlex |
| `oa_doi` | DOI if available |
| `oa_type` | Work type (e.g. `book`) |
| `oa_year` | Publication year from OpenAlex |
| `oa_cited_by_count` | Citation count |
| `oa_similarity` | Title-match similarity score |
| `oa_concept_tags` | Concept / topic tags |
| `oa_abstract` | Abstract from OpenAlex |
| `oa_status` | Lookup result status |

### Final merged columns

These are the best available value for each field, chosen by the enrichment pipeline. **These are what the ingestion layer reads first.**

| Column | Description |
|---|---|
| `final_description` | Best description (from OL, OA, or catalogue) |
| `final_description_source` | Which source it came from (e.g. `ol_description`, `oa_abstract`) |
| `final_subjects` | Best subjects / genres |
| `final_subjects_source` | Which source they came from |
| `has_final_description` | `1` if `final_description` is populated, else `0` |
| `has_final_subjects` | `1` if `final_subjects` is populated, else `0` |
| `title_key` | Normalised title used for matching |

---

## 🗄️ Database Schema (`books.db`)

### Table: `books`

Created by `storage/db.py → create_schema()`.

```sql
CREATE TABLE books (
    isbn          TEXT      PRIMARY KEY,                        -- unique ISBN-10 or ISBN-13
    title         TEXT      NOT NULL,                           -- book title
    description   TEXT,                                         -- cleaned description
    authors       TEXT,                                         -- comma-separated names
    genres        TEXT,                                         -- comma-separated genre/subject tags
    publish_date  TEXT,                                         -- ISO 8601  YYYY-MM-DD
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP          -- insertion time
);

CREATE INDEX idx_created_at ON books(created_at DESC);         -- fast "recent books" queries
```

### Column detail

| Column | Type | Constraint | What gets stored |
|---|---|---|---|
| `isbn` | TEXT | PRIMARY KEY | Stripped of hyphens/spaces. Must be exactly 10 or 13 digits (ISBN-10 allows trailing `X`). |
| `title` | TEXT | NOT NULL | HTML-cleaned, whitespace-normalised, truncated at 500 chars. |
| `description` | TEXT | nullable | HTML-cleaned via BeautifulSoup, entities decoded, min 20 chars, max 5,000 chars. Placeholder phrases like "no description" are filtered out. |
| `authors` | TEXT | nullable | Single string, comma-separated if multiple. Sourced from `Author/Editor` → `ol_authors`. |
| `genres` | TEXT | nullable | Single string, comma-separated, max 5 tags. Sourced from `final_subjects` → `ol_subjects`. |
| `publish_date` | TEXT | nullable | Normalised to `YYYY-MM-DD`. Bare years become `YYYY-01-01`. |
| `created_at` | TIMESTAMP | auto | Set by SQLite at insert time. |

### Index

`idx_created_at` on `created_at DESC` — the `/books` endpoint orders by this column, so the index keeps that query fast regardless of table size.

### How 44 CSV columns become 6 DB columns

The ingestion layer uses a priority chain (`_pick()`) so each DB field always gets the best available value:

```
isbn            ← ISBN
title           ← Title
authors         ← Author/Editor  →  ol_authors  →  authors
description     ← final_description  →  ol_description  →  oa_abstract  →  description
genres          ← final_subjects  →  ol_subjects  →  subjects  →  genres
publish_date    ← Year  →  ol_publish_date  →  oa_year  →  publish_date
```

---

## 🧹 Transformations Applied

Every row passes through `clean_books.py` before hitting the database.

| Step | What happens | Drops the row? |
|---|---|---|
| **ISBN normalisation** | Hyphens and spaces stripped. Length must be 10 or 13 digits. | Yes — if invalid |
| **Title cleaning** | HTML tags removed (BeautifulSoup), entities decoded, whitespace collapsed, truncated to 500 chars. | Yes — if empty after cleaning |
| **Description cleaning** | Same HTML/entity cleanup. Rejects anything under 20 chars or matching known placeholder phrases (`"no description"`, `"n/a"`, `"coming soon"`, etc.). Truncates at 5,000 chars. | Yes — if empty / too short / placeholder |
| **Author normalisation** | Handles both strings and lists. Each name is HTML-cleaned, joined with `, `. | No |
| **Genre normalisation** | Same as authors. Capped at 5 tags. | No |
| **Date normalisation** | Accepts `YYYY-MM-DD`, bare `YYYY`, or any string containing a 4-digit year. All become `YYYY-MM-DD`. Bare years get `-01-01`. | No |
| **Deduplication** | `isbn` is the PRIMARY KEY — SQLite rejects duplicates at insert time; the batch inserter counts and skips them. | Yes — duplicate ISBN |

---

## 🔥 CLI Reference (`python-fire`)

Every script is wired with [python-fire](https://github.com/google/python-fire). Append `-- --help` to see usage for any command.

### `run_pipeline.py`

```bash
python run_pipeline.py run_pipeline          # run the full ETL
python run_pipeline.py -- --help
```

### `ingestion/ingest_books.py`

```bash
python ingestion/ingest_books.py ingest_all_books                          # ingest all CSVs in data/
python ingestion/ingest_books.py ingest_all_books --data_dir path/to/dir   # custom directory
python ingestion/ingest_books.py read_books_from_csv data/myfile.csv       # single file
python ingestion/ingest_books.py print_stats                               # coverage report
python ingestion/ingest_books.py -- --help
```

### `ingestion/enrich_books_openlibrary.py`

```bash
python ingestion/enrich_books_openlibrary.py enrich_parallel  INPUT.csv OUTPUT.csv --max_workers 5
python ingestion/enrich_books_openlibrary.py enrich_with_retry INPUT.csv OUTPUT.csv --max_retries 2
python ingestion/enrich_books_openlibrary.py -- --help
```

### `diag.py`

```bash
python diag.py diagnose_csv data/FINAL_MASTER_WITH_FINAL_TEXT_FIXED.csv
python diag.py -- --help
```

### `storage/db.py`

```bash
python storage/db.py --db_path data/books.db    # create schema + print stats
python storage/db.py -- --help
```

---

## 📡 API Reference

Base URL: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

### `GET /`

Returns API info and available endpoint list.

### `GET /books`

Fetch the most recent books.

| Parameter | Type | Default | Max | Description |
|---|---|---|---|---|
| `limit` | int | 1000 | 1000 | Number of records to return |

```bash
curl http://localhost:8000/books?limit=10
```

Response shape:
```json
{
  "count": 10,
  "books": [
    {
      "isbn": "9783540648260",
      "title": "Multimedia information analysis and retrieval …",
      "description": "This book constitutes …",
      "authors": "Ip, Horace H. S.",
      "genres": "Information retrieval, Multimedia systems …",
      "publish_date": "1998-01-01",
      "created_at": "2026-02-03 11:15:05"
    }
  ]
}
```

### `GET /books/{isbn}`

Fetch one book by ISBN. Returns `404` if not found.

```bash
curl http://localhost:8000/books/9783540648260
```

### `POST /sync`

Re-runs the full ingestion → clean → insert pipeline. Useful after dropping a new CSV into `data/`.

```bash
curl -X POST http://localhost:8000/sync
```

Response:
```json
{
  "status": "success",
  "message": "Data sync completed",
  "books_added": 20819,
  "books_updated": 85
}
```

### `GET /stats`

Returns current database statistics.

```bash
curl http://localhost:8000/stats
```

Response:
```json
{
  "database": "books.db",
  "statistics": {
    "total_books": 20819,
    "books_with_descriptions": 20819,
    "database_size_mb": 12.45
  }
}
```

### `GET /health`

Health-check endpoint.

```bash
curl http://localhost:8000/health
```

Response: `{"status": "healthy", "service": "book-finder-api"}`

---

## 🧪 Testing & Validation

### Quick smoke test — database

```python
from storage.db import BookDatabase

with BookDatabase() as db:
    stats = db.get_statistics()
    print(f"Total books:           {stats['total_books']}")
    print(f"With descriptions:     {stats['books_with_descriptions']}")
    print(f"Database size:         {stats['database_size_mb']:.2f} MB")
```

### Quick smoke test — API

```bash
curl http://localhost:8000/health                        # should return healthy
curl http://localhost:8000/books?limit=1                 # one book, confirms DB is populated
curl http://localhost:8000/books/9783540648260           # known ISBN from the dataset
```

### Regenerate stats at any time

```bash
python ingestion/ingest_books.py print_stats
```

---

## 🔮 Next Steps

### For Data Scientists
1. Pull data: `GET /books?limit=1000`
2. Generate embeddings with `sentence-transformers`
3. Build semantic search (e.g. "lonely robot in space")
4. Cosine-similarity recommendation system

### Potential Enhancements
- [ ] Pagination for the full 20 k+ dataset
- [ ] Search filters: genre, author, date range
- [ ] Incremental / delta sync (only new rows)
- [ ] Book cover image URLs
- [ ] Pydantic validation on ingest
- [ ] Docker deployment

---

## 📝 LLM Usage

All AI assistance is logged in [logs/llm_usage.md](logs/llm_usage.md).

## 📄 License

Educational / learning project.

---

**Built with:** Python · SQLite · FastAPI · Pandas · python-fire · OpenLibrary · OpenAlex