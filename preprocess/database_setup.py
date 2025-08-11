def initialize_tables(cursor):
    movies_table_query = """
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY NOT NULL,
            title TEXT NOT NULL,
            overview TEXT,
            release_date DATE,
            vector TEXT
        );
    """

    genres_table_query = """
        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            genre TEXT UNIQUE
        );
    """

    movies_genres_table_query = """
        CREATE TABLE IF NOT EXISTS movies_genres (
            movie_id INTEGER,
            genre_id INTEGER,
            PRIMARY KEY (movie_id, genre_id),
            FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
            FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
        );
    """

    keywords_table_query = """
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            keyword TEXT UNIQUE
        );
    """

    movies_keywords_table_query = """
        CREATE TABLE IF NOT EXISTS movies_keywords (
            movie_id INTEGER,
            keyword_id INTEGER,
            PRIMARY KEY (movie_id, keyword_id),
            FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
            FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE
        );
    """

    cursor.execute(movies_table_query)
    cursor.execute(genres_table_query)
    cursor.execute(movies_genres_table_query)
    cursor.execute(keywords_table_query)
    cursor.execute(movies_keywords_table_query)