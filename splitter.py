import os
import pprint
import re
import unicodedata

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


artist_names = [
    "Deftones", "Misfits", "Bones", "A$AP Rocky", "Linkin Park", "Korn", "Kanye West", "Travis Scott", "The Smiths", "Slipknot",
    "Lil Uzi Vert", "Future", "Title Fight", "Slowdive", "Bring Me The Horizon", "Evanescence", "Twin Tribes",
    "$uicideboy$", "Yeat", "Superheaven", "TOOL", "Playboi Carti", "Lil Peep", "Nirvana", "Kendrick Lamar", "Metallica", "21 Savage",
    "Joy Division", "Crystal Castles", "Lebanon Hanover", "Limp Bizkit", "Sunny Day Real Estate", "Blink 182", "Sum 41", "The Cure",
    "Snow Strippers", "Destroy Lonely", "Ken Carson", "J. Cole", "Bladee", "Yung Lean", "Marilyn Manson", "DUCKBOY", "Eminem",
    "The Weeknd", "Young Thug", "Gunna", "System of A Down"
]


def split_documents():
    max_seq_len = -1e10
    documents = []
    ids = []
    page_contents = []

    for artist_name in artist_names:
        with open(os.path.join(CURRENT_DIRECTORY, f'data/txt/{artist_name}.txt'), 'r', encoding='utf-8') as file:
            data = ''.join(file.readlines())

        texts = data.split('Title:')

        parts = data.split('Artist Description:')

        artist_alt_names_part = parts[0]
        splitted_artist_alt_names_part = artist_alt_names_part.split('Alternate Names:')

        alternate_names = None

        if len(splitted_artist_alt_names_part) == 1:
            artist = parts[0]
        elif len(splitted_artist_alt_names_part) == 2:
            artist = splitted_artist_alt_names_part[0]
            alternate_names = splitted_artist_alt_names_part[1].strip()
            alternate_names = alternate_names.split(',')
            alternate_names = [name.strip() for name in alternate_names]
            alternate_names = [re.sub(r'\d+Embed', '', el) for el in alternate_names]


        # Deleting substring "Artist:", whitespaces and comma as last character
        artist = artist.replace('Artist:', '').strip()
        artist = artist.replace(',', '')
        artist = re.sub(r'\d+Embed', '', artist)

        description_and_songs = parts[1].strip()

        artist_description_and_songs_splitted = description_and_songs.split('Title:')

        artist_description = artist_description_and_songs_splitted[0]
        artist_description = re.sub(r'\d+Embed', '', artist_description)

        texts = [el.strip() for el in texts]
        texts = [re.sub(r'\d+Embed', '', el) for el in texts]
        texts = [re.sub(r'See\s+[\w\s]+LiveGet\s+tickets\s+as\s+low\s+as\s+\$\d+\s*You\s+might\s+also\s+like', '', el) for el in texts]
        texts = [el.replace("Embed", "") for el in texts]

        max_len_text = max([len(text) for text in texts])

        if max_len_text > max_seq_len:
            max_seq_len = max_len_text

        if alternate_names is not None:
            documents.append({
                "id": f"{artist}#info",
                "metadata": {
                    "artist": artist,
                    "alternate_names": alternate_names,
                    "artist_description": artist_description,
                    "source": f"{artist_name}.txt"
                }
            })
        else:
            documents.append({
                "id": f"{artist}#info",
                "metadata": {
                    "artist": artist,
                    "artist_description": artist_description,
                    "source": f"{artist_name}.txt"
                }
            })
        page_contents.append(texts[0])
        ids.append(f"{artist}#info")

        # extracting metadata
        titles = re.findall(r"Title:\s*(.*?)\s*Release Date:", description_and_songs)
        release_dates = re.findall(r"Release Date:\s*(.*?)\s*, URL:", description_and_songs)
        urls = re.findall(r"URL:\s*(.*?)\s*Song Description:", description_and_songs)
        song_descriptions = re.findall(r"(?<=Song Description:)(.*?)(?=Lyrics:)", description_and_songs, re.DOTALL)
        lyrics = re.findall(r"(?<=Lyrics:)(.*?)(?=Title:)", description_and_songs, re.DOTALL)

        # ensuring deleting whitespaces
        titles = [el.strip() for el in titles]
        release_dates = [el.strip() for el in release_dates]
        urls = [el.strip() for el in urls]
        song_descriptions = [el.strip() for el in song_descriptions]
        lyrics = [el.strip() for el in lyrics]


        # deleting substring "Embed" (artifact of scrapping)
        release_dates = [re.sub(r'\d+Embed', '', el) for el in release_dates]
        urls = [re.sub(r'\d+Embed', '', el) for el in urls]
        song_descriptions = [re.sub(r'\d+Embed', '', el) for el in song_descriptions]
        lyrics = [re.sub(r'\d+Embed', '', el) for el in lyrics]
        lyrics = [re.sub(r'See\s+[\w\s]+LiveGet\s+tickets\s+as\s+low\s+as\s+\$\d+\s*You\s+might\s+also\s+like', '', el) for el in lyrics]

        last_lyrics = description_and_songs.split('Lyrics:')[-1]
        lyrics.append(last_lyrics)


        for i, (title, release_date, url, song_description, lyric) in enumerate(zip(titles, release_dates, urls, song_descriptions, lyrics)):
            normalized_title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')

            ids.append(f"{artist}#{normalized_title}")
            page_contents.append(texts[i+1])

            documents.append({
                "id": f"{artist}#{normalized_title}",
                "metadata": {
                    "title": normalized_title,
                    "release_date": release_date,
                    "url": url,
                    "song_description": song_description,
                    "lyrics": lyric,
                    "source": f"{artist_name}.txt"
                }
            })

        assert len(titles) == len(release_dates) == len(song_descriptions) == len(urls) == len(lyrics) == len(texts) - 1


    print('max seq length:', max_seq_len)
    return documents, page_contents, ids

if __name__ == '__main__':
    documents, texts, ids = split_documents()
    pprint.pprint(documents[:5])
    print('Number of documents:', len(documents))