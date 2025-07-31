<h1>movie recommender</h1>
<h3>powered by python, scikit-learn, and Flask</h3>

<strong>To setup and run on Windows:</strong>
<ol>
<li>Ensure that you are running <a href="https://www.python.org/downloads/windows/">Python 3.13+</a>
    <ul><li>From a command prompt, you can confirm your current version with <em>python --version</em></li></ul>
</li>
<li>Download the project files and make note of the root directory (containing <em>app.py</em>)</li>
<li>Open a command prompt and navigate to the project root directory
    <ul><li>Ex: <em>cd C:\Code\movie_recommender</em></li></ul>
</li>
<li>Run the following commands to create a virtual environment and install the dependencies:
    <ul>
        <li><em>python -m venv .venv</em></li>
        <li><em>.venv\Scripts\activate</em></li>
        <li><em>pip install -r requirements.txt</em></li>
    </ul>
</li>
<li>Navigate to <a href="https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies">this Kaggle link</a>
and download the latest revision of the data set.
	<ul>
        <li>Extract the .csv file from the zip, rename it to <em>data.csv</em>, and save it to <em>{project_root}\data</em></li>
        <li>NOTE: You may need to make an account to download the data set.</li>
    </ul>
</li>
<li>Prepare the database tables
    <ul>
        <li>In your command prompt: <em>python preprocess\main.py</em></li>
        <li>NOTE: On first run, this may take a while</li>
    </ul>
</li>
<li>Run the webapp
    <ul>
        <li>In your command prompt: <em>flask run</em></li>
        <li>Your command prompt should display <em>Running on http://127.0.0.1:5000</em> or similar - copy and paste the IP
address and port number into your web browser.</li>
    </ul>
</li>
<li>To stop the webapp: in your command prompt, press <em>Ctrl+C</em></li>
<li>To exit the virtual environment: in your command prompt, run <em>deactivate</em></li>
</ol><br>

<strong>Subsequent launches will be much quicker:</strong>
<ol>
    <li>From a command prompt:
        <ul>
            <li><em>.venv\Scripts\activate</em></li>
            <li><em>flask run</em></li>
        </ul>
    </li>
    <li>Copy and paste the displayed IP:port into your web browser.</li>
    <li>To exit:
        <ul>
            <li>In your command prompt: press <em>Ctrl+C</em></li>
            <li>In your command prompt: <em>deactivate</em></li>
        </ul>
    </li>
</ol><br>

<strong>To update the database after initial setup:</strong>
<ol>
    <li>Remove the existing <em>data.csv</em> file from the <em>data</em> folder.</li>
    <li>Acquire an updated copy of <a href="https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies">the data set</a> and save it as <em>data/data.csv</em>.</li>
    <li>From a command prompt, navigate to the project root directory
        <ul><li>Ex: <em>cd C:\Code\movie_recommender</em></li></ul>   
    </li>
    <li>Activate your virtual environment: <em>.venv\Scripts\activate</em></li>
    <li>Run <em>python preprocess\main.py</em></li>
</ol>