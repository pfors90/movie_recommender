import database_helper as dbh
from Movie import Movie
from logger import logger

def get_composite_by_vectors(vectors: list[dict], normalize=True) -> dict[int, float]:
    """
    :param vectors: a list of sparse vectors represented as dictionaries
    :param normalize: boolean flag, whether to normalize the vector before returning (default True)
    :return: a sparse vector representing the average of the supplied vectors
    """
    if not vectors:
        return dict()

    composite = dict()
    for vector in vectors:
        for k, v in vector.items():
            composite[k] = composite.get(k, 0.0) + v # default 0.0 if the index isn't yet in the dict

    # result is the same after normalization whether we average or not
    # num_vectors = len(vectors)
    # for k in composite:
    #     composite[k] /= num_vectors

    if normalize: # default case
        return normalize_vector(composite)

    return composite # non-normalized


#--TODO: below function assumes all movies have a vector (before adding 'if' statement)
#--TODO: warn user that a movie is not being tracked? how should we handle this?

#--TODO NOTE: NEW PARSING LOGIC WILL EXCLUDE MOVIES WITH NO KEYWORDS FROM THE DATABASE
def get_composite_by_movies(movies: list[Movie], normalize=True) -> dict[int, float]:
    """
    takes in a list of Movie objects, strips out the vectors, and calls get_composite_by_vectors()
    :param movies: a list of Movie objects
    :param normalize: boolean flag, whether to normalize resulting composite vector (default True)
    :return: a sparse vector representing the average of the supplied vectors
    """
    vectors = [movie.vector for movie in movies if movie.vector is not None]

    return get_composite_by_vectors(vectors, normalize=normalize)


def compute_norm(vector: dict[int, float]):
    return sum(v**2 for v in vector.values())**0.5


def normalize_vector(vector: dict[int, float]) -> dict[int, float]:
    """
    normalization "removes" magnitude from vectors so that angles can be properly compared
    :param vector: non-normalized sparse vector represented as a dictionary
    :return: normalized sparse vector represented as a dictionary
    """
    if not vector:
        return dict()

    norm = compute_norm(vector)

    if norm == 0:
        return {k: 0.0 for k in vector}

    return {k: (v/norm) for k,v in vector.items()}


# function by default assumes vectors are normalized - set normalize flag if not
def cosine_similarity(vector1: dict[int, float], vector2: dict[int, float], normalized: bool = True) -> float:
    """
    takes in two vectors and calculates the cosine similarity, returning the value as a float\n
    if only one vector is normalized, set 'normalized' to False - the already normalized vector will have a calculated
    norm of 1 and not affect the logic
    :param vector1: a sparse vector represented as a dictionary
    :param vector2: a sparse vector represented as a dictionary
    :param normalized: boolean flag, whether the two vectors are already normalized (default True)
    :return: a float value representing the similarity score
    """
    # every dimension not shared by the vectors will resolve to 0.0
    shared_dimensions = set(vector1).intersection(set(vector2))
    similarity_score = sum((vector1[d]*vector2[d] for d in shared_dimensions))

    if normalized:
        return similarity_score

    return similarity_score / (compute_norm(vector1)*compute_norm(vector2))


def get_recommendations_by_ids(user_movie_ids: list[int], n=5):
    """
    this method takes in a list of movie IDs and an int n for number of results requested, takes a composite of the
    vectors for those movies, and then compares that composite vector to the vector representation of every potential
    match in the db\n
    "potential matches" are defined as those movies that share at least one keyword and one genre with a user-supplied
    movie, AND that have more than one keyword logged in the database.
    :param user_movie_ids: a list of IDs for the movies titles submitted by the user
    :param n: the number of results to return (default 5)
    :return: a list of tuples (Movie object, similarity score as float)
    """
    logger(f"Processing recommendation for IDs: {user_movie_ids}")
    user_movies = dbh.get_movies_by_ids(user_movie_ids)
    user_vectors = [m.vector for m in user_movies]
    genre_id_set = set() # defined as a set to avoid duplicates
    keyword_id_set = set()
    for m in user_movies:
        genre_id_set.update(m.genre_ids)
        keyword_id_set.update(m.keyword_ids)

    user_composite_vector = get_composite_by_vectors(user_vectors)

    potential_matches = dbh.get_potential_matches(list(genre_id_set), list(keyword_id_set))
    logger(f"Keyword+genre filter: {len(potential_matches)} potential matches found")
    [potential_matches.pop(m) for m in user_movie_ids] # make sure that we exclude movies the user entered
    recommendation_scores = {}

    for k,v in potential_matches.items():
        recommendation_scores[k] = cosine_similarity(user_composite_vector, v)

    # sort the movie IDs and scores by score and return them together as a list
    top_movies = sorted(recommendation_scores, key=lambda x: recommendation_scores[x], reverse=True)[:n]
    logger(f"Recommending movie IDs {top_movies}")
    rec_scores = sorted(recommendation_scores.values(), reverse=True)[:n]
    top_movies = dbh.get_movies_by_ids(top_movies)
    return zip(top_movies, rec_scores)
