from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import os
import json

from logger import logger

DATABASE_FILE = 'movie_recommender.db'
VECTORIZER_FILE = 'data/vectorizer.pkl'
FEATURE_NAMES_CACHE = 'data/feature_names.json'

# checks the database for any movies missing a vector, computes it, writes it to DB based on keywords
# TODO: modify function to run with optional parameter 'ids' which forces an update on the ids list
# TODO: if no list passed, then only update records missing a vector

def custom_tokenizer(x):
    return x.split('|')


def get_movies_missing_vectors(cursor) -> list:
    result = cursor.execute("SELECT id, vector FROM movies")
    ids_missing_vectors = [m["id"] for m in result if m["vector"] is None]
    logger(f"import_vector_data() found {len(ids_missing_vectors)} movies in the database with missing vectors", type='a')

    return ids_missing_vectors


def get_keywords_for_movies(cursor, missing_vectors) -> dict[int, list]:
    # sql query returns distinct (movie_id, keyword) pairs - keywords need to be built into a list
    # against 1 movie_id entry for vector processing
    ids_keywords = {}
    placeholder = ','.join(['?'] * len(missing_vectors))
    query = f"""SELECT mk.movie_id, k.keyword FROM movies_keywords AS mk
                    INNER JOIN keywords AS k ON mk.keyword_id = k.id
                    WHERE mk.movie_id IN ({placeholder})
                """
    result = cursor.execute(query, missing_vectors)

    for row in result:
        if row["movie_id"] not in ids_keywords:  # can't append if a list doesn't exist
            ids_keywords[row["movie_id"]] = [row["keyword"]]
        else:
            ids_keywords[row["movie_id"]].append(row["keyword"])

    return ids_keywords


def build_keyword_corpus(ids_keywords) -> (list[int], list[str]):
    movie_ids = []  # for matching purposes after keyword vectors are processed
    keyword_corpus = []
    for id, keywords in ids_keywords.items():
        movie_ids.append(id)
        # corpus needs to be pipe-separated as keywords may contain commas or spaces
        keyword_corpus.append('|'.join(keywords))

    return movie_ids, keyword_corpus


def vectorize_corpus(keyword_corpus):
    if os.path.exists(VECTORIZER_FILE): # check for existing vectorizer on disk
        with open(VECTORIZER_FILE, 'rb') as f:
            vectorizer = pickle.load(f)
        if not isinstance(vectorizer, TfidfVectorizer): # verify it was read in as a vectorizer
            raise TypeError(f"Pickle file {VECTORIZER_FILE} is not a TfidfVectorizer")
        vector_matrix = vectorizer.transform(keyword_corpus)
        logger(f"keyword_corpus processed by existing vectorizer '{VECTORIZER_FILE}'")

    else: # no vectorizer exists, create one
        vectorizer = TfidfVectorizer(token_pattern = None, tokenizer = custom_tokenizer)
        vector_matrix = vectorizer.fit_transform(keyword_corpus)
        logger("No vectorizer present on disk, creating a new one")

        # write the vectorizer to disk for potential future use
        with open(VECTORIZER_FILE, 'wb') as f:
            pickle.dump(vectorizer, f)
            logger(f"New vectorizer has been written to disk: '{VECTORIZER_FILE}'", type='a')

    # store vector names to disk as they may be useful either
    # can't directly serialize np.ndarray, converting to list first
    feature_names = list(vectorizer.get_feature_names_out())
    with open(FEATURE_NAMES_CACHE, 'w') as f:
        json.dump(feature_names, f, indent=2)
        logger(f"List of {len(feature_names)} feature names has been written to disk")

    return vector_matrix


def store_vectors_to_db(cursor, movie_ids, vector_matrix):
    # convert the scipy csr to a dict for loading and unloading from DB
    #--TODO: instead of dumping as json, can we pickle the array as is and put that in the db?
    #--TODO: would probably make later math easier to do
    for i in range(vector_matrix.shape[0]):
        row = vector_matrix.getrow(i)
        coo = row.tocoo()
        row_dict = {int(k): float(v) for k,v in zip(coo.col, coo.data)}
        query = "UPDATE movies SET vector = ? WHERE id = ?"
        values = [json.dumps(row_dict), movie_ids[i]]
        cursor.execute(query, values)


def import_vector_data(cursor, ids=None):
    movies_missing_vectors = get_movies_missing_vectors(cursor)

    if not movies_missing_vectors:
        logger(f"Vectors for all rows in table (movies) have already been calculated, returning from import_vector_data()")
        return

    ids_keywords = get_keywords_for_movies(cursor, movies_missing_vectors)
    movie_ids, keyword_corpus = build_keyword_corpus(ids_keywords)
    vector_matrix = vectorize_corpus(keyword_corpus)
    store_vectors_to_db(cursor, movie_ids, vector_matrix)

    logger("import_vector_data() finished without error - returning")

# potentially unnecessary as TfidfVectorizer() returns normalized vectors already?
# keeping this as a need may arise with composite user vectors
def normalize_vector(vector: dict[int:float]) -> dict[int:float]:
    norm = (sum(v**2 for v in vector.values()))**0.5
    normalized_vector = {k:(v/norm) for k,v in vector.items()}
    return normalized_vector