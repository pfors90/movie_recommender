from CustomExceptions import MovieNotFound
from Movie import Movie

import json

def load_sparse_dict(json_dict):
    tmp = json.loads(json_dict)
    return {int(k): v for k, v in tmp.items()}

# returns a Movie object from db for a corresponding movie id
def get_movie_by_id(cursor, movie_id: int) -> Movie:
    query = "SELECT * FROM movies WHERE id = ?"
    result = cursor.execute(query, (movie_id,)).fetchone()
    if result is None:
        raise MovieNotFound(movie_id)

    # storing both name and ID for ease of both user display and db querying
    genres, genre_ids = get_genres_by_id(cursor, movie_id)
    keywords, keyword_ids = get_keywords_by_id(cursor, movie_id)
    return Movie(**result, genres=genres, genre_ids=genre_ids, keywords=keywords, keyword_ids=keyword_ids)

# repeatedly calls get_movie_by_id() on a list of ids
def get_movies_by_ids(cursor, movie_ids: list[int]) -> list[Movie]:
    return [get_movie_by_id(cursor, id) for id in movie_ids]

# def get_movies_by_genre_ids(cursor, genre_ids: list[int]) -> list[Movie]:
#     placeholder = ','.join(['?'] * len(genre_ids))
#     query = f"SELECT DISTINCT movie_id FROM movies_genres WHERE genre_id IN ({placeholder})"
#     result = cursor.execute(query, genre_ids).fetchall()
#
#     movie_ids = [r["movie_id"] for r in result]
#     placeholder = '.'.join(['?'] * len(movie_ids))
#     query = f"SELECT * FROM movies WHERE movie_id IN ({placeholder})"
#     result = cursor.execute(query, movie_ids).fetchall()
#
#     movies = [Movie(**r) for r in result]
#     return movies

# def get_movies_by_keyword_ids(cursor, keyword_ids: list[int]) -> list[Movie]:
#     placeholder = ','.join(['?'] * len(keyword_ids))
#     query = f"SELECT DISTINCT movie_id FROM movies_keywords WHERE keyword_id IN ({placeholder})"
#     result = cursor.execute(query, keyword_ids).fetchall()
#
#     movie_ids = [r["movie_id"] for r in result]
#     placeholder = '.'.join(['?'] * len(movie_ids))
#     query = f"SELECT * FROM movies WHERE movie_id IN ({placeholder})"
#     result = cursor.execute(query, movie_ids).fetchall()
#
#     movies = [Movie(**r) for r in result]
#     return movies

# grabs a list of genre names for a given id from join table
def get_genres_by_id(cursor, movie_id: int) -> [list[str], list[int]]:
    query = "SELECT mg.genre_id, g.genre FROM movies_genres AS mg INNER JOIN genres AS g ON mg.genre_id = g.id WHERE mg.movie_id = (?)"
    result = cursor.execute(query, (movie_id,)).fetchall()

    if result is None:
        return []

    genres = [r["genre"] for r in result]
    genre_ids = [r["genre_id"] for r in result]
    return genres, genre_ids

# grabs a list of keywords for a given id from join table
def get_keywords_by_id(cursor, movie_id: int) -> [list[str], list[int]]:
    query = "SELECT mk.keyword_id, k.keyword FROM movies_keywords AS mk INNER JOIN keywords AS k ON mk.keyword_id = k.id WHERE mk.movie_id = (?)"
    result = cursor.execute(query, (movie_id,)).fetchall()

    if result is None:
        return []

    keywords = [r["keyword"] for r in result]
    keyword_ids = [r["keyword_id"] for r in result]
    return keywords, keyword_ids

# def get_movies_by_keyword_id(cursor, keyword_id: int) -> list[Movie]:
#     query = "SELECT DISTINCT movie_id FROM movies_keywords WHERE keyword_id = (?)"
#     result = cursor.execute(query, (keyword_id,)).fetchall()
#
#     if result is None:
#         return []
#
#     movie_ids = [row["movie_id"] for row in result]
#     movies = get_movies_by_ids(cursor, movie_ids)
#
#     return movies

def get_potential_matches(cursor, genre_ids: list[int], keyword_ids: list[int]) -> dict[int, dict[int, float]]:
    placeholder = ','.join(['?'] * len(genre_ids))
    query = f"SELECT DISTINCT movie_id FROM movies_genres WHERE genre_id IN ({placeholder})"
    result = cursor.execute(query, genre_ids).fetchall()
    genre_set = {r['movie_id'] for r in result}

    placeholder = ','.join(['?'] * len(keyword_ids))
    query = f"SELECT DISTINCT movie_id FROM movies_keywords WHERE keyword_id IN ({placeholder})"
    result = cursor.execute(query, keyword_ids).fetchall()
    keyword_set = {r['movie_id'] for r in result}

    results_set = list(genre_set.intersection(keyword_set))

    placeholder = ','.join(['?'] * len(results_set))
    query = f"SELECT id, vector FROM movies WHERE id IN ({placeholder})"
    result = cursor.execute(query, results_set).fetchall()
    ids_vectors = {r['id']:load_sparse_dict(r['vector']) for r in result}

    return ids_vectors
