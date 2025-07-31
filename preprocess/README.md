# movie_recommender

Using dataset from: https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies<br>
Published 2025-07-16<br><br>

Provided files are current as of the publish date listed above<br>
Movie corpus filtering criteria can be adjusted in <em>preprocess\clean_movies.py</em><br>

<ol>
    <li>Navigate to the project base directory</li>
    <li>Ensure subfolder <em>data\</em> exists</li>
    <li>Place <em>data.csv</em> (link above) in the <em>data\</em> subdirectory</li>
    <li>Run <em>preprocess\main.py</em></li>
</ol>

This will remove all entries according to the filters outlined in <em>preprocess/main.py</em>, then compare the remaining
IDs against those already existing in the database. New entries will be added, and the new entries will be looped through
in order to update the genres, movies_genres, keywords, and movie_keywords database tables accordingly.

After updating the records, any movies missing a stored vector will have one calculated and stored in the database.

Subsequent runs of the enclosed scripts with newer versions of <em>data.csv</em> as retrieved from the above link should 
properly build on existing data without causing undue CPU strain, although some lag can be expected during the initial 
filtering operation.