# Getting Started with Better Playlists
This guide explains how to install and run the Better Playlists app.

### Prerequisites
- Python 3.6 or higher
- pip

### Installation
Clone the repository.
```
git clone https://github.com/seanwendt/spotify-playlist-camelot.git
```
Navigate to the project directory.
```
cd spotify-playlist-camelot
```
Create a virtual environment for the project (we'll call it "env")
```
python -m venv env
```
Activate the virtual environment.
  - On Windows:
```
.\env\Scripts\Activate.ps1
```
  - On Unix or Linux:
```
source env/bin/activate
```
Install the project dependencies.
```
pip install -r requirements.txt
```

#### Set Environment Variables
To access the Spotify API, you need to set the Spotify client ID, client secret, and redirect URL as environment variables. The main script will prompt input if they're not found locally.


#### Run the Project
Once you have set the environment variables, you can run the test.py script to test the project.
```
python test.py
```

# How it works
TODO
