import dataclasses
from collections import deque
from pathlib import Path
from typing import Iterable, Optional

from ytss import song_actions, utils
from ytss.actionable import Actionable
from ytss.constants import CustomId3MetadataKey
from ytss.exceptions import YoutubeVideoMetadataError
from ytss.mp3_metadata import Mp3Metadata
from ytss.song import Song


@dataclasses.dataclass
class Playlist(Actionable):
    dir: Path
    title: Optional[str] = None
    songs: list[Song] = dataclasses.field(default_factory=list)
    video_id_to_remaining_songs: dict[str, deque[Song]] = dataclasses.field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        print("Reading local files...")

        if self.dir.exists() and not self.dir.is_dir():
            raise FileNotFoundError(f"path {self.dir} exists but is not a directory")

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

    def iter_songs(self) -> Iterable[Song]:
        return iter(self.songs)

    def render_changelist(self) -> None:
        if self.title is not None:
            print(
                f'Planning to sync the local directory {self.dir} with YouTube playlist "{self.title}"'
            )

        super().render_changelist()

    def sync(
        self, playlist_id: str, delete_allowed: bool, rename_allowed: bool
    ) -> None:
        if self.dir is None:
            raise ValueError(f"cannot sync playlist: dir is None")

        print("Downloading playlist metadata...")
        playlist_info = utils.get_info(playlist_id, ignore_errors=True)

        if "title" in playlist_info and playlist_info["title"] is not None:
            self.title = playlist_info["title"]

        if "entries" not in playlist_info:
            raise YoutubeVideoMetadataError.info_missing_key(
                "playlist_id", "entries", playlist_info
            )

        print("Determining changes to be applied...")
        for i, video_info in enumerate(playlist_info["entries"]):
            # skip unavailable/private videos
            if video_info is None:
                continue

            if "id" not in video_info:
                raise YoutubeVideoMetadataError(
                    f"no id for video in playlist {playlist_id} at index {i}: {video_info}"
                )
            video_id = video_info["id"]

            # song exists
            if (
                video_id in self.video_id_to_remaining_songs
                and len(self.video_id_to_remaining_songs[video_id]) > 0
            ):
                existing_song = self.video_id_to_remaining_songs[video_id].popleft()
                # the index is wrong though, move it to the correct position
                if existing_song.index is None or existing_song.index != i:
                    existing_song.actions.append(song_actions.UpdateIndexMetadata(i))
                    # rename the file to reflect the new index
                    if rename_allowed and existing_song.title is not None:
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
                artist, title = utils.get_artist_and_title(video_id, video_info)
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
        # (songs that will be in the final playlist were removed while iterating over the
        # Youtube playlist)
        if delete_allowed:
            for remaining_songs in self.video_id_to_remaining_songs.values():
                for song in remaining_songs:
                    song.actions.append(song_actions.Delete())
