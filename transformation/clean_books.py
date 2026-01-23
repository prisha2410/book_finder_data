import pandas as pd
import re
import html

def clean_description(text):
    if pd.isna(text):
        return None

    text = html.unescape(str(text))
    text = re.sub(r"<.*?>", "", text)
    text = text.strip()

    if text.lower() in ["description not available", "n/a", ""]:
        return None

    return text

def transform_books(df):
    df["description"] = df["description"].apply(clean_description)

    # Drop useless rows for semantic search
    df = df.dropna(subset=["description", "title"])

    # Remove duplicates
    df = df.drop_duplicates(subset=["title", "author"])

    return df
