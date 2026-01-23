import pandas as pd
from transformation.clean_books import transform_books
from storage.db import create_tables, insert_books

def run():
    raw_df = pd.read_csv("data/enriched_books.csv")

    clean_df = transform_books(raw_df)

    create_tables()
    insert_books(clean_df)

    print(f"Inserted {len(clean_df)} enriched & cleaned books")

if __name__ == "__main__":
    run()
