import dataclasses
from pathlib import Path
from typing import Iterable, Optional

from ytss import song_actions, utils
from ytss.actionable import Actionable
from ytss.constants import CustomId3MetadataKey
from ytss.mp3_metadata import Mp3Metadata


@dataclasses.dataclass
class Song(Actionable):
    video_id: Optional[str] = None
    index: Optional[int] = None
    artist: Optional[str] = None
    title: Optional[str] = None
    file: Optional[Path] = None
    actions: list["song_actions.SongAction"] = dataclasses.field(default_factory=list)

    def apply(self) -> None:
        for action in self.actions:
            action.apply(self)

    def iter_songs(self) -> Iterable["Song"]:
        yield self

    @staticmethod
    def from_file(file: Path) -> "Song":
        if not file.exists():
            raise FileNotFoundError(f"file {file} does not exist")
        if not file.is_file():
            raise FileNotFoundError(f"file {file} is not a file")

        metadata = Mp3Metadata(file)
        video_id = metadata.get_custom_mp3_metadata(CustomId3MetadataKey.VIDEO_ID)
        str_index = metadata.get_custom_mp3_metadata(CustomId3MetadataKey.INDEX)
        index = None if str_index is None else int(str_index)
        artist = metadata.get_mp3_metadata("artist")
        title = metadata.get_mp3_metadata("title")

        return Song(
            video_id=video_id, index=index, artist=artist, title=title, file=file
        )

    def update_metadata(
        self,
        new_title: Optional[str],
        new_artist: Optional[str],
        new_video_id: Optional[str],
        new_index: Optional[int],
        rename_allowed: bool,
    ) -> None:
        if new_title is not None:
            self.actions.append(song_actions.UpdateTitleMetadata(new_title))
        if new_artist is not None:
            self.actions.append(song_actions.UpdateArtistMetadata(new_artist))
        if new_video_id is not None:
            self.actions.append(song_actions.UpdateVideoIdMetadata(new_video_id))
        if new_index is not None:
            self.actions.append(song_actions.UpdateIndexMetadata(new_index))

        if rename_allowed:
            future_artist = self.get_future_artist()
            future_title = self.get_future_title()
            future_index = self.get_future_index()
            if (
                future_artist is not None
                and future_title is not None
                and future_index is not None
            ):
                self.actions.append(
                    song_actions.RenameFile(
                        utils.make_filename(future_artist, future_title, future_index)
                    )
                )

    def get_future_video_id(self) -> Optional[str]:
        video_id = self.video_id
        for action in self.actions:
            if isinstance(action, song_actions.UpdateVideoIdMetadata):
                video_id = action.video_id
        return video_id

    def get_future_index(self) -> Optional[int]:
        index = self.index
        for action in self.actions:
            if isinstance(action, song_actions.UpdateIndexMetadata):
                index = action.index
        return index

    def get_future_artist(self) -> Optional[str]:
        artist = self.artist
        for action in self.actions:
            if isinstance(action, song_actions.UpdateArtistMetadata):
                artist = action.artist
        return artist

    def get_future_title(self) -> Optional[str]:
        title = self.title
        for action in self.actions:
            if isinstance(action, song_actions.UpdateTitleMetadata):
                title = action.title
        return title
