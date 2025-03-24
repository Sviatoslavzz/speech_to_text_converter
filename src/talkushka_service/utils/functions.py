import importlib.metadata as im
import subprocess
from pathlib import Path
from uuid import uuid4

from dateutil.relativedelta import relativedelta
from loguru import logger

from talkushka_service.config.settings import settings
from talkushka_service.db.model import SubscriptionType
from talkushka_service.storage.dropbox_storage import DropBox


def get_package_name() -> str:
    # pyproject_f = Path(__file__).parent.parent.parent / "pyproject.toml"  # TODO resolve path
    # name = ""
    # try:
    #     if not pyproject_f.is_file():
    #         raise FileNotFoundError(f"{pyproject_f} does not exist.")
    #
    #     with pyproject_f.open(mode="rb") as f:
    #         pyproject = tomllib.load(f)
    #     name = pyproject["project"]["name"]
    # except Exception as e:
    #     logger.error(f"Failed to get package name: {e}")
    #
    # return name
    return "talkushka_service"


def get_version() -> str:
    package_name = get_package_name()
    version = ""
    try:
        version = im.version(package_name)
    except im.PackageNotFoundError:
        logger.error(f"Version not found for package {package_name}")
    except Exception as e:
        logger.error(f"Failed to get package version: {e.__repr__()}")

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


def get_project_root() -> Path:
    path_ = Path(__file__).parent

    while path_.name != settings.PROJECT_NAME:
        if path_.__fspath__() == path_.anchor:
            return path_ / settings.PROJECT_NAME
        path_ = path_.parent

    return path_.parent / settings.PROJECT_NAME


def create_saving_dir(dir_: str) -> Path:
    absolute_path = get_project_root()
    dir_ = absolute_path / dir_
    if not dir_.is_dir():
        dir_.mkdir()
        logger.info(f"Saving directory created: {dir_}")
    logger.info(f"Saving directory set up: {dir_}")
    return dir_


def convert_to_m4a(path_: Path) -> tuple[bool, Path]:
    """
    Converts any audio/video file to audio .m4a aac format using ffmpeg
    """
    if path_.suffix == ".m4a":
        return True, path_

    new_path = path_.with_suffix(".m4a")
    command = ["ffmpeg", "-i", path_, "-vn", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k", new_path]

    try:
        subprocess.run(command, check=True)  # noqa S603
        result = True
        logger.info("File successfully converted to m4a")
    except subprocess.CalledProcessError as e:
        result = False
        logger.error("Failed to convert to m4a: {err}", err=e.__repr__())

    return result, new_path


def relative_delta_by_s_type(s_type: SubscriptionType) -> relativedelta:
    """
    :return: relativedelta for provided SubscriptionType
    """
    if s_type == SubscriptionType.week:
        return relativedelta(days=7)
    if s_type == SubscriptionType.month:
        return relativedelta(month=1)
    if s_type == SubscriptionType.year:
        return relativedelta(year=1)
    logger.error(f"error getting relativedelta : Unsupported SubscriptionType: {s_type}")
    raise AssertionError("Unsupported SubscriptionType")

def generate_promocode() -> str:
    return str(uuid4())
