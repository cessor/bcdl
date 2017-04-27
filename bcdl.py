import json
import os
import requests
import re
import sys


RESERVED_CHARS = "<>:\"/\\|?*[];=%&"


def fs_friendly(filename):
    '''Removes illegal characters from titles, such as
      Jeremy Blake - Remember Etta?
      that prevent writing filenames under windows.
      See: https://msdn.microsoft.com/en-us/library/windows/desktop/aa365247(v=vs.85).aspx
    '''
    filename = filename.replace(' & ', ' and ')
    return ''.join([
        c for
        c in filename
        if c not in RESERVED_CHARS
    ])


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
            if not url.startswith('http:'):
                url = 'http:' + url
            self.binary_data = requests.get(url).content


class Album(object):

    def __init__(self, artist, title, tracks):
        self.tracks = tracks
        self.artist = artist
        self.title = title
        self.directory = self.artist + "/" + self.title

    def download(self):
        print("=========================================")
        directory = fs_friendly(self.directory)
        print("Starting download: " + directory)
        if not os.path.exists(directory):
            os.makedirs(directory)
        for track in self.tracks:
            print("  [downloading " + track.filename() + "]")
            track.download()
            with open(directory + "/" + track.filename(), 'wb') as f:
                f.write(track.binary_data)
        print("=========================================")


def parse_tracks(html):
    raw_json = re.search(r'trackinfo: (?P<tracks>.*),', html).group('tracks')
    json_tracks = json.loads(raw_json)
    return (Track(json_track) for json_track in json_tracks)


def parse_album_from(html):
    artist = re.search(r'artist: "(?P<artist>.*)",', html).group('artist')
    title = re.search(r'album_title: "(?P<title>.*)",', html).group('title')
    tracks = parse_tracks(html)
    return Album(artist, title, tracks)


def main():
    html = requests.get(sys.argv[1]).text
    album = parse_album_from(html)
    album.download()

if __name__ == "__main__":
    main()
