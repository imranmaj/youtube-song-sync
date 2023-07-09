import abc
from typing import TYPE_CHECKING, Any, Iterable, Type, TypeVar

from prettytable import ALL, SINGLE_BORDER, PrettyTable

from ytss import song_actions

if TYPE_CHECKING:
    from ytss.song import Song


class Actionable(abc.ABC):
    @abc.abstractmethod
    def apply(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def iter_songs(self) -> Iterable["Song"]:
        raise NotImplementedError()

    def confirm_and_apply(self) -> None:
        print()
        self.render_changelist()
        if self.has_any_song_action(song_actions.SongAction):
            self.get_confirmation()
            self.apply()

    @staticmethod
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

    def render_changelist(self) -> None:
        if not self.has_any_song_action(song_actions.SongAction):
            print("No changes to be applied!")
            return

        print(f"The following changes will be applied:", "\n")

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
        for song in self.iter_songs():
            for action in song.actions:
                if isinstance(action, song_action_type):
                    return True
        return False

    T = TypeVar("T", bound=song_actions.SongAction)

    def get_songs_with_action(
        self, song_action_type: Type[T]
    ) -> Iterable[tuple["Song", T]]:
        for song in self.iter_songs():
            for action in song.actions:
                if isinstance(action, song_action_type):
                    yield song, action
