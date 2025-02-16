import pytest
from pydantic import ValidationError

from talkushka_service.config.models import BotConfig


def test_bot_config_default():
    data = {
        "token_env": "token_env"
    }
    conf = BotConfig(**data)
    assert conf.server == "telegram"
    assert not conf.host
    assert not conf.port
    assert conf.token_env == "test_token"


def test_bot_config():
    data = {
        "server": "local",
        "host": "127.0.0.1",
        "port": 1234,
        "token_env": "token_env",
    }
    conf = BotConfig(**data)
    assert conf.server == "local"
    assert conf.host == "127.0.0.1"
    assert conf.port == 1234
    assert conf.token_env == "test_token"


@pytest.mark.parametrize(
    "data", [
        {
            "server": "local",
            "host": "127.0.0.1",
            "token_env": "token_env",
        },
        {
            "server": "local",
            "port": 1234,
            "token_env": "token_env",
        },
        {
            "server": "telegram",
        }
    ]
)
def test_bot_config_raise(data):
    with pytest.raises(ValidationError):
        BotConfig(**data)
