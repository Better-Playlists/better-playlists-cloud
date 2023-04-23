import os
from pprint import pprint

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from utils import pitch_to_camelot, extract_playlist_id, reorder_list

# Get environment variables
# TIP: In Windows environements, you can set these in Windows > Edit the system environment variables > Environment Variables > User variables for <user>
client_id = os.environ.get('SPOTIPY_CLIENT_ID')
client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.environ.get('SPOTIPY_REDIRECT_URI')

# Check if any of the environment variables are not set
if not client_id or not client_secret or not redirect_uri:
    client_id = input("Enter your SPOTIPY_CLIENT_ID: ")
    client_secret = input("Enter your SPOTIPY_CLIENT_SECRET: ")
    redirect_uri = input("Enter your SPOTIPY_REDIRECT_URI: ")

    # set environment variables based on input
    os.environ['SPOTIPY_CLIENT_ID'] = client_id
    os.environ['SPOTIPY_CLIENT_SECRET'] = client_secret
    os.environ['SPOTIPY_REDIRECT_URI'] = redirect_uri

# Check if any of the environment variables are missing
if not client_id or not client_secret or not redirect_uri:
    raise Exception("Missing environment variable(s)")
else: 
    print("Environment variables set successfully!")

## Ask the user for the playlist they want to use
PLAYLIST_URL = input("Enter your Spotify Playlist URL (e.g. https://open.spotify.com/playlist/...): ")

# Check that the url has been modified before proceeding
assert PLAYLIST_URL != "https://open.spotify.com/playlist/...", "Playlist URL is not valid!"

# Authenticate with Spotify API
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               redirect_uri=redirect_uri,
                                               scope="playlist-read-private,playlist-modify-public"))

# Create a dictionary that we'll use for storing track metadata
# TODO - we convert this to a list of objects later, when we might as well just make it a list of objects to start with, but requires some refactoring
tracks_dict = dict()

# Get tracks from a given playlist ID.
playlist_id = extract_playlist_id(PLAYLIST_URL)
playlist_tracks = sp.playlist_tracks(playlist_id, limit=50)

while playlist_tracks:
    for track_obj in playlist_tracks['items']:
        track = track_obj['track']
        tracks_dict[track['id']] = {
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'key': None,
            'bpm': None,
            'uri': track['uri']
        }
    
    if playlist_tracks['next']:
        playlist_tracks = sp.next(playlist_tracks)
    else:
        playlist_tracks = None


# If tracks_dict contains more than 100 tracks, we need to get the audio features in chunks from the API
max_track_ids = 100
num_tracks = len(tracks_dict)

if num_tracks == 0:
    print("Error! No tracks found.")
    exit()

# Divide the track ids into chunks of max_track_ids
track_ids_chunks = [list(tracks_dict.keys())[i:i+max_track_ids] for i in range(0, num_tracks, max_track_ids)]

for chunk in track_ids_chunks:
    # Fetch audio features for each track in the chunk
    tracks_meta = sp.audio_features(chunk)
    
    for track_meta_obj in tracks_meta:
        track_id = track_meta_obj['id']
        tracks_dict[track_id].update({
            'key': track_meta_obj['key'],
            'mode': track_meta_obj['mode'],
            'bpm': track_meta_obj['tempo'],
        })
        
        # Use the pitch_to_camelot() function to get additional data for each track
        camelot, key_tonal = pitch_to_camelot(track_meta_obj['key'], track_meta_obj['mode'])
        tracks_dict[track_id].update({
            'camelot': camelot,
            'key_tonal': key_tonal,
        })

# TODO - this simply changes the schema from a dictionary to a list of objects, we could create it as such to begin with above
new_list = []
for key, value in tracks_dict.items():
    new_dict = value.copy()
    new_dict["id"] = key
    new_list.append(new_dict)

# Assess the similarity between all tracks and then reorder the list
sorted_list = reorder_list(new_list)
# pprint(sorted_list, indent=4, width=300)

# Create a list containing just the track URIs
track_uris_list = []
for obj in sorted_list:
    track_uris_list.append(obj['uri'])
pprint("# of items to be added to new playlist: " + str(len(track_uris_list)))

# Experiment - reverse order for energizing style?
track_uris_list.reverse()


def create_new_playlist():
    # Get the current user id
    user = sp.current_user()['id']

    # Get the current playlist name and description
    # Note, the API returns fields in alphabetical order, not according to the order of fields passed as arguments
    playlist_desc, playlist_name = sp.playlist(playlist_id, fields="description,name").values()

    print(f"Current playlist name is {playlist_name}\nCurrent playlist description: {playlist_desc}")

    # TODO - check if the new playlist name is > 100 chars, decide what to do if it is
    new_playlist_name = f"{playlist_name} (sorted)"
    new_playlist_desc = f"{playlist_desc} (sorted by Better Playlists)"

    # Create a new playlist
    new_playlist_id = sp.user_playlist_create(user, new_playlist_name, public=True, collaborative=False, description=new_playlist_desc)['id']

    # Add the tracks to the new playlist in batches of 100
    max_size = 100
    split_uris = [track_uris_list[i:i+max_size] for i in range(0, len(track_uris_list), max_size)]
    for uris in split_uris:
        sp.playlist_add_items(new_playlist_id, uris)

    pprint(f"New playlist ID is {new_playlist_id}")
    return new_playlist_id


new_playlist_id = create_new_playlist()
print(f"New playlist URL is https://open.spotify.com/playlist/{new_playlist_id}")
