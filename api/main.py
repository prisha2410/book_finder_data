from fastapi import FastAPI
import sqlite3

app = FastAPI()
DB_PATH = "books.db"

def query_db(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/books")
def get_books(limit: int = 1000):
    return query_db(
        "SELECT * FROM books ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )

@app.get("/books/{book_id}")
def get_book(book_id: int):
    result = query_db("SELECT * FROM books WHERE id = ?", (book_id,))
    return result[0] if result else {}

@app.post("/sync")
def sync_data():
    from run_pipeline import run
    run()
    return {"status": "Data synchronized"}
