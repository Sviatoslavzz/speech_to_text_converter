import warnings
import os
import asyncio

from captions import get_caption_by_link
from youtube_api import get_channel_videos, get_channel_id_by_name
from transcribers.abscract import AbstractTranscriber
from transcribers.faster_whisper_transcriber import FasterWhisperTranscriber
from transcribers.whisper_transcriber import WhisperTranscriber
from objects import DownloadOptions
from yt_dlp_loader import Yt_loader

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")


def make_save_dir() -> str:
    dir_ = 'saved_files'
    if not os.path.exists(dir_):
        os.makedirs(dir_)
    return dir_


def collect_links() -> list:
    links = []
    channel_link = input(
        """You can enter a channel link to collect all videos from a channel, """
        """or press enter to proceed with simple links:\n""")
    if "youtube.com" in channel_link:
        try:
            amount, links = get_channel_videos(get_channel_id_by_name(channel_link.strip()))
            print(f"Собрано {amount} ссылок на видео")
        except ValueError as e:
            print(f"Ups: {e}")
    else:
        print("Please provide YouTube video links each on new line and press enter:")
        link = input()
        while link != "":
            if "youtube.com" in link:
                links.append(link.strip())
            link = input()
    return links


def menu():
    option = -1
    while option != '4' and option != "exit":
        print("Please choose options to continue\n1. Download text\n2. Download audio\n3. Download video\n4. Exit")
        option = input()

        if not option.isdigit():
            option = -1

        if int(option) == DownloadOptions.TEXT.value:
            return DownloadOptions.TEXT
        elif int(option) == DownloadOptions.AUDIO.value:
            return DownloadOptions.AUDIO
        elif int(option) == DownloadOptions.VIDEO.value:
            return DownloadOptions.VIDEO
        elif option != '4' and option != "exit":
            print("Sorry, you entered a wrong option")


def transcriber_saver(transcriber: AbstractTranscriber, save_dir: str, file_path: str) -> None:
    result = transcriber.transcribe(path=f'{save_dir}/{file_path}')
    # TODO validate file format
    file_path = file_path.replace('.mp3', '.txt')
    file_path = file_path.replace('.mp4', '.txt')
    with open(f'{save_dir}/{file_path}', "w") as file:
        file.write(result)
    print(f"Transcription saved\ntitle: {file_path}\n")


async def process_links(directory: str, links: list) -> None:
    """
    Tries to get captions by YT video link, in case of fail tries to transcribe loaded audio file to text
    :param directory: directory to save the transcribed videos
    :param links: list of links
    :return: None
    """
    tasks = []
    for link in links:
        tasks.append(get_caption_by_link(directory, link))

    print("запускаю загрузку субтритров")
    results = await asyncio.gather(*tasks, return_exceptions=True)


    tasks_to_download = []
    loader = Yt_loader(directory)
    for link, result in zip(links, results):
        if not result:
            print("создаю список путей к аудио")
            tasks_to_download.append(loader.async_download_audio(link))
    results_to_download = await asyncio.gather(*tasks_to_download, return_exceptions=True)

    print(results_to_download)

    transcriber = None
    for path, success in results_to_download:
        if success:
            if not transcriber:
                print("инициализирую transcriber")
                transcriber = FasterWhisperTranscriber(model="small", device="cpu")
            print(f"запускаю transcriber в новом потоке к файлу {directory}/{path}")
            await asyncio.get_running_loop().run_in_executor(None,
                                                             transcriber_saver,
                                                             transcriber,
                                                             directory,
                                                             path)


def main():
    directory = make_save_dir()

    chooser = input("Please choose the mode: 1 - file, 2 - youtube\n")
    if chooser == '1':
        path_to_file = input("please input path:\n")
        transcriber = WhisperTranscriber("small")
        transcriber_saver(transcriber,directory, path_to_file)
        
    elif chooser == '2':
        links = collect_links()
        if not links:
            print(">> You did not enter any link! <<")
            return
        menu_opt = menu()
        if menu_opt == DownloadOptions.TEXT:
            print("запускаю асинхронное выполнение process_links")
            asyncio.run(process_links(directory, links))
        elif menu_opt == DownloadOptions.VIDEO:
            quality = input("Enter a quality e.g. 720p: ")
            loader = Yt_loader(directory)
            for link in links:
                loader.download_video(link, quality=quality)
        elif menu_opt == DownloadOptions.AUDIO:
            loader = Yt_loader(directory)
            for link in links:
                print(loader.download_audio(link)[0])


if __name__ == "__main__":
    main()
