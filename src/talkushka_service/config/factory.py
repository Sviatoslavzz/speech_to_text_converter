from talkushka_service.storage.dropbox_storage import DropBox


def get_storage_cls(cls: str) -> type[DropBox]:
    # TODO abstract storage
    mapping = {
        "DropBox": DropBox,
    }
    if cls not in mapping:
        raise AssertionError(f"Unknown storage class {cls}")

    return mapping[cls]
