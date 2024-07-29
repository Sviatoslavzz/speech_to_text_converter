from youtube_transcript_api import YouTubeTranscriptApi

from yt_dlp_loader import Yt_loader


def get_caption_by_link(directory: str, links: list):
    #TODO переделать на проверку 1 линки и возврат да или нет чтобы можно было понять нужно ли запускать модельку
    for link in links:
        video_id = link.split("v=")[1]
        title, valid = Yt_loader.get_title(link)
        if not valid:
            print(f"Unable to get video title for {link}")
            continue
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'ru'])
            with open(f'{directory}/{title}.txt', "w") as file:
                for entry in transcript:
                    file.write(entry['text'].replace('\n', ' ') + ' ')
        except Exception as e:
            print(f"An error occurred: {str(e)}")
