from pathlib import Path

import pytest
from transcribers.faster_whisper_transcriber import FasterWhisperTranscriber

from talkushka_service.config.base import YAMLConfig
from talkushka_service.config.models import BaseConfig
from talkushka_service.objects import MINUTE
from talkushka_service.storage import DropBox


@pytest.fixture
def config_path() -> Path:
    return Path("tests/config/fixtures/talkushka.yml")


def test_config_load(config_path):
    conf: BaseConfig = YAMLConfig(model=BaseConfig, source=config_path).data

    assert conf.storage.q_size == 250
    assert conf.storage.storages.get("db1").app_secret_env == "test_app_secret"
    assert conf.storage.storages.get("db1").app_key_env == "test_app_key"
    assert conf.storage.storages.get("db1").refresh_token_env == "test_refresh_token"
    assert conf.storage.storages.get("db1").cls == DropBox
    assert conf.storage.storages.get("db1").storage_time == 5 * MINUTE
    assert conf.storage.storages.get("db2").app_secret_env == "test_app_secret_2"
    assert conf.storage.storages.get("db2").app_key_env == "test_app_key_2"
    assert conf.storage.storages.get("db2").refresh_token_env == "test_refresh_token_2"
    assert conf.storage.storages.get("db2").cls == DropBox
    assert conf.storage.storages.get("db2").storage_time == 5 * MINUTE

    assert conf.bot.server == "local"
    assert conf.bot.host == "localhost"
    assert conf.bot.port == 1234
    assert conf.bot.token_env == "test_token"

    assert conf.youtube.api_key_env == "test_api_key"
    assert conf.youtube.heavy_pool_size == 5
    assert conf.youtube.light_pool_size == 10
    assert conf.youtube.save_dir.name == "saved_files"
    assert conf.youtube.proxies == ["http://1.1.1.1:1234", "http://1.1.1.2:4321"]

    assert conf.transcriber.q_size == 200
    assert conf.transcriber.cls == FasterWhisperTranscriber
    assert conf.transcriber.model == "small"
