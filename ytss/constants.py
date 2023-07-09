from enum import Enum

RESERVED_FILENAME_CHARS = r'<>:"/\|?*'
NORMALIZATION = -20
DEFAULT_YOUTUBE_DL_OPTS = {
    "quiet": True,
    "no_warnings": True,
}


class CustomId3MetadataKey(Enum):
    VIDEO_ID = "YoutubeSongSync_video_id"
    INDEX = "YoutubeSongSync_index"
