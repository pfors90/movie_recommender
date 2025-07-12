# movie_recommender

Using dataset from: https://www.kaggle.com/datasets/octopusteam/tmdb-movies-dataset<br>
Published 2025-06-30<br><br>

Provided files are current as of the publish date listed above<br>
Movie corpus filtering criteria can be adjusted in <em>scripts/clean_movies.py</em><br><br>

<ol>
    <li>Navigate to the project base directory</li>
    <li>Ensure subfolders <em>data/</em> and <em>scripts/</em> exist</li>
    <li>Place <em>data.json</em> (link above) in the <em>data/</em> subdirectory
        <ul><li><strong>Note:</strong> <em>data/ids_keywords.json</em> will always be checked before querying the API. To avoid excess API calls, please use the provided <em>ids_keywords.json</em> file.</li></ul>
    </li>
    <li>Run <em>scripts/main.py</em></li>
</ol>

When running <em>scripts/main.py</em>, the following will occur:
<ol>
    <li>Extraneous records will be stripped from <em>data/data.json</em></li>
    <li>The filtered list will be converted to a list of dictionaries with minimal info</li>
    <li>These dictionaries will be used to populate three database tables:
        <ul>
            <li><em>movies</em> - basic movie metadata and vector information</li>
            <li><em>genres</em> - index of id:genre_name</li>
            <li><em>movies_genres</em> - many-to-many relationship linking movie_id to genre_id</li>
        </ul>
    </li>
    <li>Keyword data is grabbed and written to the cache file <em>data/ids_keywords.json</em>
        <ul><li><strong>Note:</strong> <em>data/ids_keywords.json</em> will be checked for existing keywords before calling the API. To avoid excess API calls, please use the provided <em>ids_keywords.json</em> file.</li></ul>
    </li>
    <li>Keyword data is used to populate two database tables:
        <ul>
            <li><em>keywords</em> - index of id:keyword_name</li>
            <li><em>movies_keywords</em> - many-to-many relationship linking movie_id to keyword_id</li>
        </ul>
    </li>
    <li>Movie database is checked for any rows missing a vector. Vectors are calculated and committed to the database as needed.</li>
</ol>

Subsequent runs of the enclosed scripts with newer versions of <em>data.json</em> as retrieved from the above link should properly build on existing data without causing undue CPU or network strain, although some lag can be expected during the initial filtering operation.