import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from collections import Counter

from logger import logger


def render_genre_distribution_chart(df: pd.DataFrame) -> None:
    filepath = "static/images/genre_distribution.png"
    genre_counts = Counter()

    df["genres"].apply(lambda x: [genre_counts.update(x)])

    genre_df = pd.DataFrame(genre_counts.items(), columns=["genre", "count"])
    genre_df = genre_df.sort_values(by="count", ascending=False, )

    plt.figure(figsize=[10, 5])
    sns.barplot(data=genre_df, x="genre", y="count")
    plt.title("Genre Distribution")
    plt.xticks(rotation=75)
    plt.tight_layout()

    plt.savefig(filepath)
    logger(f"Genre distribution chart saved to '{filepath}'")


def render_keyword_decade_distributions(df: pd.DataFrame) -> None:
    filepath = "static/images/keyword_distribution.png"

    df["keyword_count"] = df["keywords"].fillna('').apply(lambda x: len(x))
    df["release_decade"] = (df["release_date"].dt.year // 10) * 10

    plt.figure(figsize=[10, 5])
    sns.barplot(data=df, x="release_decade", y="keyword_count")
    plt.title("Average Movie Keywords by Decade")
    plt.xlabel("Release Year")
    plt.xticks(rotation=45)
    plt.ylabel("Keyword Count")
    plt.tight_layout()

    plt.savefig(filepath)
    logger(f"Keyword distribution chart saved to '{filepath}'")


def render_movie_runtime_boxplot(df: pd.DataFrame) -> None:
    filepath = "static/images/runtime_distribution.png"

    plt.figure(figsize=[10, 5])
    sns.boxplot(data=df, x="runtime")
    plt.title("Runtime Distribution")
    plt.xlabel("Runtime")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(filepath)
    logger(f"Runtime boxplot saved to '{filepath}'")


if __name__ == "__main__":
    # TODO: take this out of main.py so that it can be run independently of the processing
    # TODO:     this will require filtering the data frame - maybe move everything but main() from main.py to a
    # TODO:       tools.py file so they can be imported and called here?
    INPUT_FILE = "data/data.csv"
    df = pd.read_csv(INPUT_FILE)