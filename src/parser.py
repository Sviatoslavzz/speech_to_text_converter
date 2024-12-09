import argparse
from pathlib import Path

from loguru import logger

from config.base import ConfigModelType, YAMLConfig
from config.conf_models import BaseConfig
from utils import get_version


class ConfigModelFileType:
    def __init__(
            self,
            model: type[ConfigModelType],
            config_class: type[YAMLConfig],
            allow_empty: bool = False,
    ):
        self._model = model
        self._config_class = config_class
        self._allow_empty = allow_empty

    def __call__(self, source: str) -> YAMLConfig:
        source_path = Path(source)
        if not source_path.exists() and not self._allow_empty:
                raise argparse.ArgumentTypeError(f'No such file or directory: "{source}"')

        try:
            return self._config_class(self._model, source_path)
        except Exception as e:
            logger.error(f"Exception while parsing config file: {e}")
            raise


def get_base_parser():
    parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=argparse.HelpFormatter
    )
    help_group = parser.add_argument_group(title="Help")
    help_group.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="help",
    )
    help_group.add_argument(
        "--version",
        action="version",
        version=get_version(),
        help="show installed service version",
    )

    return parser


def get_parser(parser_: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    if not parser_:
        parser_ = get_base_parser()

    service_group = parser_.add_argument_group(title="Service options")

    service_group.add_argument(
        "-c",
        dest="config",
        type=ConfigModelFileType(
            BaseConfig,
            YAMLConfig,
            allow_empty=False,
        ),
        help="path to configuration file.yml",
        default="conf/base.yml"
    )

    return parser_
