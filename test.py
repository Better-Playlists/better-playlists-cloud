import os
import html
from pprint import pprint

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from utils import (pitch_to_camelot, 
                    extract_playlist_id, 
                    reorder_list, 
                    convert_tracks_dict_to_list, 
                    create_new_playlist)

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
PLAYLIST_URL = input("Spotify playlist URL to sort:")
assert PLAYLIST_URL != "https://open.spotify.com/playlist/...", "Playlist URL is not valid!"

# Create the Spotipy Client using Spotify access token
try: 
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                client_secret=client_secret,
                                                redirect_uri=redirect_uri,
                                                scope="playlist-read-private,playlist-modify-public"))
except Exception as e:
    print(f"An error occurred initializing the Spotipy client: {e}")

# Create a dictionary that we'll use for storing track metadata
tracks_dict = dict()
# Get tracks from a given playlist ID.
playlist_id = extract_playlist_id(PLAYLIST_URL)
playlist_tracks = sp.playlist_tracks(playlist_id, limit=50)

while playlist_tracks:
    for track_obj in playlist_tracks['items']:
        track = track_obj['track']
        tracks_dict[track['id']] = {
            'artist': track['artists'][0]['name'],
            'bpm': None,
            'camelot': None,
            'key': None,
            'key_tonal': None,
            'mode': None,
            'name': track['name'],
            'uri': track['uri']
        }

    if playlist_tracks['next']:
        playlist_tracks = sp.next(playlist_tracks)
    else:
        playlist_tracks = None

num_tracks = len(tracks_dict)
if num_tracks == 0:
    print("Error! No tracks found.")
    exit()

# In case tracks_dict contains more than 100 tracks, we need to query for audio features in chunks 
# Divide the track ids into chunks of max_track_ids, creating a list of lists of the track ids
max_track_ids = 100
track_ids_chunks = [list(tracks_dict.keys())[i:i+max_track_ids] for i in range(0, num_tracks, max_track_ids)]

# Fetch audio features for each track in the chunk
for chunk in track_ids_chunks:
    tracks_meta = sp.audio_features(chunk)

    for track_meta_obj in tracks_meta:
        track_id = track_meta_obj['id']
        tracks_dict[track_id].update({
            'bpm': track_meta_obj['tempo'],
            'key': track_meta_obj['key'],
            'mode': track_meta_obj['mode'],
        })

        # Use the pitch_to_camelot() function to get additional data for each track
        camelot, key_tonal = pitch_to_camelot(track_meta_obj['key'], track_meta_obj['mode'])
        tracks_dict[track_id].update({
            'camelot': camelot,
            'key_tonal': key_tonal,
        })

# Convert the dictionary to a list of objects
unsorted_tracks_list = convert_tracks_dict_to_list(tracks_dict)

# Assess the similarity between all tracks and then reorder the list
sorted_tracks_list = reorder_list(unsorted_tracks_list)

# Create a list containing just the track URIs
sorted_track_uris_list = []
for track in sorted_tracks_list:
    sorted_track_uris_list.append(track['uri'])
# pprint("# of items to be added to new playlist: " + str(len(track_uris_list)))

# Experiment - reverse order for energizing style?
sorted_track_uris_list.reverse()

# Get the current user id (inherited from access token)
user = sp.current_user()['id']
pprint(f"User is {user}")
try:
    playlist_desc, playlist_name = sp.playlist(playlist_id, fields="description,name").values()
except Exception as e:
    print(f"Error fetching playlist information via the playlist id: {e}")

print(f"Playlist name is: {playlist_name}")
print(f"Playlist description is: {html.unescape(playlist_desc)}")
new_playlist_name = f"{playlist_name} (sorted by Better Playlists)"
