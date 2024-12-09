from storage.dropbox_storage import DropBox
from transcribers.abscract_transcriber import AbstractTranscriber
from transcribers.faster_whisper_transcriber import FasterWhisperTranscriber
from transcribers.whisper_transcriber import WhisperTranscriber


def get_transcriber_cls(cls: str) -> type[AbstractTranscriber]:
    mapping = {
        "WhisperTranscriber": WhisperTranscriber,
        "FasterWhisperTranscriber": FasterWhisperTranscriber,
    }
    if cls not in mapping:
        raise AssertionError(f"Unknown transcriber class {cls}")

    return mapping[cls]


def get_storage_cls(cls: str) -> type[DropBox]:
    # TODO abstract storage
    mapping = {
        "DropBox": DropBox,
    }
    if cls not in mapping:
        raise AssertionError(f"Unknown storage class {cls}")

    return mapping[cls]
