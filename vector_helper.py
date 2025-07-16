from Movie import Movie

def get_composite_by_vectors(vectors: list[dict], normalize=True) -> dict[int, float]:
    if not vectors:
        return dict()

    composite = dict()
    for vector in vectors:
        for k, v in vector.items():
            composite[k] = composite.get(k, 0.0) + v

    num_vectors = len(vectors)
    for k in composite:
        composite[k] /= num_vectors

    if normalize:
        return normalize_vector(composite)

    return composite


#--TODO: below function assumes all movies have a vector (before adding 'if' statement)
#--TODO: warn user that a movie is not being tracked? how should we handle this?
def get_composite_by_movies(movies: list[Movie], normalize=True) -> dict[int, float]:
    vectors = [movie.vector for movie in movies if movie.vector is not None]

    return get_composite_by_vectors(vectors, normalize=normalize)


def compute_norm(vector: dict[int, float]):
    return sum(v**2 for v in vector.values())**0.5


def normalize_vector(vector: dict[int, float]) -> dict[int, float]:
    if not vector:
        return dict()

    norm = compute_norm(vector)

    if norm == 0:
        return {k: 0.0 for k in vector}

    return {k: (v/norm) for k,v in vector.items()}


# function by default assumes vectors are normalized - set normalize flag if not
def cosine_similarity(vector1: dict[int, float], vector2: dict[int, float], normalized: bool = True) -> float:
    # every dimension not shared by the vectors will resolve to 0.0
    shared_dimensions = set(vector1).intersection(set(vector2))
    similarity_score = sum((vector1[d]*vector2[d] for d in shared_dimensions))

    if normalized:
        return similarity_score

    return similarity_score / (compute_norm(vector1)*compute_norm(vector2))