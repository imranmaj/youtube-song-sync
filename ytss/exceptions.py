from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ytss.song_actions import SongAction


class ActionError(Exception):
    def __init__(self, action: "SongAction", message: str) -> None:
        super().__init__(f"cannot perform action {type(action).__name__}: {message}")


class Mp3MetadataError(Exception):
    pass


class YoutubeVideoMetadataError(Exception):
    @staticmethod
    def info_missing_key(
        playlist_or_video_url_or_id: str, key: str, info: dict[str, Any]
    ) -> "YoutubeVideoMetadataError":
        return YoutubeVideoMetadataError(
            f'info for "{playlist_or_video_url_or_id}" missing key "{key}" (actual keys: {list(info.keys())})'
        )
