import dataclasses
from collections import deque
from pathlib import Path
from typing import Any, Optional

import yt_dlp

import song_actions
import utils
from exceptions import YoutubeVideoMetadataError
from mp3_metadata import CustomId3MetadataKey, Mp3Metadata
from song import Song


@dataclasses.dataclass
class Playlist:
    dir: Path
    title: Optional[str] = None
    songs: list[Song] = dataclasses.field(default_factory=list)
    video_id_to_remaining_songs: dict[str, deque[Song]] = dataclasses.field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        print("Reading local files...")

        if not self.dir.is_dir():
            self.dir.mkdir()

        for file in self.dir.iterdir():
            if not file.is_file() or file.suffix != ".mp3":
                continue
            # not a tracked file
            if (
                Mp3Metadata(file).get_custom_mp3_metadata(CustomId3MetadataKey.VIDEO_ID)
                is None
            ):
                continue

            song = Song.from_file(file)

            self.songs.append(song)

            video_id: str = song.video_id  # type: ignore # if the video id is None the song would be ignored
            if video_id in self.video_id_to_remaining_songs:
                self.video_id_to_remaining_songs[video_id].append(song)
            else:
                self.video_id_to_remaining_songs[video_id] = deque([song])

    def apply(self) -> None:
        for song in self.songs:
            song.apply()

    def render_changelist(self) -> None:
        raise NotImplementedError()

    def sync(self, playlist_id: str) -> None:
        print("Determining changes to be applied...")

        if self.dir is None:
            raise ValueError(f"cannot sync playlist: dir is None")

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            unsanitized_playlist_info = ydl.extract_info(playlist_id, download=False)
            playlist_info: dict[str, Any] = ydl.sanitize_info(unsanitized_playlist_info)  # type: ignore

        if playlist_info is None:
            raise YoutubeVideoMetadataError(
                f"could not get playlist info for playlist {playlist_id}"
            )
        if "entries" not in playlist_info:
            raise YoutubeVideoMetadataError(
                f"could not get playlist entries for playlist {playlist_id}"
            )

        for i, video in enumerate(playlist_info["entries"]):
            if "id" not in video:
                raise YoutubeVideoMetadataError(
                    f"could not find id for video in playlist {playlist_id} at index {i}: {video}"
                )
            video_id = video["id"]

            # song exists
            if (
                video_id in self.video_id_to_remaining_songs
                and len(self.video_id_to_remaining_songs[video_id]) > 0
            ):
                existing_song = self.video_id_to_remaining_songs[video_id].popleft()
                # the index is wrong though, move it to the correct position
                if existing_song.index is None or existing_song.index != i:
                    existing_song.actions.append(song_actions.UpdateIndexMetadata(i))
                    if existing_song.title is not None:
                        existing_song.actions.append(
                            song_actions.RenameFile(
                                utils.make_filename(
                                    existing_song.artist, existing_song.title, i
                                )
                            )
                        )
            # song does not exist, create it
            else:
                new_song = Song()
                artist, title = utils.get_artist_and_title(video_id)
                new_song.actions.extend(
                    [
                        song_actions.Download(
                            video_id,
                            self.dir / utils.make_filename(artist, title, i),
                        ),
                        song_actions.Normalize(),
                        song_actions.UpdateArtistMetadata(artist),
                        song_actions.UpdateTitleMetadata(title),
                        song_actions.UpdateIndexMetadata(i),
                        song_actions.UpdateVideoIdMetadata(video_id),
                    ]
                )
                self.songs.append(new_song)

        # delete songs that exist locally but not in the youtube playlist
        # ie the songs that haven't been removed from video_id_to_remaining_songs
        for remaining_songs in self.video_id_to_remaining_songs.values():
            for song in remaining_songs:
                song.actions.append(song_actions.Delete())
