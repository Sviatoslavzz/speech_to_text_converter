import yt_dlp
from os import remove


class Yt_loader:
    def __init__(self, link: str):
        self._title = "example"
        self.link = link
        self._ydl_opts = {
            'format': 'bestaudio/best',  # Select the best audio quality available
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',  # Quality in kbps (e.g., 192)
            }],
            'outtmpl': f'{self._title}.%(ext)s',  # Output filename template
        }

    def __del__(self):
        if self._title.endswith(".mp3"):
            remove(self._title)
        if self._title.endswith(".webm"):
            remove(self._title)

    def get_title(self) -> (str, bool):
        try:
            with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.link, download=False)
                self._title = info_dict.get('title', None)
                self._prepare_title()
                return self._title, True
        except yt_dlp.utils.DownloadError:
            return self._title, False

    def _prepare_title(self):
        self._title = self._title.encode('utf-8').decode('utf-8').rstrip(' .')
        self._title = self._title.lower()
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
            self._title = self._title.replace(old, new)

    def download_audio(self) -> (str, bool):
        self._title, is_valid = self.get_title()
        if is_valid:
            self._ydl_opts['outtmpl'] = f'{self._title}.%(ext)s'
            try:
                with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
                    ydl.download([self.link])
                    self._title = self._title + ".mp3"
                    return f'{self._title}', True
            except yt_dlp.utils.DownloadError:
                print(f'An error occurred while downloading audio for: "{self.link}"')
                self._title = self._title + ".webm"
                return "", False
        else:
            print(f'provided link is not valid: "{self.link}"')
            return "", False
