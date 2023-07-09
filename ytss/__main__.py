from pathlib import Path

import click

from ytss import song_actions, utils
from ytss.playlist import Playlist


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
    are "tracked" and only these files will be deleted or renamed.

    \b
    Author: Imran Majeed
    Project homepage: https://github.com/imranmaj/youtube-song-sync
    """

    pass


@click.command()
@click.argument("playlist_url", type=click.STRING)
@click.argument("output_directory", type=click.Path(path_type=Path))
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
def sync(
    playlist_url: str, output_directory: Path, no_delete: bool, no_rename: bool
) -> None:
    """
    Syncs a YouTube playlist to a local directory.

    The playlist at PLAYLIST_URL will be synced to the path OUTPUT_DIRECTORY.
    If the output directory does not exist, an attempt will be made to create it.

    A confirmation screen for changes to apply to the local directory will
    appear before any changes are made.

    Local changes to the directory are not applied to the remote YouTube playlist.
    Only changes to the YouTube playlist will be applied to the local directory.

    Only "tracked" songs are affected. If a song was not downloaded by YTSS,
    then by default it is not tracked.

    The following changes will be made to the local directory:
    - If any songs exist in the YouTube playlist that do not exist locally,
    those songs will be downloaded.
    - If any songs exist locally that do not exist in the YouTube playlist, they will be deleted.
    - If the order of any songs is changed in the YouTube playlist, the files will be renamed locally.
    - Audio levels of all downloaded songs are normalized so the volume is consistent.
    - MP3 metadata is updated for any songs that are affected.
    """

    playlist = Playlist(output_directory)
    playlist_id = utils.get_playlist_or_video_id(playlist_url)
    playlist.sync(
        playlist_id,
        delete_allowed=not no_delete,
        rename_allowed=not no_rename,
    )
    playlist.render_changelist()
    if playlist.has_any_song_action(song_actions.SongAction):
        utils.get_confirmation()
        playlist.apply()


cli.add_command(sync)

cli()
