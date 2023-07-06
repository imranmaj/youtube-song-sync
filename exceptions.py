from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from song_actions import SongAction


class ActionError(Exception):
    def __init__(self, action: "SongAction", message: str) -> None:
        super().__init__(f"cannot perform action {type(action).__name__}: {message}")


class Mp3MetadataError(Exception):
    pass

class YoutubeVideoMetadataError(Exception):
    pass
