"""This is a program which calculates the number of unique words an artist has in their
discography."""

import os
import sys
import json
import re
import lyricsgenius
import requests

def get_albums(artist_name, cutoff_year, silent_mode, album_list_directory):
    """Gets the albums from the given artist and saves all the lyrics for said albums into JSON
    files labelled Lyrics_{albumname}.json"""

    # for silent mode, parsing the file for album names
    album_list = []
    if album_list_directory != "" and silent_mode:
        with open(album_list_directory, encoding="utf-8") as album_list_text:
            for line in album_list_text:
                line = re.sub('\'', '’', line)
                album_list.append(line.lower().rstrip())

    # please substitute this with your own genius key if you are going to fork this.
    genius = lyricsgenius.Genius("GehPJjxd7tBLvvMTbDQnTb01EV00_Pt6Swzp6N2aunBWlVSZ8zlQzZ0GYugYmrnT")
    genius.remove_section_headers = True

    # search for artist, get artist ID for searching artist's albums, search albums
    artist_search = genius.search_artists(artist_name)
    artist_id = artist_search["sections"][0]["hits"][0]["result"]["id"]

    # finding all albums of an artist
    page = 1
    albums = []
    current_page = genius.artist_albums(artist_id, 50, page)
    albums.extend(current_page["albums"])
    while current_page["next_page"] is not None:
        page += 1
        current_page = genius.artist_albums(artist_id, 50, page)
        albums.extend(current_page["albums"])

    def sort_by_year(json_data):
        """sort albums by year with provided JSON (earliest to latest)"""
        release_date = json_data['release_date_components']

        # timestamps will be in yyyymmdd format because it self sorts
        # there is probably a better way to do this.
        try:
            year = release_date['year']
            month = release_date['month']
            day = release_date['day']

            if release_date['month'] is None:
                month = "01"
            if release_date['day'] is None:
                day = "01"

            month = str(month).zfill(2)
            day = str(day).zfill(2)

            return f"{year}{month}{day}"

        # want to have any errant stuff out of the filter later
        except KeyError:
            return str(sys.maxsize)
        except TypeError:
            return str(sys.maxsize)

    def filter_by_year(json_data):
        """filter by cutoff year (useful if you're searching for an artist with a lot
        of material after they break up)"""
        year = sort_by_year(json_data)
        return int(year) <= int(f"{cutoff_year}0101")

    albums.sort(key = sort_by_year)
    albums = filter(filter_by_year, albums)

    # minimizing any searches that we don't need in silent mode
    if silent_mode:
        albums = filter(lambda x: x["name"].lower().rstrip() in album_list, albums)

    # save each album's lyrics in a json file
    for album in albums:

        success = False

        # timeout retries
        for _ in range(5):

            try:
                # Genius seems to vary what is returned based off of
                # search query so we specify 2 variants to search
                #
                # TODO: maybe include year in one of the searches to deal self-titled albums
                # this depends on Genius's SEO

                album_name = album["name"].rstrip()
                search_queries = [f"{album_name}",
                                  f"{album_name} {artist_name}", 
                                  f"{artist_name} {album_name}"]

                for query in search_queries:

                    album_to_download = genius.search_album(query)

                    # checking if album artist and name match album_list
                    if silent_mode:
                        if album_to_download.name.lower() in album_list and \
                        album_to_download.artist.name.lower() == artist_name.lower():
                            album_to_download.save_lyrics()
                            success = True
                            break

                    # user input section
                    else:
                        user_input = ''
                        print("Album found:")
                        print(f"{album_to_download.artist} - {album_to_download.name}")
                        print("Album ok? Y/n, s to skip album search")
                        user_input = input()
                        if user_input.lower() == "y" or user_input == "":
                            album_to_download.save_lyrics()
                            success = True
                            break
                        if user_input.lower() == "s":
                            success = True
                            break

                    if success:
                        break

                if success:
                    break

            except requests.Timeout:
                pass

            except KeyboardInterrupt:
                print()
                return

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

    # get each file that starts with Lyrics, load every track, removing the first section and last
    # section and then add that to the buffer
    # with lyricsgenius the first section starts like "Song Name Lyrics\n"
    # the last section always seems to end with a random number followed by the word "Embed"
    for file in list_of_files:
        if file.startswith("Lyrics"):
            lyrics = open(file, "r", encoding="utf-8")
            lyrics_buffer = json.load(lyrics)
            for i in range(len(lyrics_buffer["tracks"])):
                lyrics = lyrics_buffer["tracks"][i]["song"]["lyrics"]
                lyrics = lyrics.partition("\n")[-1]
                lyrics = re.sub(r'\d+Embed', '', lyrics)
                buffer += lyrics

    # turn buffer lowercase, remove new lines, remove apostrophes, remove non alphanumeric and
    # space characters, split each word, and use only the first 35000 words
    # 35000 is used per the logic in https://pudding.cool/projects/vocabulary/index.html
    buffer = buffer.lower()
    buffer = re.sub('\n', ' ', buffer)
    buffer = re.sub('\'', '', buffer)
    buffer = re.sub('[ ](?=[ ])|[^-_A-Za-z0-9 ]+', '', buffer)
    buffer = buffer.split(' ')
    buffer = buffer[0:35000]

    # get length of the set with all unique words
    # return unique strings and diversity percentage (perhaps that's not needed)
    print(f"Total number of strings: {len(buffer)}")
    unique_strings = len(set(buffer))
    print(f"{unique_strings} unique strings")
    print(f"Uniqueness percentage: {(unique_strings / len(buffer)) * 100}%")

    # TODO: remove all json files which start with Lyrics after we generate
    # Maybe not because we're optimally running this in a docker container?

def main():
    """main method."""
    if len(sys.argv) > 1:

        # defaults
        artist = ""
        cutoff_year = "2023"
        silent_mode = False
        album_name_file = ""

        # argv parsing
        for i in range(1, len(sys.argv)):
            if re.match(r"\d{4}",sys.argv[i]):
                cutoff_year = sys.argv[i]
            elif re.match("-silent", sys.argv[i]):
                silent_mode = True
            elif os.path.exists(sys.argv[i]):
                album_name_file = sys.argv[i]
            else:
                artist = sys.argv[i]

        # if silent mode is missing album list or cutoff is malformatted
        if silent_mode and album_name_file == "" or len(cutoff_year) != 4:
            fail()

        get_albums(artist, cutoff_year, silent_mode, album_name_file)
        generate_unique_word_count()

    else:
        fail()

def fail():
    """if we can't run the code because of bad argv parsing execute these lines and exit"""
    print("USAGE: python main.py artist_name cutoff_year -silent album_name_list_file")
    print("Cutoff year must be 4 digits. \"-silent\" requires an album_name_list file path to run.")
    sys.exit(1)

main()
