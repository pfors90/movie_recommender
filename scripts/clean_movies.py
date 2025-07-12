from logger import logger

import json

# takes in a large movie corpus and filters out likely unnecessary records
def remove_unwanted_from_json_file(input_file) -> list[dict]:
    with open(input_file, mode='r', encoding='utf-8') as f:
        full_movies = [json.loads(line) for line in f]
        logger(f"clean_movie.py loaded in a movie corpus '{input_file}' : {len(full_movies)} records to process")

    wanted_movies = []

    for m in full_movies:
        not_adult = not m.get('adult', False)  # remove pornography
        is_released = m.get('status', 'none') == "Released"  # no announced, upcoming, etc
        has_plot = len(m.get('overview', 'none').split()) > 10  # ensure that there is reasonable plot length
        not_gibberish = any(
            char.isalpha() for char in m.get('overview', ''))  # remove empty and "pure junk" descriptions
        is_english = m.get('original_language', 'none') == "en"  # english movies only
        is_feature = 60 < m.get('runtime', 0) < 240  # removes non-feature length films and overly long outliers
        year_str = m.get('release_date', '').strip()[:4]
        if year_str.isdigit():
            is_modern = int(year_str) >= 1920
        else:
            is_modern = False
        has_votes = m.get('vote_count', 0) >= 40  # has some sort of engagement
        is_not_dtv = not m.get('video', True)  # not direct-to-video

        # confirm that all filters are true before we append to our wanted_movies list
        if all((not_adult, is_released, has_plot, not_gibberish, is_english, is_feature, is_modern, has_votes,
                is_not_dtv)):
            wanted_movies.append(m)

    logger(f"Extracted {len(wanted_movies)} wanted movies from '{input_file}'")
    return wanted_movies

# takes in a filtered list of movie data and strips out the fields that we need
# populates the movies, genres, and movies_genres tables
def process_wanted_movie_list(cursor, input_data) -> list[dict]:
    cleaned_data = []
    movie_genre_pairs = []

    # build map of known genres from database
    result = cursor.execute("SELECT id, genre FROM genres").fetchall()
    genre_map = {row["genre"]: row["id"] for row in result}

    # build list of movie IDs already in database
    result = cursor.execute("SELECT id FROM movies").fetchall()
    # --TODO: can we not use existing_ids and just let INSERT OR IGNORE handle it?
    existing_ids = [movie["id"] for movie in result] # track as a return value, probably unnecessary

    for r in input_data:
        movie_id = r.get('id')

        if movie_id in existing_ids:
            continue

        # put the record in order for database insertion
        cleaned_record = [
            movie_id,
            r.get('title'),
            r.get('overview'),
            r.get('release_date')
        ]

        existing_ids.append(movie_id) # track as a return value, probably unnecessary
        cleaned_data.append(cleaned_record)

        genres = [g.get('name', 'none') for g in r.get('genres', [])]

        new_genres = set([genre for genre in genres if genre not in genre_map])

        # update genres database if new genres are found in results
        # gets the autoincrement genre ID and adds it to the local map
        if new_genres:
            values = [[genre] for genre in new_genres]
            cursor.executemany("INSERT OR IGNORE INTO genres (genre) VALUES (?)", values)
            logger(f"{len(new_genres)} new genres found in movie ID {movie_id} - database (genres) updated", type='a')

            placeholder = ','.join(['?'] * len(new_genres))
            query = f"SELECT id, genre FROM genres WHERE genre IN ({placeholder})"
            result = cursor.execute(query, list(new_genres)).fetchall()

            for row in result:
                genre_map[row["genre"]] = row["id"]

        # build the data set for populating movie_genre_pairs
        for genre in genres:
            genre_id = genre_map.get(genre)
            if genre_id is not None:
                movie_genre_pairs.append([movie_id, genre_id])

    # populate the tables - or, if tracking a new column, update the movies table
    query = ("""
        INSERT INTO movies (id, title, overview, release_date)
        VALUES (?,?,?,?)
        ON CONFLICT (id) DO UPDATE SET
        title = excluded.title,
        overview = excluded.overview,
        release_date = excluded.release_date;
    """)
    cursor.executemany(query, cleaned_data)

    query = "INSERT OR IGNORE INTO movies_genres (movie_id, genre_id) VALUES (?,?);"
    cursor.executemany(query, movie_genre_pairs)
    logger(f"{len(movie_genre_pairs)} records inserted into table (movies_genres)")

    return existing_ids # ??