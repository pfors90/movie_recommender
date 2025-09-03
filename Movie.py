import json

class Movie():

    def __init__(self, id, title, overview, release_date, vector, genres, genre_ids, keywords, keyword_ids):
        self.id = id
        self.title = title
        self.overview = overview
        self.release_date = release_date
        self.vector = {int(k):v for k, v in json.loads(vector).items()}
        self.genres = genres
        self.genre_ids = set(genre_ids)
        self.keywords = keywords
        self.keyword_ids = set(keyword_ids)


    def __str__(self):
        return (f"[{self.id}] {self.title} ({self.release_date})\n"
                f"Plot: {self.overview[:200]}\n"
                f"Genres: {self.genres}\n"
                f"Keywords: {self.keywords}\n")
