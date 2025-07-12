from requests import Response
from logger import logger

from tqdm import tqdm
import requests
import time
import json

#--TODO: make sure BEARER_TOKEN is empty before pushing to git lol
BEARER_TOKEN = ""  # insert TMDB bearer token

def load_or_initialize_cache(cache_file: str) -> dict[int: list[str]]:
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            logger(f"Loaded cache: {cache_file}")
            return {int(k): v for k,v in raw_data.items()}
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        logger(e, type='e')
        return {}

def write_cache(cache_file: str, cache_data: dict[int:]) -> None:
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
        logger(f"Wrote cache: {cache_file}")

# this is only intended to be run once, to initially populate the keywords and movies_keywords
# tables from a json file in the format {id: [keywords]}
# after the initial table build, .get_keywords_by_ids() should be used instead
def build_db_tables_from_json_file(cursor, cache_file: str):
    ids_keywords = load_or_initialize_cache(cache_file)

    #--TODO: can this be normalized to [[kw] for kw_list etc etc]?
    #--TODO NOTE: sets help reinforce deduplication
    keywords_iterable_lists = {
        (kw,)
        for kw_list in ids_keywords.values()
        for kw in kw_list
    }

    query = "INSERT OR IGNORE INTO keywords (keyword) VALUES (?)"
    cursor.executemany(query, keywords_iterable_lists)
    logger(f"{len(keywords_iterable_lists)} keywords have been loaded into table (keywords)")

    # build keyword map
    result = cursor.execute("SELECT id, keyword FROM keywords").fetchall()
    keyword_map = {row["keyword"]: row["id"] for row in result}

    # initialize array for populating movies_keywords table
    movie_keyword_pairs = []

    for movie_id, keywords in ids_keywords.items():
        for keyword in keywords:
            keyword_id = keyword_map.get(keyword)
            if keyword_id is not None:
                movie_keyword_pairs.append([movie_id, keyword_id])

    query = "INSERT OR IGNORE INTO movies_keywords (movie_id, keyword_id) VALUES (?,?);"
    cursor.executemany(query, movie_keyword_pairs)
    logger(f"{len(movie_keyword_pairs)} records loaded into table (movies_keywords)")


def get_keywords_by_ids(cursor, requested_ids: list[int], cache_file: str): # -> dict[int: list[str]]:
    # default case
    if not requested_ids:
        logger("kh.get_keywords_by_ids() called with an empty list of IDs", type='a')
        return

    # if keyword data already exists in db table, load it in to avoid unnecessary API calls
    query = "SELECT DISTINCT movie_id FROM movies_keywords"
    result = cursor.execute(query).fetchall()
    existing_ids = {row["movie_id"] for row in result}

    # strip out any needed ids that are already cached to minimize API calls
    missing_ids = [movie_id for movie_id in requested_ids if movie_id not in existing_ids]
    if not missing_ids:
        return # all keywords known

    new_ids_keywords = retrieve_keywords_from_api(missing_ids, cache_file)

    if not new_ids_keywords:
        return

    # build keyword map
    result = cursor.execute("SELECT id, keyword FROM keywords").fetchall()
    keyword_map = {row["keyword"]: row["id"] for row in result}

    # initialize an array for populating the movies_keywords table
    movie_keyword_pairs = []

    for movie_id, keywords in new_ids_keywords.items():
        # prepare any newfound keywords for insert - as a set to reinforce singularity
        new_keywords = set([kw for kw in keywords if kw not in keyword_map])

        # update keywords database if new keywords are found in results
        if new_keywords:
            insert_data = [[kw] for kw in new_keywords]
            cursor.executemany("INSERT OR IGNORE INTO keywords (keyword) VALUES (?)", insert_data)
            logger(f"{len(new_keywords)} new keywords found in movie ID {movie_id} - database (keywords) updated", type='a')

            # after insert, get the ID and add it to the map
            placeholder = ','.join(['?'] * len(new_keywords))
            query = f"SELECT id, keyword FROM keywords WHERE keyword IN ({placeholder})"
            result = cursor.execute(query, list(new_keywords)).fetchall()

            for row in result:
                keyword_map[row["keyword"]] = row["id"]

        # translate the keyword to its id and prepare its movie pair for database insert
        for kw in keywords:
            keyword_id = keyword_map.get(kw)
            if keyword_id:
                movie_keyword_pairs.append([movie_id, keyword_id])

    query = "INSERT OR IGNORE INTO movies_keywords (movie_id, keyword_id) VALUES (?,?)"
    cursor.executemany(query, movie_keyword_pairs)
    logger(f"{len(movie_keyword_pairs)} records inserted into table (movies_keywords)")


def retrieve_keywords_from_api(ids: list[int], cache_file: str, max_fails=10, delay=0.1, cache_update_interval=25) -> dict[int:list]:
    """function returns a dict[int(movie_id):list(keywords)] of ALL movie_ids"""
    if not BEARER_TOKEN:
        raise ValueError("TMDB API bearer token missing from keyword_harvester.py")

    existing_ids_keywords = load_or_initialize_cache(cache_file)
    logger(f"kh.retrieve_keywords_from_api has imported a cache file with {len(existing_ids_keywords)} records")

    new_ids_keywords = dict()

    responses = []

    # track fail count so we don't hammer the API if it goes down or we get rate limited
    # if the fail count is hit, all existing data will be written to the cache file
    fail_count = 0

    # base case
    if not ids:
        return responses

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }

    # update our cache at regular intervals to minimize duplicate API calls in case of program error
    updates_since_cached = 0

    # progress bar via tqdm as this can be a lengthy operation
    for movie_id in tqdm(ids, desc="Fetching movie keywords"):
        if movie_id in existing_ids_keywords:
            continue

        try:
            url = f"https://api.themoviedb.org/3/movie/{movie_id}/keywords"
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            keywords = [kw["name"] for kw in data.get("keywords", [])]
            new_ids_keywords[movie_id] = keywords
            updates_since_cached += 1

            # write our changes to cache if we've exceeded the interval
            if updates_since_cached >= cache_update_interval:
                existing_ids_keywords.update(new_ids_keywords)
                write_cache(cache_file, existing_ids_keywords)
                logger("API call still in process, writing current data to cache")
                updates_since_cached = 0
            #responses.append(data)
            fail_count = 0 # reset on successful response
            time.sleep(delay)

        # if the API call fails, catch it here so we can keep going or store our data and quit
        except Exception as e:
            fail_count += 1
            logger(f"kh.retrieve_keywords_from_api failed for movie_id {movie_id}\n"
                   f"[Error]: {e}", type='a')

            # something seems to be wrong with our API calls - write the cache and abort
            if fail_count >= max_fails:
                logger(f"kh.retrieve_keywords_from_api encountered {max_fails} consecutive errors - aborting", type='e')
                existing_ids_keywords.update(new_ids_keywords)
                write_cache(cache_file, existing_ids_keywords)
                logger(f"API call aborted, cache written to memory", type='a')
                break

            # throttle ourselves a bit just in case
            time.sleep(delay * 5)

    existing_ids_keywords.update(new_ids_keywords)
    write_cache(cache_file, existing_ids_keywords)
    logger(f"kh.retrieve_keywords_from_api has written {len(existing_ids_keywords)} records to the cache file")

    return new_ids_keywords