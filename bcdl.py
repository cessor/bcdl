import json
import os
import re
import requests
import sys


RESERVED_CHARS = "<>:\"/\\|?*[];=%&"


def fs_friendly(filename):
    '''Removes illegal characters from titles, such as Questionmarks.
      that prevent writing filenames under windows.
      See: https://msdn.microsoft.com/en-us/library/windows/desktop/aa365247(v=vs.85).aspx
    '''
    filename = filename.replace(' & ', ' and ')
    return ''.join([
        c for
        c in filename
        if c not in RESERVED_CHARS
    ])


def add_schema_if_necessary(url):
    if not url.startswith('http:'):
        url = 'http:' + url
    return url


class Track(object):

    def __init__(self, json):
        self.json = json
        self.binary_data = None
        self.number = self.json["track_num"]
        self.title = self.json["title"]

    def filename(self):
        tracknum = ["", "0"][self.number < 10] + str(self.number)
        filename_ = tracknum + " - " + self.title + ".mp3"
        filename_ = fs_friendly(filename_)
        return filename_

    def download(self):
        if self.binary_data is None:
            url = self.json["file"]["mp3-128"]
            url = add_schema_if_necessary(url)
            self.binary_data = requests.get(url).content


class Album(object):

    def __init__(self, artist, title, tracks):
        self.tracks = tracks
        self.artist = artist
        self.title = title

    @property
    def directory(self):
        return os.path.join(
            fs_friendly(self.artist),
            fs_friendly(self.title)
        )

    def download(self):
        print("=========================================")
        directory = self.directory
        print("Starting download: " + directory)
        if not os.path.exists(directory):
            os.makedirs(directory)

        for track in self.tracks:
            path = directory + "/" + track.filename()
            if os.path.exists(path):
                print("  [skipping " + track.filename() + "]")
                continue
            print("  [downloading " + track.filename() + "]")
            track.download()
            with open(path, 'wb') as f:
                f.write(track.binary_data)
        print("=========================================")


FIELD = r'%s: "(?P<%s>.*)",'
TRACK = r'%s: (?P<%s>.*),'


class Page(object):

    def __init__(self, text):
        self._text = text

    def _find(self, pattern, field):
        match = re.search(pattern % (field, field), self._text)
        return match.group(field)

    def album(self):
        html = self._text
        artist = self._find(FIELD, 'artist')
        title = self._find(FIELD, 'album_title')
        tracks = self.tracks()
        return Album(artist, title, tracks)

    def tracks(self):
        html = self._text
        raw_json = self._find(TRACK, 'trackinfo')
        json_tracks = json.loads(raw_json)
        return (
            Track(json_track)
            for json_track
            in json_tracks
        )


def main():
    url = sys.argv[1]
    url = url.strip()
    print('Downloading ' + url)
    text = requests.get(url).text
    Page(text).album().download()


if __name__ == "__main__":
    main()
