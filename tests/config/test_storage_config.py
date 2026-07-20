import pytest
from pydantic import ValidationError

from talkushka_service.config.models import DropboxConfig, StorageConfig
from talkushka_service.storage import DropBox


def test_dropbox_config_default():
    data = {
        "refresh_token_env": "refresh_token_env",
        "app_key_env": "app_key_env",
        "app_secret_env": "app_secret_env",
    }
    conf = DropboxConfig(**data)

    assert conf.cls is DropBox
    assert conf.storage_time == 5 * 60
    assert conf.refresh_token_env == "test_refresh_token"
    assert conf.app_key_env == "test_app_key"
    assert conf.app_secret_env == "test_app_secret"


def test_dropbox_config_manual():
    data = {
        "cls": "DropBox",
        "storage_time": 2,
        "refresh_token_env": "refresh_token_env",
        "app_key_env": "app_key_env",
        "app_secret_env": "app_secret_env",
    }
    conf = DropboxConfig(**data)

    assert conf.cls is DropBox
    assert conf.storage_time == 2
    assert conf.refresh_token_env == "test_refresh_token"
    assert conf.app_key_env == "test_app_key"
    assert conf.app_secret_env == "test_app_secret"


@pytest.mark.parametrize(
    "data",
    [
        {
            "cls": "WrongClass",
            "storage_time": 2,
            "refresh_token_env": "refresh_token_env",
            "app_key_env": "app_key_env",
            "app_secret_env": "app_secret_env",
        },
        {
            "storage_time": "abc",
            "refresh_token_env": "refresh_token_env",
            "app_key_env": "app_key_env",
            "app_secret_env": "app_secret_env",
        },
        {
            "refresh_token_env": "missing",
            "app_key_env": "app_key_env",
            "app_secret_env": "app_secret_env",
        },
        {
            "refresh_token_env": "refresh_token_env",
            "app_key_env": "missing",
            "app_secret_env": "app_secret_env",
        },
        {
            "refresh_token_env": "refresh_token_env",
            "app_key_env": "app_key_env",
            "app_secret_env": "missing",
        },
    ],
)
def test_dropbox_config_raise(data):
    with pytest.raises(ValidationError):
        DropboxConfig(**data)


@pytest.mark.parametrize(
    "data",
    [
        {
            "storages": {
                "s1": {
                    "refresh_token_env": "refresh_token_env",
                    "app_key_env": "app_key_env",
                    "app_secret_env": "app_secret_env",
                },
                "s2": {
                    "refresh_token_env": "refresh_token_env",
                    "app_key_env": "app_key_env_2",
                    "app_secret_env": "app_secret_env_2",
                },
            }
        },
        {
            "storages": {
                "s1": {
                    "refresh_token_env": "refresh_token_env",
                    "app_key_env": "app_key_env",
                    "app_secret_env": "app_secret_env",
                },
                "s2": {
                    "refresh_token_env": "refresh_token_env_2",
                    "app_key_env": "app_key_env",
                    "app_secret_env": "app_secret_env_2",
                },
            }
        },
        {
            "storages": {
                "s1": {
                    "refresh_token_env": "refresh_token_env",
                    "app_key_env": "app_key_env",
                    "app_secret_env": "app_secret_env",
                },
                "s2": {
                    "refresh_token_env": "refresh_token_env_2",
                    "app_key_env": "app_key_env_2",
                    "app_secret_env": "app_secret_env",
                },
            }
        },
    ],
)
def test_storage_config_equal_credentials(data):
    """Checks for equal credentials in case of multy Dropbox storages"""
    with pytest.raises(ValidationError):
        StorageConfig(**data)
