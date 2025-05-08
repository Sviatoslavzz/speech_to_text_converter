import asyncio
import base64
import hashlib
import secrets
from typing import Any

from aiohttp import ClientSession
from loguru import logger


class VKApiClient:
    _base_url = "https://api.vk.com/method/{api_method}?{params}&v=5.131&access_token={access_token}"

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.__access_token = ""

    @staticmethod
    def generate_code_verifier():
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b"=").decode("ascii")

        return {
            "code_verifier": code_verifier,
            "code_challenge": code_challenge,
            "state": secrets.token_urlsafe(32),
            "device_id": secrets.token_urlsafe(16),
        }

    def generate_user_auth_url(self, pkce_dict: dict) -> str:
        return (
            f"https://id.vk.com/authorize?response_type=code"
            f"&client_id={self.__client_id}"
            f"&redirect_uri=vk/callback"  # адрес куда возвращается авторизационный код
            f"&scope=video"
            f"&state={pkce_dict['state']}"
            f"&code_challenge={pkce_dict['code_challenge']}"
            f"&code_challenge_method=S256"
            f"&device_id={pkce_dict['device_id']}"
        )

    @classmethod
    def get_instance(cls):
        return cls._instance

    @staticmethod
    def extract_id_string(url: str) -> str:
        """
        Gets VK url and extracts full video id.
        :param url: only VK url
        :return: {owner_id}_{video_id} or {owner_id}_{video_id}_{access_key} or ""
        """
        ids = ""
        if index := url.find("video-"):
            index += len("video-")
            for i in range(index, len(url)):
                if url[i].isdigit() or url[i] == "_":
                    ids += url[i]
                else:
                    break

        return ids

    @staticmethod
    async def __request(url: str) -> dict[str, Any]:
        try:
            async with ClientSession() as session:
                async with session.get(url=url) as response:
                    result = await response.json()
                    if "error" in result or "response" not in result:
                        logger.error("Error while requesting VK API {err}", err=result["error"])
                    return result
        except Exception:
            logger.exception("Error while requesting VK API")
            return {"error": True}

    async def get_video_info(self, video_id: str):
        """
        :param video_id: VK video id in format {owner_id}_{video_id} or {owner_id}_{video_id}_{access_key}
        :return: response dict from VK API or None in case of error
        """
        api_method = "video.get"
        url = self._base_url.format(
            api_method=api_method,
            params=f"videos={video_id}",
            access_token=self.__access_token
        )

        print(await self.__request(url))

    async def get_user_info(self, user_id: str, fields: list[str] | None = None) -> dict[str, Any] | None:
        """
        Get information about a user.
        :param user_id: VK user id
        :param fields: list of fields to return by API
        :return: response dict from VK API or None in case of error
        """
        api_method = "users.get"
        actual_fields = f"&fields={','.join(fields)}" if fields else ""
        url = self._base_url.format(api_method=api_method,
                                    params=f"user_ids={user_id}{actual_fields}",
                                    access_token=self.__access_token)

        res = await self.__request(url)

        return None if res.get("error") else res["response"]


# 82061114_456239872 svyatoslavzz

async def run():
    client = VKApiClient()
    # asyncio.run(client.get_user_info("svyatoslavzz", fields=["bdate"]))
    id_ = client.extract_id_string(
        "https://vkvideo.ru/playlist/-192002772_18/video-192002772_456246561?isLinkedPlaylist=1")
    await client.get_video_info(id_)


def main():
    asyncio.run(run())


main()
