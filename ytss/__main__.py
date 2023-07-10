from pathlib import Path
from typing import Optional

import click

from ytss import utils
from ytss.playlist import Playlist
from ytss.song import Song


@click.group()
def cli() -> None:
    """
    YouTube Song Sync

    Syncs songs on YouTube to your computer. Videos are downloaded and converted to audio.

    "sync" is the main command; it will sync and download songs from a YouTube playlist.

    Entire YouTube playlists can be synced/downloaded.
    If you would like for the playlist to remain private, it is recommended
    that you set the visibility on the playlist to "unlisted."

    By default YTSS does not affect existing audio files. Files that are downloaded by YTSS
    are "tracked" automatically and only tracked files will be deleted or renamed.
    To track an existing file, use the "track" command.

    \b
    Author: Imran Majeed
    Project homepage: https://github.com/imranmaj/youtube-song-sync
    """

    pass


@click.command()
@click.argument("playlist_url", type=click.STRING)
@click.argument("playlist_directory", type=click.Path(path_type=Path))
@click.option(
    "--no-delete",
    type=click.BOOL,
    is_flag=True,
    default=False,
    show_default=True,
    help="Do not delete local files",
)
@click.option(
    "--no-rename",
    type=click.BOOL,
    is_flag=True,
    default=False,
    show_default=True,
    help="Do not rename local files",
)
@click.option(
    "--no-normalize",
    type=click.BOOL,
    is_flag=True,
    default=False,
    show_default=True,
    help="Do not normalize audio levels",
)
def sync(
    playlist_url: str,
    playlist_directory: Path,
    no_delete: bool,
    no_rename: bool,
    no_normalize: bool,
) -> None:
    """
    Syncs a YouTube playlist to a local directory.

    The playlist at PLAYLIST_URL will be synced to the path PLAYLIST_DIRECTORY.
    If the playlist directory does not exist, an attempt will be made to create it.

    A confirmation screen for changes to apply to the local directory will
    appear before any changes are made.

    Local changes to the directory are not applied to the remote YouTube playlist.
    Only changes to the YouTube playlist will be applied to the local directory.

    Only "tracked" songs are affected.
    If a song was not downloaded by YTSS, then by default it is not tracked.
    MP3 files can be tracked by using the track command to add video ID metadata.

    \b
    The following changes will be made to the local directory:
    - If any songs exist in the YouTube playlist that do not exist locally, those songs will be downloaded.
    - If any songs exist locally that do not exist in the YouTube playlist, they will be deleted.
    - If the order of any songs is changed in the YouTube playlist, the files will be renamed locally.
    - Audio levels of all downloaded songs are normalized so the volume is consistent.
    - MP3 metadata is updated for any songs that are affected.
    """

    playlist = Playlist(playlist_directory)
    playlist_id = utils.get_playlist_or_video_id(playlist_url)
    playlist.sync(
        playlist_id,
        delete_allowed=not no_delete,
        rename_allowed=not no_rename,
        normalize_allowed=not no_normalize,
    )
    playlist.confirm_and_apply()


@click.command(name="update-metadata")
@click.argument("file", type=click.Path(path_type=Path))
@click.option(
    "--title", "new_title", type=click.STRING, help="The new title of the song"
)
@click.option(
    "--artist", "new_artist", type=click.STRING, help="The new artist of the song"
)
@click.option(
    "--video-id", "new_video_id", type=click.STRING, help="The new video ID of the song"
)
@click.option(
    "--index", "new_index", type=click.INT, help="The new index/position of the song"
)
@click.option(
    "--no-rename",
    type=click.BOOL,
    is_flag=True,
    default=False,
    show_default=True,
    help="Do not rename local files",
)
def update_metadata(
    file: Path,
    new_title: Optional[str],
    new_artist: Optional[str],
    new_video_id: Optional[str],
    new_index: Optional[int],
    no_rename: bool,
) -> None:
    """
    Updates the MP3 metadata for a file and renames it.
    """

    song = Song.from_file(file)
    song.update_metadata(
        new_title,
        new_artist,
        new_video_id,
        new_index,
        rename_allowed=not no_rename,
    )
    song.confirm_and_apply()


@click.command()
@click.argument("file", type=click.Path(path_type=Path))
@click.argument("video_url_or_id", type=click.STRING)
def track(file: Path, video_url_or_id: str) -> None:
    """
    Tracks a file so that it can by used with "sync."

    The MP3 file at FILE will be tracked with the YouTube video specified by VIDEO_URL_OR_ID.
    VIDEO_URL_OR_ID can be a YouTube video URL or just the ID.

    The sync commmand does not modify files that are not tracked.
    To allow the sync command to update audio files that are not tracked,
    track them with this command.

    YTSS tracks files using video ID metadata.
    Files that are downloaded by YTSS are automatically tracked,
    but files that are not downloaded by YTSS are not tracked by default.
    """

    song = Song.from_file(file)
    video_id = utils.get_playlist_or_video_id(video_url_or_id)
    song.track(video_id)
    song.confirm_and_apply()


@click.command(name="list")
@click.argument("playlist_directory", type=click.Path(path_type=Path))
def list_tracked(playlist_directory: Path) -> None:
    """
    Lists the tracked files in a playlist directory.

    For more information about tracked files,
    see the documentation for the "track" command.
    """

    playlist = Playlist(playlist_directory)
    playlist.list_songs()


@click.command()
@click.argument("video_url", type=click.STRING)
@click.argument("playlist_directory", type=click.Path(path_type=Path))
@click.option(
    "--no-normalize",
    type=click.BOOL,
    is_flag=True,
    default=False,
    show_default=True,
    help="Do not normalize audio levels",
)
def download_song(video_url: str, playlist_directory: Path, no_normalize: bool) -> None:
    """
    Downloads a single song.

    The song at VIDEO_URL will be downloaded to the folder at PLAYLIST_DIRECTORY.
    If the playlist directory does not exist, an attempt will be made to create it.
    """

    song = Song()
    video_id = utils.get_playlist_or_video_id(video_url)
    song.download(video_id, playlist_directory, normalize_allowed=not no_normalize)
    song.confirm_and_apply()


cli.add_command(sync)
cli.add_command(update_metadata)
cli.add_command(track)
cli.add_command(list_tracked)
cli.add_command(download_song)

cli()
