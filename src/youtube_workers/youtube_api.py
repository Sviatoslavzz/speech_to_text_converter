import re

from aiohttp import ClientSession
from loguru import logger

from objects import YouTubeVideo


class YouTubeClient:
    """
    Singleton YouTube API client.
    Using official YouTube API libs.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

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

        async with ClientSession() as session:
            if "channel/" in link:
                channel_id = link.split("channel/")[1]
                url = f"{self.base_url}/channels"
                params = {
                    "part": "id",
                    "id": channel_id,
                    "key": self.api_key,
                }
                try:
                    async with session.get(url, params=params) as response:
                        response_json = await response.json()
                        if not (response_json.get("items") and response_json["items"][0]["kind"] == "youtube#channel"):
                            logger.warning(f"Unable to get channel id from link {link}")
                            channel_id = None
                        else:
                            logger.info(f"Found a channel id: {channel_id}")
                except Exception as error:
                    logger.error(f"Error during http connection try: {error}")
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
                try:
                    async with session.get(url, params=params) as response:
                        response_json = await response.json()
                        if response_json.get("items") and response_json["items"][0]["id"]["kind"] == "youtube#channel":
                            channel_id = response_json["items"][0]["id"]["channelId"]
                            logger.info(f"Found a channel id: {channel_id}")
                        else:
                            logger.warning(f"Unable to get channel id from link {link}")
                except Exception as error:
                    logger.error(f"Error during http connection try: {error}")
            else:
                logger.warning(f"Unable to get channel id from link {link}")

        return channel_id

    async def get_channel_videos(self, channel_id: str) -> tuple[int, list[YouTubeVideo] | None]:
        videos = []
        amount = 0
        logger.info("Collecting video links process started...")

        async with ClientSession() as session:
            url = f"{self.base_url}/channels"
            params = {
                "part": "contentDetails",
                "id": channel_id,
                "key": self.api_key,
            }
            try:
                async with session.get(url, params=params) as response:
                    response_json = await response.json()
                    if response_json.get("items") and response_json["items"][0]["contentDetails"]:
                        playlist_id = response_json["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
                        logger.info(f"Got the playlist id: {playlist_id}")
                    else:
                        logger.warning(f"Unable to get the playlist id for channel id: {channel_id}")
                        return amount, None
            except Exception as error:
                logger.error(f"Error during http connection try: {error}")
                return amount, None

            url = f"{self.base_url}/playlistItems"
            params = {
                "part": "snippet",
                "playlistId": playlist_id,
                "maxResults": 50,
                "key": self.api_key,
            }
            while True:
                try:
                    async with session.get(url, params=params) as response:
                        response_json = await response.json()
                        logger.info(
                            f"Processing videos from {amount}.. to total: {response_json['pageInfo']['totalResults']}"
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
                            logger.warning(f"Unable to get video #{amount} info for playlist_id: {playlist_id}")
                except Exception as error:
                    logger.error(f"Error during http connection try: {error}")
                next_page_token = response_json.get("nextPageToken")
                params["pageToken"] = next_page_token
                if not next_page_token:
                    break

        return amount, videos

    async def get_video_by_link(self, link: str) -> YouTubeVideo | None:
        patterns = [r"v=([^&]+)", r"shorts/([^&]+)", r"live/([^&]+)"]
        video_obj = None
        for pattern in patterns:
            match = re.search(pattern, link)
            if match:
                video_id = match.group(1)
                video_obj = await self._form_object_from_video(video_id)
                break

        if not video_obj:
            logger.warning(f"Unable to get video id from link {link}")

        return video_obj

    async def _form_object_from_video(self, video_id: str) -> YouTubeVideo | None:
        video = None

        async with ClientSession() as session:
            url = f"{self.base_url}/videos"
            params = {
                "part": "snippet",
                "id": video_id,
                "key": self.api_key,
            }
            try:
                async with session.get(url, params=params) as response:
                    response_json = await response.json()
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
                        video.generate_link()
                        logger.info(f"Got the video by id: {video_id}")
                    else:
                        logger.warning(f"Unable to get video by id: {video_id}")
            except Exception as error:
                logger.error(f"Error during http connection try: {error}")

        return video
