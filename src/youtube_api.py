from googleapiclient.discovery import build

YT_API = "AIzaSyCwScs_FL7ojj7se73PFfdcdhhapQ1Ma0E"
youtube = build("youtube", "v3", developerKey=YT_API)


def get_channel_id_by_name(link: str) -> str:
    """
    Searches a YouTube channel by name and returns its ID.
    :param link: YouTube channel link
    :return: channel id
    """
    channel_name = [i for i in link.split("/") if i.startswith("@")]

    # Search for the channel by name
    request = youtube.search().list(part="snippet", q=channel_name, type="channel", maxResults=1)
    response = request.execute()

    if not response["items"]:
        raise ValueError(f"No channel found for the name: {channel_name}")

    # Get the channel ID
    channel_id = response["items"][0]["snippet"]["channelId"]
    return channel_id  # noqa RET504


def get_channel_videos(channel_id: str) -> tuple[int, list[str]]:
    videos = []
    next_page_token = None

    print("Collecting video links process started...")

    amount = 0
    while True:
        # Fetch the playlist ID for the channel's uploads
        request = youtube.channels().list(part="contentDetails", id=channel_id)
        response = request.execute()
        playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        # Fetch the videos from the uploads playlist
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token,
        )
        response = request.execute()

        for item in response["items"]:
            video_id = item["snippet"]["resourceId"]["videoId"]
            amount += 1
            videos.append(f"https://www.youtube.com/watch?v={video_id}")

        next_page_token = response.get("nextPageToken")
        if next_page_token is None:
            break

    return amount, videos
