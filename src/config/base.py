from pathlib import Path
from typing import TypeVar

import yaml

from config.models import BaseConfig

ConfigModelType = TypeVar("ConfigModelType", bound=BaseConfig)


class YAMLConfig:
    ENCODING = "utf-8"

    def __init__(self, model: type[ConfigModelType], source: Path, blank: bool = False):
        self._model = model
        self._source = source
        self._data = None

        if not blank:
            self.read()

    def read(self):
        with self._source.open(encoding=self.ENCODING) as f:
            data = yaml.safe_load(f.read())
        self._data = self._model(**data)

    @property
    def data(self):
        return self._data
