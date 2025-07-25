<h1>movie recommender</h1>
<h3>powered by python, scikit-learn, and Flask</h3>

To run on Windows:
<ol>
<li>Ensure that you are running <a href="https://www.python.org/downloads/windows/">Python 3.13+</a>
    <ul><li>From a command prompt, you can confirm your current version with <em>python --version</em></li></ul>
</li>
<li>Download the project files and make note of the root directory (containing <em>app.py</em>)</li>
<li>Open a command prompt and navigate to the project root directory
    <ul><li>Ex: <em>cd C:\path\to\project</em></li></ul>
</li>
<li>Run the following commands to create a virtual environment and install the dependencies:
    <ul>
        <li><em>python -m venv .venv</em></li>
        <li><em>.venv\Scripts\activate</em></li>
        <li><em>pip install -r requirements.txt</em></li>
    </ul>
</li>
<li>Navigate to <a href="https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies">this Kaggle link</a>
and download the latest revision of the data set. Save it to <em>project_root/data</em></li>
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
address into your web browser.</li>
    </ul>
</li>

</ol>