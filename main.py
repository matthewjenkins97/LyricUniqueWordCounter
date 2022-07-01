"""This is a program which calculates the number of unique words an artist has in their
discography."""

import os
import sys
import json
import re
import lyricsgenius
import requests

def get_albums(artist_name):
    """Gets the albums from the given artist and saves all the lyrics for said albums into JSON
    files labelled Lyrics_{albumname}.json"""

    # please substitute this with your own genius key if you are going to fork this.
    genius = lyricsgenius.Genius("GehPJjxd7tBLvvMTbDQnTb01EV00_Pt6Swzp6N2aunBWlVSZ8zlQzZ0GYugYmrnT")
    genius.remove_section_headers = True
    artist_search = genius.search_artists(artist_name)
    artist_id = artist_search["sections"][0]["hits"][0]["result"]["id"]
    albums = genius.artist_albums(artist_id)
    albums = albums["albums"]

    # do we want to sort by creation dates?
    # seems like there's a case where it can shit itself if you give it a none type.

    # print(albums)

    # def sort_by_year(json):
    #     try:
    #         return json["release_date_components"]["year"]
    #     except KeyError:
    #         return 0
    # albums.sort(key = sort_by_year)
    
    for album in albums:
        try:
            searched_album = genius.search_album(f"{album['name']} {artist_name}")
            searched_album.save_lyrics()
        except requests.Timeout:
            continue


def generate_unique_word_count():
    """generates the unique word count by going through all the lyrics, pruning
    extra characters at the beginning and end of each lyric sheet,
    removing new lines, apostrophes, and non alphanumeric and space
    characters.
    we then split each word and use only the first 35000 words to calculate
    the unique strings."""

    buffer = ""
    list_of_files = list(filter(os.path.isfile, os.listdir("./")))
    list_of_files.sort(key=os.path.getmtime)
    for file in list_of_files:
        if file.startswith("Lyrics"):
            lyrics = open(file, "r")
            lyrics_buffer = json.load(lyrics)
            for i in range(len(lyrics_buffer["tracks"])):
                lyrics = lyrics_buffer["tracks"][i]["song"]["lyrics"]
                lyrics = lyrics.partition("\n")[-1]
                lyrics = re.sub(r'\d+Embed', '', lyrics)
                buffer += lyrics

    buffer = buffer.lower()
    buffer = re.sub('\n', ' ', buffer)
    buffer = re.sub('\'', '', buffer)
    buffer = re.sub('[ ](?=[ ])|[^-_A-Za-z0-9 ]+', '', buffer)
    buffer = buffer.split(' ')
    buffer = buffer[0:35000]

    unique_strings = len(set(buffer))

    print(f"{unique_strings} unique strings")
    print(unique_strings / len(buffer))

    # TODO: remove all json files which start with Lyrics after we generate 

def main():
    """main method."""

    if len(sys.argv) == 2:
        get_albums(sys.argv[1])
        generate_unique_word_count()
    else:
        print("USAGE: python main.py artist_name")

main()
