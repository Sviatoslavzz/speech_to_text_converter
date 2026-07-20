import asyncio

from talkushka_service.model.objects import DownloadTask
from talkushka_service.utils.functions import get_project_root
from talkushka_service.youtube_clients.youtube_api import YouTubeClient
from talkushka_service.youtube_clients.youtube_loader import YouTubeLoader


async def start():
    link = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    api = YouTubeClient("AIzaSyCwScs_FL7ojj7se73PFfdcdhhapQ1Ma0E")
    video = await api.get_video_by_id(api.get_video_id(link))
    if not video:
        print("Video not found")
        return

    task = DownloadTask(id=video.id, video=video)

    loader = YouTubeLoader(get_project_root() / "saved_files", 20, 40)
    options = await loader.get_video_options(link)

    task = await loader.download_video(task)
    print(task)

    print(options)


def main():
    asyncio.run(start())


if __name__ == "__main__":
    main()
