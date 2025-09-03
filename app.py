from flask import Flask, render_template, abort, request

import database_helper as dbh
import vector_helper as vh
from logger import logger

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/visualizations/")
def visualizations():
    #--TODO build out visualizations page
    return render_template("visualizations.html")


@app.route("/your_movies/", methods=["GET"])
def your_movies():
    # routing for the user movie entry page
    return render_template("your_movies.html")


@app.route("/parse_user_movies/", methods=["POST"])
def parse_user_movies():
    #--TODO: modify database to store a "normalized" movie title (remove spaces, punctuation, etc)
    #--TODO: then normalize user queries and search the database for a partial/full match

    alerts = []
    # determines whether we can proceed with the recommendations or if we need clarification from the user
    user_movie_titles = request.form.getlist("movie_titles")
    user_movie_titles = [title.strip() for title in user_movie_titles if title.strip()]

    # TODO: bring in Bootstrap CSS and display pretty alerts at the top of the page
    # TODO: or pass this to a custom error page that redirects to your_movies.html because the below block keeps
    # TODO:     /parse_user_movies in the URL bar, which would throw an error if the user hits refresh
    if not user_movie_titles:
        alerts.append("Enter at least one movie title.")
        return render_template("your_movies.html", alerts = alerts)

    exact_matches = []
    partial_matches = []
    missing_matches = []

    for title in user_movie_titles:
        # each result row is a Row_factory, contains "id", "title", "release_date"
        # runs exact and approximate SELECT queries to try and find matches with slightly decreasing precision
        results = dbh.get_potential_title_matches(title)

        if len(results) == 1: # only one match in the database, grab it and go
            exact_matches.append(results[0])

        elif len(results) > 1: # multiple matches found
            # store the user-entered title along with a list of the results to pass to front end for confirmation
            partial_matches.append([title, results])

        else: # no matches found
            missing_matches.append(title)

    # TODO: bring in Bootstrap CSS and display pretty alerts at the top of the page
    # TODO: or pass this to a custom error page that redirects to your_movies.html because the below block keeps
    # TODO:     /parse_user_movies in the URL bar, which would throw an error if the user hits refresh
    if len(missing_matches) == len(user_movie_titles):
        alerts.append("None of the following movie titles were found in the database")
        alerts.append(missing_matches)
        return render_template("your_movies.html", alerts = alerts)

    # pass potential matches to a confirmation page for the user
    if partial_matches or missing_matches:
        return render_template("confirm.html", exact_matches = exact_matches, partial_matches = partial_matches, missing_matches = missing_matches)

    elif exact_matches: # fallback condition: everything matched exactly
        user_movie_ids = [int(movie["id"]) for movie in exact_matches]
        return render_template("recommendations.html", user_movies = dbh.get_movies_by_ids(user_movie_ids), recs = vh.get_recommendations_by_ids(user_movie_ids))

    else: abort(500)


@app.route("/parse_user_movies/", methods=["GET"])
def parse_user_movies_get(): # invalid request
    abort(405)


@app.route("/process_confirmation/", methods=["POST"])
def process_confirmation():
    user_movie_ids_raw = request.form.getlist("confirmed_ids")
    user_movie_ids = [int(id) for id in user_movie_ids_raw]

    for key in request.form:
        if key.startswith("partial_"):
            user_movie_ids.append(int(request.form[key]))
    return render_template("recommendations.html", user_movies = dbh.get_movies_by_ids(user_movie_ids), recs = vh.get_recommendations_by_ids(user_movie_ids))


@app.route("/process_confirmation/", methods=["GET"])
def process_confirmations_get(): # invalid request
    abort(405)


@app.teardown_appcontext
def teardown_db(exception): # closes db connection between page loads
    dbh.close_db()