from lyricsgenius import Genius
import os
import argparse
import time

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

artist_names = [
    "Deftones", "Misfits", "Bones", "A$AP Rocky", "Linkin Park", "Korn", "Kanye West", "Travis Scott", "The Smiths", "Slipknot",
    "Lil Uzi Vert", "Future", "Drake", "Title Fight", "Slowdive", "Bring Me The Horizon", "Evanescence", "Twin Tribes",
    "$uicideboy$", "Yeat", "Superheaven", "TOOL", "Playboi Carti", "Lil Peep", "Nirvana", "Kendrick Lamar", "Metallica", "21 Savage",
    "Joy Division", "Crystal Castles", "Lebanon Hanover", "Limp Bizkit", "Sunny Day Real Estate", "Blink 182", "Sum 41", "The Cure",
    "Snow Strippers", "Destroy Lonely", "Ken Carson", "J. Cole", "Bladee", "Yung Lean", "Marilyn Manson", "DUCKBOY", "Eminem",
    "Type O Negative", "The Weeknd", "Young Thug", "Gunna", "System of A Down"
]

# Drake, Kanye West, Lil Uzi Vert,

print(f"Number of artists: {len(artist_names)}")

parser = argparse.ArgumentParser(description="Pass API key for a script")

parser.add_argument(
    "--api_key",
    type=str,
    required=True,
    help="Your Genius API key"
)

args = parser.parse_args()



def main():
    genius = Genius(args.api_key)

    not_processed_artists = set([artist_name for artist_name in artist_names
                                 if not os.path.exists(os.path.join(CURRENT_DIRECTORY, f'{artist_name}.json'))])

    print(f'Not processed artists: {not_processed_artists}')

    while len(not_processed_artists) > 0:
        artist_name = not_processed_artists.pop()

        if os.path.exists(os.path.join(CURRENT_DIRECTORY, f'{artist_name}.json')):
            print(f'{artist_name}.json already exists')
            continue

        try:
            artist = genius.search_artist(artist_name, max_songs=100, sort="popularity")
            artist.save_lyrics(filename=f'{artist_name}.json')
        except Exception as e:
            print(f'Exception: {e}')
            not_processed_artists.add(artist_name)
            print('Sleeping for 15 seconds')
            time.sleep(15)

        print(f'After this iteration, not processed artists: {not_processed_artists}')

if __name__ == "__main__":
    main()