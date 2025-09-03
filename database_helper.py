import json
import sqlite3
from flask import g

from CustomExceptions import MovieNotFound
from Movie import Movie

DB_FILE = 'movie_recommender.db'

def get_db():
    # stores a db connection in the Flask global context, autocloses between page loads
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_FILE)
        db.row_factory = sqlite3.Row # dict-like access

    return db


def close_db():
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# used to convert the jsonified dbh vector into a dictionary
def load_sparse_dict(json_dict):
    tmp = json.loads(json_dict)
    return {int(k): v for k, v in tmp.items()}


def get_potential_title_matches(movie_title: str) -> list[sqlite3.Row]:
    """
    takes in a single user-entered movie title and queries the database, with decreasing levels of precision, for a match\n
    first looks for an exact match, then uses user-supplied wildcards (if present), finally uses LIKE ?query?
    :param movie_title: string (with or without wildcards) to be queried
    :return: list of sqlite3.Rows
    """
    db = get_db()
    exact_query = f"SELECT id, title, release_date FROM movies WHERE LOWER(title) = LOWER(?) LIMIT 5"
    wildcard_query = f"SELECT id, title, release_date FROM movies WHERE title LIKE ? LIMIT 5"

    # always check for an exact match first just in case
    results = db.execute(exact_query, [movie_title]).fetchall()
    if results: return results

    # if the user entered their own wildcards, query using those
    if "%" in movie_title or "_" in movie_title:
        results = db.execute(wildcard_query, [movie_title]).fetchall()
        if results: return results

    # fallback to our "default" wildcard query
    results = db.execute(wildcard_query, [f"%{movie_title}%"]).fetchall()
    return results


# returns a Movie object from dbh for a corresponding movie id
def get_movie_by_id(movie_id: int) -> Movie:
    db = get_db()
    query = "SELECT * FROM movies WHERE id = ?"
    result = db.execute(query, (movie_id,)).fetchone()
    if result is None:
        raise MovieNotFound(movie_id)

    # storing both name and ID for ease of both user display and dbh querying
    genres, genre_ids = get_genres_by_id(movie_id)
    keywords, keyword_ids = get_keywords_by_id(movie_id)
    return Movie(**result, genres=genres, genre_ids=genre_ids, keywords=keywords, keyword_ids=keyword_ids)


# repeatedly calls get_movie_by_id() on a list of ids
def get_movies_by_ids(movie_ids: list[int]) -> list[Movie]:
    return [get_movie_by_id(id) for id in movie_ids]


# grabs a list of genre names for a given id from join table
def get_genres_by_id(movie_id: int) -> tuple[list, list]:
    db = get_db()
    query = "SELECT mg.genre_id, g.genre FROM movies_genres AS mg INNER JOIN genres AS g ON mg.genre_id = g.id WHERE mg.movie_id = (?)"
    result = db.execute(query, (movie_id,)).fetchall()

    if result is None:
        return []

    genres = [r["genre"] for r in result]
    genre_ids = [r["genre_id"] for r in result]
    return genres, genre_ids


# grabs a list of keywords for a given id from join table
def get_keywords_by_id(movie_id: int) -> tuple[list, list]:
    db = get_db()
    query = "SELECT mk.keyword_id, k.keyword FROM movies_keywords AS mk INNER JOIN keywords AS k ON mk.keyword_id = k.id WHERE mk.movie_id = (?)"
    result = db.execute(query, (movie_id,)).fetchall()

    if result is None:
        return []

    keywords = [r["keyword"] for r in result]
    keyword_ids = [r["keyword_id"] for r in result]
    return keywords, keyword_ids


def get_potential_matches(genre_ids: list[int], keyword_ids: list[int]) -> dict[int, dict[int, float]]:
    """
    takes in a list of genre and keyword ids and queries the database for a set of unique movie_ids that share at least one
    keyword and one genre from the parameters, then returns a dictionary of movie_id (key) and sparse dict vectorization (value)\n
    even though our cosine similarity only runs on keyword vectorization, we include genre constraints in an attempt to subtly
    reinforce thematic appeal
    :param genre_ids: list of ids from genres db table
    :param keyword_ids: list of ids from keywords db table
    :return: a list of dictionaries in the format movie_id: dict(vectorization)
    """
    db = get_db()

    # find movies with at least one matching genre
    placeholder = ','.join(['?'] * len(genre_ids))
    query = f"SELECT DISTINCT movie_id FROM movies_genres WHERE genre_id IN ({placeholder})"
    result = db.execute(query, genre_ids).fetchall()
    genre_set = {r['movie_id'] for r in result}

    # find movies with at least one matching keyword AND that have more than one total keywords
    # movies with only one keyword logged tend to rank disproportionately high in otherwise diverse calculations
    placeholder = ','.join(['?'] * len(keyword_ids))
    query = f"""
        SELECT DISTINCT mk.movie_id FROM movies_keywords AS mk
        WHERE mk.keyword_id IN ({placeholder}) 
        AND mk.movie_id IN (
            SELECT movie_id FROM movies_keywords 
            GROUP BY movie_id HAVING COUNT(*) > 1
        )
    """
    result = db.execute(query, keyword_ids).fetchall()
    keyword_set = {r['movie_id'] for r in result}

    # take the intersection of the set so that we only test movies that match both lists
    results_set = list(genre_set.intersection(keyword_set))

    # get and return the vectors
    placeholder = ','.join(['?'] * len(results_set))
    query = f"SELECT id, vector FROM movies WHERE id IN ({placeholder})"
    result = db.execute(query, results_set).fetchall()
    ids_vectors = {r['id']:load_sparse_dict(r['vector']) for r in result}

    return ids_vectors
