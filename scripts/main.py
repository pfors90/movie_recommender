from logger import logger
import database_setup as db
import clean_movies as cm
import keyword_harvester as kh
import vector_preprocess as vp

import sqlite3
import os

RAW_FILE = '../data/data.json'
DB_FILE = '../movie_recommender.db'
IDS_KEYWORDS_FILE = '../data/ids_keywords.json'

def main():
    # attempt to open the DB file and establish a connection
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        logger(f"Connected to db {DB_FILE} and enabled foreign key constraints")
    except Exception as e:
        logger(f"Error while connecting to {DB_FILE}: {e} - aborting", type='e')
        exit(f"Error: {e}")

    # create the DB tables
    db.initialize_tables(cursor)
    conn.commit()

    # load in the movie corpus and strip out any movies that don't meet validity criteria
    filtered_movies = cm.remove_unwanted_from_json_file(RAW_FILE)
    logger(f"main.py processed {len(filtered_movies)} from '{RAW_FILE}'")

    # parse the movie list and begin building database tables
    try:
        cm.process_wanted_movie_list(cursor, filtered_movies)
        conn.commit()
        logger("Successfully committed cm.process_wanted_movie_list() to database from main.py")
    except Exception as e:
        logger(f"Error in main.py while processing cm.process_wanted_movie_list():\n{e}\n"
               f"Exiting program...", type='e')
        exit(f"[Error]: {e}")

    # if the movies_keywords DB is empty but there's a keyword cache on disk, process that first
    result = cursor.execute("SELECT COUNT(*) from movies_keywords").fetchone()
    if result[0] == 0 and os.path.exists(IDS_KEYWORDS_FILE):
        logger(f"Table (movies_keywords) is empty, but a keyword cache file exists - processing from disk first", type='a')
        try:
            kh.build_db_tables_from_json_file(cursor, IDS_KEYWORDS_FILE)
            conn.commit()
            logger(f"Successfully loaded {IDS_KEYWORDS_FILE} into table (movies_keywords)")
        except Exception as e:
            logger(f"Error in main.py while loading {IDS_KEYWORDS_FILE} to the database:\n{e}\n"
                   f"Exiting program...", type='e')
            exit(f"[Error]: {e}")

    # check for any existing movies that still need keywords, and grab them from the api
    result = cursor.execute("SELECT id FROM movies").fetchall()
    existing_ids = [m["id"] for m in result]
    try:
        kh.get_keywords_by_ids(cursor, existing_ids, IDS_KEYWORDS_FILE)
        conn.commit()
        logger("All keywords loaded into tables (keywords), (movies_keywords) by kh.get_keywords_by_ids()")
    except Exception as e:
        logger(f"Error in main.py while processing kh.get_keywords_by_ids():\n{e}\n"
               f"Exiting program...", type='e')
        exit(f"[Error]: {e}")

    try:
        vp.import_vector_data(cursor)
        conn.commit()
        logger("All changes loaded into table (movies) by vp.import_vector_data()")
    except Exception as e:
        logger(f"Error in main.py while processing vp.import_vector_data():\n{e}\n"
               f"Exiting program...", type='e')

if __name__ == '__main__':
    main()