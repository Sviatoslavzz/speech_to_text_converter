import asyncio
import re
from pprint import pprint

from aiohttp import ClientSession
from loguru import logger

from talkushka_service.model.objects import YouTubeVideo


class YouTubeClient:
    """
    Singleton YouTube API client.
    Official YouTube API libs are used.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        logger.debug("{cls} initialized.", cls=self.__class__.__name__)

    @classmethod
    def get_instance(cls):
        return cls._instance

    async def get_channel_id_by_link(self, link: str) -> str | None:
        """
        Searches for the YouTube channel by name and returns its ID.
        :param link: YouTube channel link
        :return: channel id or None
        """
        channel_id = None

        try:
            async with ClientSession() as session:
                if "channel/" in link:
                    channel_id_ = link.split("channel/")[1]
                    url = f"{self.base_url}/channels"
                    params = {
                        "part": "id",
                        "id": channel_id_,
                        "key": self.api_key,
                    }
                elif "@" in link:
                    channel_name = link.split("@")[1]
                    url = f"{self.base_url}/search"
                    params = {
                        "part": "id",
                        "q": channel_name,
                        "type": "channel",
                        "maxResults": 1,
                        "key": self.api_key,
                    }
                else:
                    logger.warning("Unable to get channel id or name from link {link}", link=link)
                    return channel_id

                async with session.get(url, params=params) as response:
                    response_json = await response.json()
                    if not response_json.get("items"):
                        logger.warning("Unable to get channel id by link {link}", link=link)
                        return channel_id

                    if response_json["items"][0]["kind"] == "youtube#channel":
                        channel_id = response_json["items"][0]["id"]
                        logger.debug("Found a channel id: {ch_id}", ch_id=channel_id)
                    elif (
                        response_json["items"][0]["kind"] == "youtube#searchResult"
                        and response_json["items"][0]["id"]["kind"] == "youtube#channel"
                    ):
                        channel_id = response_json["items"][0]["id"]["channelId"]
                        logger.debug("Found a channel id: {ch_id}", ch_id=channel_id)
                    else:
                        logger.warning("Unable to get channel id by link {link}", link=link)

        except Exception as error:
            logger.error("Error during http connection try: {err}", err=error.__repr__())

        return channel_id

    async def get_channel_videos(self, channel_id: str) -> tuple[int, list[YouTubeVideo] | None]:
        videos = []
        amount = 0
        logger.debug("Collecting video links process started...")

        try:
            async with ClientSession() as session:
                url = f"{self.base_url}/channels"
                params = {
                    "part": "contentDetails",
                    "id": channel_id,
                    "key": self.api_key,
                }

                async with session.get(url, params=params) as response:
                    response_json = await response.json()
                    if response_json.get("items") and response_json["items"][0]["contentDetails"]:
                        playlist_id = response_json["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
                        logger.info("Got the playlist id: {playlist_id}", playlist_id=playlist_id)
                    else:
                        logger.warning("Unable to get the playlist id for channel id: {ch_id}", ch_id=channel_id)
                        return amount, None

                url = f"{self.base_url}/playlistItems"
                params = {
                    "part": "snippet",
                    "playlistId": playlist_id,
                    "maxResults": 50,
                    "key": self.api_key,
                }
                while True:
                    async with session.get(url, params=params) as response:
                        response_json = await response.json()
                        logger.debug(
                            "Processing videos from {amount}.. to total: {total}",
                            amount=amount,
                            total=response_json["pageInfo"]["totalResults"],
                        )
                        if response_json["items"] and response_json["items"][0]["snippet"]:
                            for item in response_json["items"]:
                                video = YouTubeVideo(
                                    id=item["snippet"]["resourceId"]["videoId"],
                                    kind=item["snippet"]["resourceId"]["kind"],
                                    published_at=item["snippet"]["publishedAt"],
                                    owner_username=item["snippet"]["channelTitle"],
                                    channel_id=channel_id,
                                    title=item["snippet"]["title"],
                                    link=None,
                                )
                                video.generate_link()
                                amount += 1
                                videos.append(video)
                        else:
                            logger.warning(
                                "Unable to get video #{amount} info for playlist_id: {playlist_id}",
                                amount=amount,
                                playlist_id=playlist_id,
                            )
                    next_page_token = response_json.get("nextPageToken")
                    params["pageToken"] = next_page_token
                    if not next_page_token:
                        break
        except Exception as error:
            logger.error("Error during http connection try: {err}", err=error.__repr__())
            return amount, None

        return amount, videos

    @staticmethod
    def get_video_id(link: str) -> str | None:
        """
        Search for YouTube link pattern
        :param link: YouTube link
        :return: video id
        """
        patterns = [r"v=([^&]+)", r"shorts/([^&]+)", r"live/([^&]+)", r"youtu.be/([^?]+)"]
        for pattern in patterns:
            match = re.search(pattern, link)
            if match:
                return match.group(1)

        return None

    async def get_video_by_id(self, id_: str) -> YouTubeVideo | None:
        """
        :param id_: youtube video id
        :return: YouTubeVideo instance
        """
        return await self._form_object_from_video(id_)

    async def _form_object_from_video(self, video_id: str) -> YouTubeVideo | None:
        video = None

        try:
            async with ClientSession() as session:
                url = f"{self.base_url}/videos"
                params = {
                    "part": "snippet",
                    "id": video_id,
                    "key": self.api_key,
                }
                async with session.get(url, params=params) as response:
                    response_json = await response.json()
                    pprint(response_json)  # noqa: T203
                    if response_json.get("items") and response_json["items"][0]:
                        video = YouTubeVideo(
                            id=video_id,
                            kind=response_json["items"][0]["kind"],
                            published_at=response_json["items"][0]["snippet"]["publishedAt"],
                            owner_username=response_json["items"][0]["snippet"]["channelTitle"],
                            channel_id=response_json["items"][0]["snippet"]["channelId"],
                            title=response_json["items"][0]["snippet"]["title"],
                            link=None,
                        )
                        logger.info("Found the video by id: {video_id}", video_id=video_id)
                    else:
                        logger.warning("Unable to get video by id: {video_id}", video_id=video_id)
        except Exception as error:
            logger.error("Unable to get and form video info: {err}", err=error.__repr__())

        return video

    async def get_captions(self, video_id: str) -> list[str] | None:
        captions = await self.get_all_captions_by_video_id(video_id)
        if not captions:
            return None

        for caption in captions:
            caption_id = caption["id"]
            async with ClientSession() as session:
                url = f"{self.base_url}/captions/{caption_id}"
                params = {
                    "id": caption_id,
                    "key": self.api_key,
                }
                async with session.get(url, params=params) as response:
                    response_json = await response.json()
                    pprint(response_json)  # noqa: T203

    async def get_all_captions_by_video_id(self, video_id: str) -> list[str] | None:

        try:
            async with ClientSession() as session:
                url = f"{self.base_url}/captions"
                params = {
                    "part": "snippet",
                    "videoId": video_id,
                    "key": self.api_key,
                }
                async with session.get(url, params=params) as response:
                    response_json = await response.json()
                    pprint(response_json)  # noqa: T203
                    if response_json.get("items"):
                        logger.debug("Found captions by video id: {video_id}", video_id=video_id)
                        return response_json["items"]
                    logger.warning("Unable to get captions by video id: {video_id}", video_id=video_id)
        except Exception as error:
            logger.error("Unable to get captions by video id: {err}", err=error.__repr__())
            return None


async def main():
    api_client = YouTubeClient(api_key="AIzaSyCwScs_FL7ojj7se73PFfdcdhhapQ1Ma0E")
    user_link = input("Enter the video link: ")
    video_id = api_client.get_video_id(link=user_link)
    print(video_id)
    video = await api_client.get_video_by_id(video_id)
    print(video)
    captions = await api_client.get_captions(video_id)
    print(captions)


if __name__ == "__main__":
    asyncio.run(main())
