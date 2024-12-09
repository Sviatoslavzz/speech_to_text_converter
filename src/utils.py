import importlib.metadata as im
import tomllib
from pathlib import Path

from loguru import logger

from storage.dropbox_storage import DropBox


def get_package_name() -> str:
    pyproject_f = Path(__file__).parent.parent / "pyproject.toml"
    name = ""
    try:
        if not pyproject_f.is_file():
            raise FileNotFoundError(f"{pyproject_f} does not exist.")

        with pyproject_f.open(mode="rb") as f:
            pyproject = tomllib.load(f)
        name = pyproject["project"]["name"]
    except Exception as e:
        logger.error(f"Failed to get package name: {e}")

    return name


def get_version() -> str:
    package_name = get_package_name()
    version = ""
    try:
        version = im.version(package_name)
    except im.PackageNotFoundError:
        logger.error(f"Version not found for package {package_name}")

    return version


def validate_db_storages(storages: list):
    """Verifies the uniqueness of DropBox credentials"""
    db_storages = list(filter(lambda x: x.cls is DropBox, storages))
    n_unique = len(db_storages)
    if n_unique != len({x.refresh_token_env for x in db_storages}):
        raise AssertionError("Refresh tokens must be unique for each DropBox storage")
    if n_unique != len({x.app_key_env for x in db_storages}):
        raise AssertionError("App keys must be unique for each DropBox storage")
    if n_unique != len({x.app_secret_env for x in db_storages}):
        raise AssertionError("App secrets must be unique for each DropBox storage")


def create_saving_dir(dir_: str) -> Path:
    absolute_path = Path(__file__).absolute().parent.parent.parent
    dir_ = Path(f"{absolute_path}/{dir_}")
    if not dir_.is_dir():
        dir_.mkdir()
        logger.info(f"Saving directory created: {dir_}")
    logger.info(f"Saving directory set up: {dir_}")
    return dir_
