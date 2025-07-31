import sqlite3
import pandas as pd

from logger import logger
import database_setup as db
import vector_preprocess as vp
import create_visualizations as cv

RAW_FILE = 'data/data.csv'
DB_FILE = 'movie_recommender.db'

def load_and_filter_csv(input_file: str) -> pd.DataFrame:
    """
    reads in a CSV movie corpus from disk and filters unwanted entries. expected to contain the following columns:
    release_date, runtime, vote_count, overview, adult, status, runtime
    :param input_file: string file location of a CSV file
    :return: DataFrame of movie data
    """
    df = pd.read_csv(input_file)
    logger(f"Loaded CSV file '{input_file}' with {len(df)} records")

    # standardize data for filtering
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df['runtime'] = pd.to_numeric(df['runtime'], errors='coerce')
    df['vote_count'] = pd.to_numeric(df['vote_count'], errors='coerce')
    df['overview'] = df['overview'].fillna('')

    filters = (
            (df['adult'] == False) & # no adult films
            (df['status'] == 'Released') & # only movies available for viewing
            (df['overview'].str.split().str.len() >= 5) &
            (df['keywords'].str.split().str.len() >= 1) &
            # (df['overview'].str.contains(r'[A-Za-z]', regex=True)) & # overview isn't numeric (is hopefully coherent)
            # (df['original_language'] == 'en') &
            (df['runtime'].between(60, 180)) &
            (df['release_date'].dt.year >= 1920) &
            (df['vote_count'] >= 40)
    )

    filtered = df[filters].copy()

    # standardize data for processing
    filtered["genres"] = filtered["genres"].apply(
        lambda x: [g.strip().capitalize() for g in x.split(',')] if pd.notnull(x) else []
    )
    filtered["keywords"] = filtered["keywords"].apply(
        lambda x: [k.strip().lower() for k in x.split(',')] if pd.notnull(x) else []
    )

    logger(f"Filtered down to {len(filtered)} movies")
    return filtered


def process_movies_from_df(df: pd.DataFrame, cursor) -> None:
    """
    populates database table 'movies' based on a DataFrame of movie data
    :param df: pandas DataFrame of movie data, expected to contain columns 'id', 'title', 'release_data', and 'overview'
    :param cursor: sql connection
    :return: None
    """
    cleaned_movies = []

    existing_ids = {row["id"] for row in cursor.execute("SELECT id FROM movies").fetchall()}
    logger(f"{len(existing_ids)} movies exist in the database. Processing filtered CSV for new entries.")

    for _, row in df.iterrows():
        movie_id = int(row["id"])
        if movie_id in existing_ids:
            continue

        cleaned_movies.append([
            movie_id,
            row["title"],
            row["overview"],
            row["release_date"].date().isoformat() if pd.notnull(row["release_date"]) else None
        ])

    cursor.executemany("""
        INSERT INTO movies (id, title, overview, release_date)
        VALUES (?,?,?,?)
        ON CONFLICT (id) DO UPDATE SET
            title = excluded.title,
            overview = excluded.overview,
            release_date = excluded.release_date
    """, cleaned_movies)

    logger(f"{len(cleaned_movies)} movies added to database. Pending commit.")


def process_genres_from_df(df: pd.DataFrame, cursor) -> None:
    """
    populates database tables 'genres' and 'movies_genres' based on a DataFrame of movie data
    :param df: pandas DataFrame of movie data, expected to contain columns 'genres' and 'id'
    :param cursor: SQL connection
    :return: None
    """
    genre_map = {row["genre"]: row["id"] for row in cursor.execute("SELECT id, genre FROM genres").fetchall()}
    logger(f"Processing genres from filtered CSV. {len(genre_map)} genres exist in database.")
    movie_genre_pairs = []

    for _, row in df.iterrows():
        movie_id = int(row["id"])
        # raw_genres = row.get("genres", "")
        # # TODO: modify this to account for new data preprocessing
        # genres = [g.strip() for g in raw_genres.split(",") if g.strip()]

        genres = row.get("genres", [])

        new_genres = set(g for g in genres if g not in genre_map)
        if new_genres:
            logger(f"{len(new_genres)} new genres found: {new_genres}")
            cursor.executemany("INSERT OR IGNORE INTO genres (genre) VALUES (?)", [[g] for g in new_genres])
            rows = cursor.execute(
                f"SELECT id, genre FROM genres WHERE genre IN ({','.join(['?'] * len(new_genres))})",
                list(new_genres)
            ).fetchall()
            for row in rows:
                genre_map[row["genre"]] = row["id"]

        for g in genres:
            genre_id = genre_map.get(g)
            if genre_id:
                movie_genre_pairs.append([movie_id, genre_id])

    cursor.executemany("INSERT OR IGNORE INTO movies_genres (movie_id, genre_id) VALUES (?, ?)", movie_genre_pairs)
    logger(f"New (movie,genre) pairs added to database: {len(movie_genre_pairs)}. Pending commit.")


def clean_keywords(keyword_str: str) -> list:
    """
    helper function that removes keywords like 'based on a book', 'based on a novel', etc
    :param keyword_str: string of comma-separated keywords
    :return: list of keywords sans those beginning with 'based on'
    """
    if not isinstance(keyword_str, str):
        return []

    keywords = [kw for kw in keyword_str.split(',') if not kw.lower().startswith("based on")]

    return keywords


def process_keywords_from_df(df: pd.DataFrame, cursor) -> None:
    """
    populates database tables 'keywords' and 'movies_keywords' based on a DataFrame of movie data
    :param df: pandas DataFrame of movie data, expected to contain columns 'keywords' and 'id'
    :param cursor: SQL connection
    :return: None
    """
    keyword_map = {row["keyword"]: row["id"] for row in cursor.execute("SELECT id, keyword FROM keywords").fetchall()}
    logger(f"Processing keywords from filtered CSV. {len(keyword_map)} keywords exist in database.")
    movie_keyword_pairs = []

    for _, row in df.iterrows():
        movie_id = int(row["id"])
        # raw_keywords = row.get("keywords", "")
        # # TODO: modify this to account for new data preprocessing
        # keywords = [k.strip() for k in clean_keywords(raw_keywords)]

        keywords = row.get("keywords", [])

        new_keywords = set(k for k in keywords if k not in keyword_map)
        if new_keywords:
            logger(f"{len(new_keywords)} new keywords found: {new_keywords}")
            cursor.executemany("INSERT OR IGNORE INTO keywords (keyword) VALUES (?)", [[k] for k in new_keywords])
            rows = cursor.execute(
                f"SELECT id, keyword FROM keywords WHERE keyword IN ({','.join(['?'] * len(new_keywords))})",
                list(new_keywords)
            ).fetchall()
            for row in rows:
                keyword_map[row["keyword"]] = row["id"]

        for k in keywords:
            keyword_id = keyword_map.get(k)
            if keyword_id:
                movie_keyword_pairs.append([movie_id, keyword_id])

    cursor.executemany("INSERT OR IGNORE INTO movies_keywords (movie_id, keyword_id) VALUES (?, ?)", movie_keyword_pairs)
    logger(f"New (movie,keyword) pairs added to database: {len(movie_keyword_pairs)}. Pending commit.")


def main():
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        logger(f"Connected to db '{DB_FILE}' and enabled foreign key constraints")
    except Exception as e:
        logger(f"Error while connecting to {DB_FILE}:\n{e}\nAborting", type='e')
        exit(f"Error: {e}")

    # create the DB tables
    db.initialize_tables(cursor)
    conn.commit()
    logger(f"Loaded database file {DB_FILE}")

    try:
        filtered_df = load_and_filter_csv(RAW_FILE)
        process_movies_from_df(filtered_df, cursor)
        process_genres_from_df(filtered_df, cursor)
        process_keywords_from_df(filtered_df, cursor)
        conn.commit()
        logger(f"All data from {RAW_FILE} has been processed and committed to the database")
    except Exception as e:
        logger(f"Error in 'main.py' while processing movie data:\n{e}\nAborting - no changes committed to the database", type='e')
        exit(f"Error: {e}")

    try:
        vp.import_vector_data(cursor)
        conn.commit()
        logger("All vectors loaded into table (movies) by vp.import_vector_data()")
    except Exception as e:
        logger(f"Error in main.py while processing vp.import_vector_data():\n{e}\nAborting - no changed committed to the database", type='e')
        exit(f"Error: {e}")

    logger("Creating visualizations for updated data set")
    cv.render_genre_distribution_chart(filtered_df)
    cv.render_keyword_decade_distributions(filtered_df)
    cv.render_movie_runtime_boxplot(filtered_df)
    logger("Visualizations created and saved to static/images")


if __name__ == '__main__':
    main()