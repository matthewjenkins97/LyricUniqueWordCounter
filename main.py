"""This is a program which calculates the number of unique words an artist has in their
discography."""

import os
import sys
import json
import re
import lyricsgenius
import requests

SILENT_MODE = True

def get_albums(artist_name, cutoff_year=2023):
    """Gets the albums from the given artist and saves all the lyrics for said albums into JSON
    files labelled Lyrics_{albumname}.json"""

    # please substitute this with your own genius key if you are going to fork this.
    genius = lyricsgenius.Genius("GehPJjxd7tBLvvMTbDQnTb01EV00_Pt6Swzp6N2aunBWlVSZ8zlQzZ0GYugYmrnT")
    genius.remove_section_headers = True

    # search for artist, get artist ID for searching artist's albums, search albums
    artist_search = genius.search_artists(artist_name)
    artist_id = artist_search["sections"][0]["hits"][0]["result"]["id"]
    
    # finding all albums through
    page = 1
    albums = []
    current_page = genius.artist_albums(artist_id, 50, page)
    albums.extend(current_page["albums"])
    while current_page["next_page"] is not None:
        page += 1
        current_page = genius.artist_albums(artist_id, 50, page)
        albums.extend(current_page["albums"])

    # sort albums by year (earliest to latest)
    def sort_by_year(json):
        try:
            return f"{json['release_date_components']['year']}"
        except KeyError:
            return str(sys.maxsize)
        except TypeError:
            return str(sys.maxsize)
        
    # filter by cutoff year (useful if you're searching for an artist with a lot of material after they break up)
    def filter_by_year(json):
        year = sort_by_year(json)
        if int(year) <= int(cutoff_year):
            return True
        else:
            return False
        
    albums.sort(key = sort_by_year)
    albums = filter(filter_by_year, albums)
    
    # save each album's lyrics in a json file
    for album in albums:
        try:
            search_query = f"{artist_name} {album['name']}"
            searched_album = genius.search_album(search_query)
            if searched_album is not None:
                if SILENT_MODE:
                    searched_album.save_lyrics()
                else:
                    print(f"{searched_album.artist} - {searched_album.name}")
                    print("Album ok? Y/n")
                    user_input = input()
                    if user_input.upper() == "Y" or user_input == "":
                        searched_album.save_lyrics()
                    elif user_input.upper() == "N":
                        continue
                    
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

    # get each file and sort it by creation time
    list_of_files = list(filter(os.path.isfile, os.listdir("./")))
    list_of_files.sort(key=os.path.getmtime)

    # get each file that starts with Lyrics, load every track, removing the first section and last section
    # and then add that to the buffer
    # with lyricsgenius the first section starts like "Song Name Lyrics\n"
    # the last section always seems to end with a random number followed by the word "Embed"
    for file in list_of_files:
        if file.startswith("Lyrics"):
            lyrics = open(file, "r")
            lyrics_buffer = json.load(lyrics)
            for i in range(len(lyrics_buffer["tracks"])):
                lyrics = lyrics_buffer["tracks"][i]["song"]["lyrics"]
                lyrics = lyrics.partition("\n")[-1]
                lyrics = re.sub(r'\d+Embed', '', lyrics)
                buffer += lyrics

    # turn buffer lowercase, remove new lines, remove apostrophes, remove non alphanumeric and space characters,
    # split each word, and use only the first 35000 words
    # 35000 is used per the logic in https://pudding.cool/projects/vocabulary/index.html
    buffer = buffer.lower()
    buffer = re.sub('\n', ' ', buffer)
    buffer = re.sub('\'', '', buffer)
    buffer = re.sub('[ ](?=[ ])|[^-_A-Za-z0-9 ]+', '', buffer)
    buffer = buffer.split(' ')
    buffer = buffer[0:35000]

    # get length of the set with all unique words
    # return unique strings and diversity percentage (perhaps that's not needed)
    unique_strings = len(set(buffer))
    print(f"{unique_strings} unique strings")
    print(unique_strings / len(buffer))

    # TODO: remove all json files which start with Lyrics after we generate 
    # Maybe not because we're optimally running this in a docker container?

def main():
    """main method."""
    if len(sys.argv) == 2:
        get_albums(sys.argv[1])
        generate_unique_word_count()
    elif len(sys.argv) == 3:
        get_albums(sys.argv[1], sys.argv[2])
        generate_unique_word_count()
    else:
        print("USAGE: python main.py artist_name optional_silent_mode_Y/N")

main()
