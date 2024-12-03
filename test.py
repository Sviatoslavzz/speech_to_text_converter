from pathlib import Path

from src.config.base import YAMLConfig
from src.config.conf_models import BaseConfig


conf = YAMLConfig(BaseConfig, Path("conf/base.yml"))

print(conf.data.bot)