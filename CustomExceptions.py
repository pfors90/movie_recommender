# class MissingDatabase(FileNotFoundError):
#     def __init__(self, message: str):
#         self.message = message

class MovieNotFound(Exception):
    def __init__(self, movie_id: int):
        self.message = f"Movie ID {movie_id} missing from production database"

class InvalidListLength(Exception):
    def __init__(self, message: str):
        self.message = message