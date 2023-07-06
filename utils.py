import re
from typing import Optional

import yt_dlp

from exceptions import YoutubeVideoMetadataError


def get_artist_and_title(video_id: str) -> tuple[Optional[str], str]:
    video_title = get_video_title(video_id)
    return parse_video_title(video_title)


cached_video_titles = {}


def get_video_title(video_id: str) -> str:
    if video_id in cached_video_titles is not None:
        return cached_video_titles[video_id]

    ydl_opts = {"quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        unsanitized_video_info = ydl.extract_info(video_id, download=False)
        video_info: dict[str, Any] = ydl.sanitize_info(unsanitized_video_info)  # type: ignore

    if video_info is None:
        raise YoutubeVideoMetadataError(
            f"could not get video info for video {video_id}"
        )
    if "title" not in video_info:
        raise YoutubeVideoMetadataError(f"could not find title for video {video_id}")

    video_title = video_info["title"]
    cached_video_titles[video_id] = video_title
    return video_title


def parse_video_title(video_title: str) -> tuple[Optional[str], str]:
    # remove junk in square brackets and certain things in parentheses
    remove_spans = []
    for square in re.finditer(r"\[.*?\]", video_title):
        remove_spans.append(square.span())
    for parens in re.finditer(r"\(.*?\)", video_title):
        lower = parens.group(0).casefold()
        for word in ("audio", "lyric", "video", "hq"):
            if word in lower:
                remove_spans.append(parens.span())
    clean_video_title = ""
    for i, (start, _) in enumerate(remove_spans):
        if i == 0:
            clean_video_title += video_title[:start]
        else:
            end = remove_spans[i - 1][1]
            clean_video_title += video_title[end:start]
    if remove_spans:
        end = remove_spans[-1][1]
        clean_video_title += video_title[end:]
    else:
        clean_video_title = video_title

    # assume video title is like "<artist> - <title>"
    components = clean_video_title.split(" - ", maxsplit=1)
    if len(components) == 1:
        artist = None
        title = components[0]
    else:
        artist, title = components

    if artist is not None:
        artist = artist.strip()
    title = title.strip()

    return artist, title


RESERVED_FILENAME_CHARS = r'<>:"/\|?*'


def make_filename(artist: Optional[str], title: str, index: int) -> str:
    if artist is None:
        new_name = f"{index} {title}.mp3"
    else:
        new_name = f"{index} {artist} - {title}.mp3"

    return sanitize_filename(new_name)


def sanitize_filename(filename: str) -> str:
    table = str.maketrans("", "", RESERVED_FILENAME_CHARS)
    return filename.translate(table)
