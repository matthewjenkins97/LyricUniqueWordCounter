# LyricUniqueWordCounter
Given an artist, this program goes through a random selection of 35000 words in their discography and counts how many unique words they use.

# Logic
This program is based off the logic behind one of my favorite uses of data science, [the rap vocabulary sheet from pudding.cool](https://pudding.cool/projects/vocabulary/index.html). What they do is get the first 35000 words of an artist's vocabulary, and count how many unique words are used in those first 35000. The more unique words, the more diverse of a vocabulary. There are a lot of cool findings from this article, such as hip hop in general having a much more diverse vocabulary than rock and country, and even the least diverse vocabulary rapper contains more unique words than a rock or country artist.

In my version, an artist is provided as input to the program `python3 main.py "Freddie Gibbs"`. We then go find the genius ID for that artist and use it to find a selection of albums in the database. We then save each album as a json file labelled `Lyrics_{albumname}.json`. Once that is complete, we search through this group of album lyrics by creation time, and add all the lyrics to a buffer, removing the first and last line of the lyrics (as those are extraneous words provided by the program we don't need). We then lowercase everything, remove apostrophes, new lines, and non alphanumeric and non space characters, and split all the words on each space character, and then take the first 35000 words. We then compute a set on the buffer so we get all the unique words.

# TODO
Right now I'm aware the "sort by album year" functionality when downloading lyrics is buggy so that needs a fix. Also I am unsure as to whether I want to remove the lyrics when complete, as I am currently running this in a Docker container whenever I want to check an artist's vocabulary.
