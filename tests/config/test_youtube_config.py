import pytest
from pydantic import ValidationError

from talkushka_service.config.models import YouTubeConfig


def test_youtube_config_default():
    data = {
        "api_key_env": "api_key_env"
    }
    conf = YouTubeConfig(**data)

    assert conf.api_key_env == "test_api_key"
    assert conf.heavy_pool_size == 20
    assert conf.light_pool_size == 40
    assert conf.save_dir.name == "saved_files"
    assert not conf.proxies


def test_youtube_config():
    data = {
        "api_key_env": "api_key_env",
        "heavy_pool_size": 25,
        "light_pool_size": 45,
        "save_dir": "tmp",
        "proxies": ["http://proxy.com"],
    }
    conf = YouTubeConfig(**data)
    assert conf.api_key_env == "test_api_key"
    assert conf.heavy_pool_size == 25
    assert conf.light_pool_size == 45
    assert conf.save_dir.name == "tmp"
    assert conf.proxies[0] == "http://proxy.com"

    conf.save_dir.rmdir()


def test_youtube_config_raise():
    data = {
        "heavy_pool_size": 12,
    }
    with pytest.raises(ValidationError):
        YouTubeConfig(**data)
