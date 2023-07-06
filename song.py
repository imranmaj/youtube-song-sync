import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from mp3_metadata import CustomId3MetadataKey, Mp3Metadata

if TYPE_CHECKING:
    import song_actions


@dataclasses.dataclass
class Song:
    video_id: Optional[str] = None
    index: Optional[int] = None
    artist: Optional[str] = None
    title: Optional[str] = None
    file: Optional[Path] = None
    actions: list["song_actions.SongAction"] = dataclasses.field(default_factory=list)

    def apply(self) -> None:
        for action in self.actions:
            action.apply(self)

    # @staticmethod
    # def from_video_id_or_url(video_id_or_url: str) -> "Song":
    #     raise NotImplementedError()

    @staticmethod
    def from_file(file: Path) -> "Song":
        if not file.is_file():
            raise ValueError(f"file {file} is not a file")

        metadata = Mp3Metadata(file)
        video_id = metadata.get_custom_mp3_metadata(CustomId3MetadataKey.VIDEO_ID)
        str_index = metadata.get_custom_mp3_metadata(CustomId3MetadataKey.INDEX)
        index = None if str_index is None else int(str_index)
        artist = metadata.get_mp3_metadata("artist")
        title = metadata.get_mp3_metadata("title")

        return Song(
            video_id=video_id, index=index, artist=artist, title=title, file=file
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
