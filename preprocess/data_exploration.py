import pandas as pd

from logger import logger

RAW_FILE = 'data/data.csv'

def load_and_preprocess_csv(input_file: str) -> pd.DataFrame:
    df = pd.read_csv(input_file)
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df['runtime'] = pd.to_numeric(df['runtime'], errors='coerce')
    df['vote_count'] = pd.to_numeric(df['vote_count'], errors='coerce')
    df['overview'] = df['overview'].fillna('')
    df["genres"] = df["genres"].apply(
        lambda x: [g.strip().capitalize() for g in x.split(',')] if pd.notnull(x) else []
    )
    df["keywords"] = df["keywords"].apply(
        lambda x: [k.strip().lower() for k in x.split(',')] if pd.notnull(x) else []
    )
    return df


def main():
    df = load_and_preprocess_csv(RAW_FILE)
    orig_size = df.shape[0]
    df.info()

    df = df[df["adult"] == False].copy()
    print(f"Original data set size: {orig_size}\n")
    print(f"Remaining after removing adult content: {df.shape[0]} ({(df.shape[0] / orig_size) * 100:.2f}%)\n")

    print("Top original languages:")
    print(f"{df["original_language"].value_counts().head(10)}\n")

    filtered = df[df["original_language"] == "en"].copy()
    print(f"Remaining after removing originally non-English: {filtered.shape[0]} ({(filtered.shape[0] / orig_size) * 100:.2f}%)\n")

    filtered["release_year"] = filtered["release_date"].dt.year
    filtered = filtered[filtered["release_year"].notnull()]
    movies_per_decade = (filtered["release_year"] // 10 * 10).value_counts().sort_index()
    print(f"Movies by decade:\n{movies_per_decade}\n")

    filtered["keyword_count"] = filtered["keywords"].apply(len)
    print(f"Average keywords per movie:\n{filtered["keyword_count"].describe()}\n")

    filtered = filtered[filtered["keyword_count"] >= 1].copy()
    print(f"Remaining after removing movies with no keywords: {filtered.shape[0]} ({(filtered.shape[0] / orig_size) * 100:.2f}%)\n")

    # TODO - movie all functions from main.py to a tools.py file so they can be called here for post-processing exploration


if __name__ == "__main__":
    main()