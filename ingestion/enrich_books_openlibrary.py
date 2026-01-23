import requests
import pandas as pd
import time

print("RUNNING enrich_books_openlibrary.py")

BASE_SEARCH_URL = "https://openlibrary.org/search.json"
BASE_WORK_URL = "https://openlibrary.org"


# -------------------------------------------------
# Detect title column automatically (NO assumptions)
# -------------------------------------------------
def detect_title_column(df):
    for col in df.columns:
        if "title" in col.lower():
            return col
    raise ValueError(f"No title-like column found. Columns: {df.columns.tolist()}")


# -------------------------------------------------
# Fetch description + genre from OpenLibrary
# -------------------------------------------------
def fetch_book_data(title):
    try:
        params = {"title": title, "limit": 1}
        r = requests.get(BASE_SEARCH_URL, params=params, timeout=10)

        if r.status_code != 200:
            return None, None

        docs = r.json().get("docs", [])
        if not docs:
            return None, None

        work_key = docs[0].get("key")
        if not work_key:
            return None, None

        work_url = f"{BASE_WORK_URL}{work_key}.json"
        work_resp = requests.get(work_url, timeout=10)

        if work_resp.status_code != 200:
            return None, None

        work_data = work_resp.json()

        # -------- description --------
        desc = work_data.get("description")
        if isinstance(desc, dict):
            desc = desc.get("value")

        # -------- genre (subjects) --------
        subjects = work_data.get("subjects", [])
        genre = ", ".join(subjects[:5]) if subjects else None

        return desc, genre

    except Exception as e:
        print(f"ERROR fetching '{title}': {e}")
        return None, None


# -------------------------------------------------
# Enrich dataset
# -------------------------------------------------
def enrich_dataset(csv_path, output_path):
    # Read CSV safely
    df = pd.read_csv(csv_path, encoding="latin-1")

    # Detect title column
    title_col = detect_title_column(df)
    print(f"Using title column: {title_col}")

    descriptions = []
    genres = []

    for title in df[title_col]:
        print(f"Fetching: {title}")
        desc, genre = fetch_book_data(title)
        descriptions.append(desc)
        genres.append(genre)
        time.sleep(0.2)  # polite + unlimited

    # Add new columns
    df["description"] = descriptions
    df["genre"] = genres

    # Drop rows without description (useless for semantic search)
    df = df.dropna(subset=["description"])

    # Save enriched dataset
    df.to_csv(output_path, index=False)
    print(f"Enriched dataset saved to: {output_path}")


# -------------------------------------------------
# Entry point
# -------------------------------------------------
if __name__ == "__main__":
    enrich_dataset(
        "data/books data.csv",
        "data/enriched_books.csv"
    )

