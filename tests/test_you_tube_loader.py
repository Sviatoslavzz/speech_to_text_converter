import pytest


@pytest.mark.asyncio
async def test_title_preparation(youtube_loader, youtube_api_client, youtube_videos):
    for link in youtube_videos:
        video = await youtube_api_client.form_video_from_link(link)
        title = youtube_loader.prepare_title(video.title)
        for letter in title:
            assert letter.isalpha() or letter == "_"


@pytest.mark.asyncio
async def test_download_audio(youtube_loader, youtube_api_client, youtube_videos):
    for link in youtube_videos:
        video = await youtube_api_client.form_video_from_link(link)
        youtube_loader.download_audio(video)
        break