import dataclasses
from collections import deque
from pathlib import Path
from typing import Any, Iterable, Optional, Type, TypeVar

from prettytable import ALL, SINGLE_BORDER, PrettyTable

from ytss import song_actions, utils
from ytss.constants import CustomId3MetadataKey
from ytss.exceptions import YoutubeVideoMetadataError
from ytss.mp3_metadata import Mp3Metadata
from ytss.song import Song


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
        print()

        if not self.has_any_song_action(song_actions.SongAction):
            print("No changes to be applied!")
            return

        if self.title is not None:
            print(f'Planning to sync with YouTube playlist "{self.title}"')

        print(
            f"The following changes will be applied to the local playlist at {str(self.dir)}:",
            "\n",
        )

        # downloads
        if self.has_any_song_action(song_actions.Download):
            print("The following songs will be downloaded:")
            downloads_table = self.make_table(
                ["Filename", "Title", "Artist", "Video ID", "Index"]
            )
            for song, action in self.get_songs_with_action(song_actions.Download):
                downloads_table.add_row(
                    self.clean_table_row(
                        [
                            action.output_file.name,
                            song.get_future_title(),
                            song.get_future_artist(),
                            song.get_future_video_id(),
                            song.get_future_index(),
                        ]
                    )
                )
            print(downloads_table, "\n")

        # normalization
        if self.has_any_song_action(song_actions.Normalize):
            print("The following songs will have their audio levels normalized:")
            normalized_table = self.make_table(["Title", "Artist", "Index"])
            for song, action in self.get_songs_with_action(song_actions.Normalize):
                normalized_table.add_row(
                    self.clean_table_row(
                        [
                            song.get_future_title(),
                            song.get_future_artist(),
                            song.get_future_index(),
                        ]
                    )
                )
            print(normalized_table, "\n")

        # video id metadata
        if self.has_any_song_action(song_actions.UpdateVideoIdMetadata):
            print("The following songs will have their video ID metadata updated:")
            video_id_table = self.make_table(
                ["Title", "Artist", "Index", "Old Video ID", "New Video ID"]
            )
            for song, _ in self.get_songs_with_action(
                song_actions.UpdateVideoIdMetadata
            ):
                video_id_table.add_row(
                    self.clean_table_row(
                        [
                            song.get_future_title(),
                            song.get_future_artist(),
                            song.get_future_index(),
                            song.video_id,
                            song.get_future_video_id(),
                        ]
                    )
                )
            print(video_id_table, "\n")

        # index metadata
        if self.has_any_song_action(song_actions.UpdateIndexMetadata):
            print("The following songs will have their index metadata updated:")
            index_table = self.make_table(["Title", "Artist", "Old Index", "New Index"])
            for song, _ in self.get_songs_with_action(song_actions.UpdateIndexMetadata):
                index_table.add_row(
                    self.clean_table_row(
                        [
                            song.get_future_title(),
                            song.get_future_artist(),
                            song.index,
                            song.get_future_index(),
                        ]
                    )
                )
            print(index_table, "\n")

        # title metadata
        if self.has_any_song_action(song_actions.UpdateTitleMetadata):
            print("The following songs will have their title metadata updated:")
            title_table = self.make_table(["Artist", "Index", "Old Title", "New Title"])
            for song, _ in self.get_songs_with_action(song_actions.UpdateTitleMetadata):
                title_table.add_row(
                    self.clean_table_row(
                        [
                            song.get_future_artist(),
                            song.get_future_index(),
                            song.title,
                            song.get_future_title(),
                        ]
                    )
                )
            print(title_table, "\n")

        # artist metadata
        if self.has_any_song_action(song_actions.UpdateArtistMetadata):
            print("The following songs will have their artist metadata updated:")
            artist_table = self.make_table(
                ["Title", "Index", "Old Artist", "New Artist"]
            )
            for song, _ in self.get_songs_with_action(
                song_actions.UpdateArtistMetadata
            ):
                artist_table.add_row(
                    self.clean_table_row(
                        [
                            song.get_future_title(),
                            song.get_future_index(),
                            song.artist,
                            song.get_future_artist(),
                        ]
                    )
                )
            print(artist_table, "\n")

        # rename file
        if self.has_any_song_action(song_actions.RenameFile):
            print("The following songs will have their files renamed:")
            rename_file_table = self.make_table(
                ["Title", "Artist", "Old Filename", "New Filename"]
            )
            for song, action in self.get_songs_with_action(song_actions.RenameFile):
                rename_file_table.add_row(
                    self.clean_table_row(
                        [
                            song.get_future_title(),
                            song.get_future_artist(),
                            None if song.file is None else song.file.name,
                            action.new_name,
                        ]
                    )
                )
            print(rename_file_table, "\n")

        # delete file
        if self.has_any_song_action(song_actions.Delete):
            print("The following songs will have their files PERMANENTLY DELETED:")
            delete_table = self.make_table(["Title", "Artist", "Filename"])
            for song, action in self.get_songs_with_action(song_actions.Delete):
                delete_table.add_row(
                    self.clean_table_row(
                        [
                            song.get_future_title(),
                            song.get_future_artist(),
                            None if song.file is None else song.file.name,
                        ]
                    )
                )
            print(delete_table, "\n")

    def make_table(self, field_names: list[str]) -> PrettyTable:
        table = PrettyTable(field_names, hrules=ALL)
        table.set_style(SINGLE_BORDER)
        return table

    @staticmethod
    def clean_table_row(row: list[Any]) -> list[Any]:
        for i, value in enumerate(row):
            if value is None:
                row[i] = "(none)"
        return row

    def has_any_song_action(
        self, song_action_type: Type[song_actions.SongAction]
    ) -> bool:
        for song in self.songs:
            for action in song.actions:
                if isinstance(action, song_action_type):
                    return True
        return False

    T = TypeVar("T", bound=song_actions.SongAction)

    def get_songs_with_action(
        self, song_action_type: Type[T]
    ) -> Iterable[tuple[Song, T]]:
        for song in self.songs:
            for action in song.actions:
                if isinstance(action, song_action_type):
                    yield song, action

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
