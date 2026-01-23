import pandas as pd

def load_books(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    return df

if __name__ == "__main__":
    df = load_books("data\\books data.csv")
    print(df.head())
    print(df.columns)
