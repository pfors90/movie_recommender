import database as db
import vector_helper as vh

from Movie import Movie

import sqlite3
import os

DB_FILE = 'movie_recommender.db'

def initiate_db(db_file:str = DB_FILE) -> [sqlite3.Connection, sqlite3.Cursor]:
    if not os.path.exists(db_file):
        raise FileNotFoundError(f"File {db_file} does not exist - check scripts/README.md")

    try:
        connection = sqlite3.connect(db_file)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        #--TODO: bring in logging functionality
        # logger(f"Connected to db {DB_FILE} and enabled foreign key constraints")

        return connection, cursor

    except Exception as e:
        print(f"Error while connecting to {db_file}: {e} - aborting")
        # logger(f"Error while connecting to {db_file}: {e} - aborting", type='e')


def get_recommendations_by_ids(cursor, user_movie_ids: list[int], n=10) -> list[tuple[Movie], float]:
    user_movies = db.get_movies_by_ids(cursor, user_movie_ids)
    user_vectors = [m.vector for m in user_movies]
    genre_id_set = set()
    keyword_id_set = set()
    for m in user_movies:
        genre_id_set.update(m.genre_ids)
        keyword_id_set.update(m.keyword_ids)

    user_composite_vector = vh.get_composite_by_vectors(user_vectors)

    potential_matches = db.get_potential_matches(cursor, list(genre_id_set), list(keyword_id_set))
    # make sure that we exclude movies the user entered
    [potential_matches.pop(m) for m in user_movie_ids]
    recommendation_scores = {}

    for k,v in potential_matches.items():
        recommendation_scores[k] = vh.cosine_similarity(user_composite_vector, v)

    # sort the movie IDs and scores by score and return them as a list
    top_movies = sorted(recommendation_scores, key=lambda x: recommendation_scores[x], reverse=True)[:n]
    rec_scores = sorted(recommendation_scores.values(), reverse=True)[:n]
    top_movies = db.get_movies_by_ids(cursor, top_movies)
    return zip(top_movies, rec_scores)


def main():
    conn, curs = initiate_db()


if __name__ == '__main__':
    main()