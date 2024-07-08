import os

from pytube import YouTube
import sys


def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    progress = f'Download progress: {int(percentage_of_completion)}%\n'
    sys.stdout.write('\r' + progress)
    sys.stdout.flush()


class Loader:
    def __init__(self, link):
        self.__yt = YouTube(link, on_progress_callback=on_progress)
        self.__stream = None
        self.__title = ""

    def __del__(self):
        os.remove(self.__title)

    def download_video(self):
        self.__prepare_title()
        self.__stream = self.__yt.streams.get_lowest_resolution()
        if self.__stream is not None:
            self.__stream.download(filename=self.__title)
        else:
            print("Unable to get video stream")
        return self.__title

    def download_audio(self):
        self.__prepare_title()
        self.__stream = self.__yt.streams.filter(only_audio=True).first()
        if self.__stream is not None:
            self.__stream.download(filename=self.__title)
        else:
            print("Unable to get audio stream")
        return self.__title

    def __prepare_title(self):
        self.__title = self.__yt.title.encode('utf-8').decode('utf-8').rstrip(' .') + ".mp4"
        replacements = {
            ',': ' ',
            '!': ' ',
            '?': ' ',
            "'": ' ',
            "/": '',
            ' ': '_',
            '\\': '',
            '|': ''
        }
        for old, new in replacements.items():
            self.__title = self.__title.replace(old, new)
