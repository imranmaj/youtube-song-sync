import re
from typing import Any, Optional

import yt_dlp

from ytss.constants import DEFAULT_YOUTUBE_DL_OPTS, RESERVED_FILENAME_CHARS
from ytss.exceptions import YoutubeVideoMetadataError


def get_artist_and_title(
    video_id: str, video_info: Optional[dict[str, Any]] = None
) -> tuple[Optional[str], str]:
    video_title = get_video_title(video_id, existing_video_info=video_info)
    return parse_video_title(video_title)


cached_video_titles = {}


def get_video_title(
    video_id: str, existing_video_info: Optional[dict[str, Any]] = None
) -> str:
    if video_id in cached_video_titles is not None:
        return cached_video_titles[video_id]

    if existing_video_info is not None and "title" in existing_video_info:
        video_title = existing_video_info["title"]
    else:
        video_info = get_info(video_id)
        if "title" not in video_info:
            raise YoutubeVideoMetadataError.info_missing_key(
                video_id, "title", video_info
            )

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


def make_filename(artist: Optional[str], title: str, index: int) -> str:
    if artist is None:
        new_name = f"{index} {title}.mp3"
    else:
        new_name = f"{index} {artist} - {title}.mp3"

    return sanitize_filename(new_name)


def sanitize_filename(filename: str) -> str:
    table = str.maketrans("", "", RESERVED_FILENAME_CHARS)
    return filename.translate(table)


def get_confirmation() -> None:
    print("Please read the above carefully before continuing.")
    print("The above changes will be applied if you choose to continue.")
    response = input(
        'If you like to continue, type "yes" (only "yes" will be accepted to continue): '
    )
    if response != "yes":
        print("Aborting.")
        raise SystemExit()
    print()


def get_info(
    playlist_or_video_url_or_id: str, ignore_errors: bool = False, resolve: bool = True
) -> dict[str, Any]:
    """
    ignore_errors: don't stop on an error, e.g. when a video is unavailable when getting info for a playlist
    resolve: resolve all references, e.g. calculate entries in playlist info (this can be slow)
    """

    ydl_opts = {
        **DEFAULT_YOUTUBE_DL_OPTS,
        "ignoreerrors": ignore_errors,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        unsanitized_info = ydl.extract_info(
            playlist_or_video_url_or_id, download=False, process=resolve
        )
        info: Optional[dict[str, Any]] = ydl.sanitize_info(unsanitized_info)  # type: ignore

    if info is None:
        raise YoutubeVideoMetadataError(f"no info for {playlist_or_video_url_or_id}")

    return info


def get_playlist_or_video_id(playlist_or_video_url_or_id: str) -> str:
    info = get_info(playlist_or_video_url_or_id, resolve=False)

    if "id" not in info:
        raise YoutubeVideoMetadataError.info_missing_key(
            playlist_or_video_url_or_id, "id", info
        )

    return info["id"]
