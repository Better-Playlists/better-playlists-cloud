import html
import random

def extract_playlist_id(url):
    """
    Extracts the playlist ID from a Spotify playlist URL.

    Args:
        url (str): The URL of the Spotify playlist.

    Returns:
        str: The ID of the playlist.
    """
    if '?' in url:
        playlist_id = url.split("/playlist/")[1].split("?")[0]
    else:
        playlist_id = url.split("/playlist/")[1]
    return playlist_id


"""
This method takes a Pitch Class notation (PCN) and a mode (0 for minor, 1 for major), 
and returns a string containing the corresponding Camelot Wheel representation (1A-12B)
and the tonal representation of the note (e.g. "C major").
"""
def pitch_to_camelot(pcn, major):
    # Return the corresponding tonal representation of the input note
    tonal = pitch_class_dict[pcn] + " " + major_minor_dict[major]
    
    # Return the corresponding Camelot Wheel representation of the input note
    camelot = cw_map_string[pcn,major]
    
    return camelot, tonal

# The special sauce algorithm
def reorder_list(unsorted_tracks_list, camelot_similarities):
    try: 
        reordered_list = []
        remaining_tracks = unsorted_tracks_list.copy()
        current_track = remaining_tracks.pop(0)
        reordered_list.append(current_track)
        while remaining_tracks:
            similarities = camelot_similarities[current_track['camelot']]
            similar_tracks = [track for track in remaining_tracks if track['camelot'] in similarities]
            if similar_tracks:
                similar_tracks.sort(key=lambda track: similarities.index(track['camelot']))
                current_track = similar_tracks.pop(0)
                reordered_list.append(current_track)
                remaining_tracks.remove(current_track)
            else:
                remaining_similarities = {track['camelot']: 0 for track in remaining_tracks}
                for t1 in remaining_tracks:
                    for t2 in remaining_tracks:
                        if t2['camelot'] in camelot_similarities[t1['camelot']]:
                            remaining_similarities[t1['camelot']] += 1
                current_track = max(remaining_tracks, key=lambda track: remaining_similarities[track['camelot']])
                reordered_list.append(current_track)
                remaining_tracks.remove(current_track)
        return max_five(reordered_list)
    except Exception as e:
        print(f"An error occurred sorting the tracks list: {e}")


# Ensure (or die trying) no more than 6 tracks in a row have the same primary chord
# TODO - get audio_analysis key_confidence first and presort using confidence intervals to improve overall groups
def max_five(lst):
    try:
        # Initialize the list of unique camelot values and a counter
        camelot_list = [lst[0]["camelot"]]
        camelot_counter = 1

        # Iterate through the list starting from the second element
        for i in range(1, len(lst)):
            # Check if the current camelot value is the same as the previous one
            if lst[i]["camelot"] == lst[i-1]["camelot"]:
                # Increment the counter and append the camelot value to the list if it is not already present
                if lst[i]["camelot"] not in camelot_list:
                    camelot_list.append(lst[i]["camelot"])
                camelot_counter += 1
            else:
                # Reset the counter if the current camelot value is different from the previous one
                camelot_counter = 1

            # Check if we have 6 consecutive dictionaries with the same camelot value
            if camelot_counter == 6:
                # Get the index of the last dictionary with the same camelot value
                last_index = i
                while last_index < len(lst)-1 and lst[last_index+1]["camelot"] == lst[i]["camelot"]:
                    last_index += 1

                # Move the rest of the dictionaries with the same camelot value to the end of the list
                rest = lst[i:last_index+1]
                lst = lst[:i] + lst[last_index+1:] + rest

                # Reset the camelot list and counter
                camelot_list = []
                camelot_counter = 1

        return lst
    except Exception as e:
        print(f"An error occurred sorting the tracks list: {e}")



def convert_tracks_dict_to_list(tracks_dict):
    new_list = []
    try:
        for key, value in tracks_dict.items():
            new_dict = value.copy()
            new_dict["id"] = key
            new_list.append(new_dict)
    except AttributeError as e:
        print(f"Error converting tracks_dict to list: {e}")
    return new_list


def shuffle_unsorted_tracks_list(tracks_list):
    # Fisher-Yates algorithm, first index is excluded to preserve first song in original playlist
    n = len(tracks_list)
    for i in range(n - 1, 1, -1):
        j = random.randint(1, i)
        tracks_list[i], tracks_list[j] = tracks_list[j], tracks_list[i]
    return tracks_list


def create_new_playlist(user, sp, playlist_id, sorted_track_uris_list):
    """
    Get the current playlist name and description
    Note the API returns fields in alphabetical order, not according to the order of fields passed as arguments
    """
    try:
        playlist_desc, playlist_name = sp.playlist(playlist_id, fields="description,name").values()
    except Exception as e:
        print(f"Error fetching playlist information via the playlist id: {e}")
    
    new_playlist_name = f"{playlist_name} (sorted by Better Playlists)"
    new_playlist_desc = html.unescape(playlist_desc)

    # Some logic to handle cases where the new playlist name ends up being longer than 100 chars
    if len(new_playlist_name) > 100:
        new_playlist_name = f"{playlist_name} (sorted)"
        if len(new_playlist_name) > 100:
            new_playlist_name = f"{playlist_name} *"
            if len(new_playlist_name) > 100:
                new_playlist_name = playlist_name

    # Create a new playlist
    try: 
        new_playlist_id = sp.user_playlist_create(
            user, 
            new_playlist_name, 
            public=True, # TODO - public=request_json['make_public'] 
            collaborative=False, 
            description=new_playlist_desc
        )['id']
    except Exception as e:
        print(f"Error creating the playlist: {e}")

    # Add the tracks to the new playlist in batches of 100
    max_size = 100
    split_uris = [sorted_track_uris_list[i:i+max_size] for i in range(0, len(sorted_track_uris_list), max_size)]
    for uris in split_uris:
        try:
            sp.playlist_add_items(new_playlist_id, uris)
        except Exception as e:
            print(f"Error adding items to playlist {new_playlist_id}: {e}")

    return new_playlist_id


"""
Create a dictionary that maps the Pitch Class notation (PCN) and mode (major/minor) of a 
note to its corresponding Camelot Wheel representation. The keys of the dictionary are 
tuples containing the PCN (0-11) and mode (0 for minor and 1 for major), and the values 
are strings containing the Camelot Wheel code (1A-12B)
"""
cw_map_string = {
    (0,1):'8B',
    (1,1):'3B',
    (2,1):'10B',
    (3,1):'5B',
    (4,1):'12B',
    (5,1):'7B',
    (6,1):'2B',
    (7,1):'9B',
    (8,1):'4B',
    (9,1):'11B',
    (10,1):'6B',
    (11,1):'1B',
    (0,0):'5A',
    (1,0):'12A',
    (2,0):'7A',
    (3,0):'2A',
    (4,0):'9A',
    (5,0):'4A',
    (6,0):'11A',
    (7,0):'6A',
    (8,0):'1A',
    (9,0):'8A',
    (10,0):'3A',
    (11,0):'10A'
}

""" 
This is the priority of camelot wheel attributes similarities to use for the sorting algorithm.  
In plain English, it is +1 key, -1 key, scale change, diagonal mix, +7 key, mode change.
"""
camelot_similarities = {
    "1A": ["1A","2A", "12A", "1B", "12B", "8A", "4B"],
    "2A": ["2A","3A", "1A", "2B", "1B", "9A", "5B"],
    "3A": ["3A","4A", "2A", "3B", "2B", "10A", "6B"],
    "4A": ["4A","5A", "3A", "4B", "3B", "11A", "7B"],
    "5A": ["5A","6A", "4A", "5B", "4B", "12A", "8B"],
    "6A": ["6A","7A", "5A", "6B", "5B", "1A", "9B"],
    "7A": ["7A","8A", "6A", "7B", "6B", "2A", "10B"],
    "8A": ["8A","9A", "7A", "8B", "7B", "3A", "11B"],
    "9A": ["9A","10A", "8A", "9B", "8B", "4A", "12B"],
    "10A": ["10A","11A", "9A", "10B", "9B", "5A", "1B"],
    "11A": ["11A","12A", "10A", "11B", "10B", "6A", "2B"],
    "12A": ["12A","1A", "11A", "12B", "11B", "7A", "3B"],
    "1B": ["1B","2B", "12B", "1A", "2A", "8B", "10A"],
    "2B": ["2B","3B", "1B", "2A", "3A", "9B", "11A"],
    "3B": ["3B","4B", "2B", "3A", "4A", "10B", "12A"],
    "4B": ["4B","5B", "3B", "4A", "5A", "11B", "1A"],
    "5B": ["5B","6B", "4B", "5A", "6A", "12B", "2A"],
    "6B": ["6B","7B", "5B", "6A", "7A", "1B", "3A"],
    "7B": ["7B","8B", "6B", "7A", "8A", "2B", "4A"],
    "8B": ["8B","9B", "7B", "8A", "9A", "3B", "5A"],
    "9B": ["9B","10B", "8B", "9A", "10A", "4B", "6A"],
    "10B": ["10B","11B", "9B", "10A", "11A", "5B", "7A"],
    "11B": ["11B","12B", "10B", "11A", "12A", "6B", "8A"],
    "12B": ["12B","1B", "11B", "12A", "1A", "7B", "9A"]
}

# Create a dictionary that maps the Pitch Class notation (PCN) to its corresponding musical key.
pitch_class_dict = {
    0: "C",
    1: "C♯/D♭",
    2: "D",
    3: "D♯/E♭",
    4: "E",
    5: "F",
    6: "F♯/G♭",
    7: "G",
    8: "G♯/A♭",
    9: "A",
    10: "A♯/B♭",
    11: "B"
}

# Helper dictionary for mapping Spotify mode value to major/minor string
major_minor_dict = {
    0: "minor",
    1: "major"
}


