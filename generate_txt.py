import json
import os
import re

artist_names = [
    "Deftones", "Misfits", "Bones", "A$AP Rocky", "Linkin Park", "Korn", "Kanye West", "Travis Scott", "The Smiths", "Slipknot",
    "Lil Uzi Vert", "Future", "Title Fight", "Slowdive", "Bring Me The Horizon", "Evanescence", "Twin Tribes",
    "$uicideboy$", "Yeat", "Superheaven", "TOOL", "Playboi Carti", "Lil Peep", "Nirvana", "Kendrick Lamar", "Metallica", "21 Savage",
    "Joy Division", "Crystal Castles", "Lebanon Hanover", "Limp Bizkit", "Sunny Day Real Estate", "Blink 182", "Sum 41", "The Cure",
    "Snow Strippers", "Destroy Lonely", "Ken Carson", "J. Cole", "Bladee", "Yung Lean", "Marilyn Manson", "DUCKBOY", "Eminem",
    "The Weeknd", "Young Thug", "Gunna", "System of A Down"
]
# artist_names = ["Deftones"]

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Song:
    def __init__(self, title, release_date, url, artist, lyrics, description):
        self.title = title
        # self.album = album
        self.release_date = release_date
        self.url = url
        self.artist = artist
        self.lyrics = lyrics
        self.description = description

    # def __repr__(self):
    #     return (f"Song: {self.title}\nRelease Date: {self.release_date}, URL: {self.url}\n"
    #             f"Description: {self.description}\nLyrics:\n{self.lyrics}")

    def __str__(self):
        return (f"\nTitle: {self.title}\nRelease Date: {self.release_date}, URL: {self.url}\n"
                f"Song Description: {self.description}\nLyrics:\n\n{self.lyrics}\n")

class ArtistDocument:
    def __init__(self, artist, description, alternate_names, songs):
        self.artist = artist
        self.description = description
        self.alternate_names = alternate_names
        self.songs = songs

    def __str__(self):
        return (
            f"Artist: {self.artist}{', Alternate Names: ' if self.alternate_names else ''}"
            f"{', '.join(self.alternate_names) if self.alternate_names else ''}\nArtist Description: {self.description}\n"
            f"\nSongs:\n{''.join([str(song) for song in self.songs])}"
        )

def main():
    artist_documents = []

    for artist_name in artist_names:
        print(artist_name)
        with open(os.path.join(CURRENT_DIRECTORY, f'data/json/{artist_name}.json'), 'r', encoding='utf-8') as file:
            data = json.load(file)

            # for song in data['songs']:
            #     lyrics = song['lyrics']
            #     lyrics = re.sub(r'.+Lyrics', '', lyrics)
            U_CHARACTERS = r'\\u[0-9A-Fa-f]{4}'

            # for song in data['songs']:
            #     print(type(song['release_date_for_display']))

            songs = [Song(
                song['title'],
                          # song['album']['name'],
                song['release_date_for_display'],
                song['url'],
                artist_name,
                song['lyrics'],
                song['description']['plain']
                     ) for song in data['songs']]

            for song in songs:
                # print(song.lyrics)
                song.lyrics = re.sub(r'.+Lyrics|\\u[0-9A-Fa-f]{4}', '', song.lyrics)
                song.description = re.sub(r'[^\x00-\x7F]+', '', song.description)

            # for song in songs:
            #     print(song)

            artist_document = ArtistDocument(
                artist_name,
                re.sub(U_CHARACTERS, '', data['description']['plain']),
                data['alternate_names'],
                songs)

            artist_document.description = re.sub(U_CHARACTERS, '', artist_document.description)

            with open(os.path.join(CURRENT_DIRECTORY, f'data/txt/{artist_name}.txt'), 'w', encoding='utf-8') as file:
                file.write(str(artist_document))

if __name__ == '__main__':
    main()