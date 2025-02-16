from pprint import pprint

import yt_dlp


def main():
    with yt_dlp.YoutubeDL() as ydl:
        info_dict = ydl.extract_info("https://www.youtube.com/watch?v=tyZqw_UuiF0", download=False)
        formats = info_dict.get("formats", [])
        pprint(formats)

main()
