import abc
import dataclasses
from pathlib import Path
from typing import Any, Optional

import tqdm
import yt_dlp
from pydub import AudioSegment

from exceptions import ActionError
from mp3_metadata import CustomId3MetadataKey, Mp3Metadata
from song import Song


class SongAction(abc.ABC):
    @abc.abstractmethod
    def apply(self, song: Song) -> None:
        pass

    def set_mp3_metadata(
        self, file: Optional[Path], metadata_key: str, value: Optional[str]
    ) -> None:
        if file is None:
            raise ActionError(self, "file is None")

        Mp3Metadata(file).set_mp3_metadata(metadata_key, value)

    def set_custom_mp3_metadata(
        self,
        file: Optional[Path],
        metadata_key: CustomId3MetadataKey,
        value: Optional[str],
    ) -> None:
        if file is None:
            raise ActionError(self, "file is None")

        Mp3Metadata(file).set_custom_mp3_metadata(metadata_key, value)


@dataclasses.dataclass(eq=True, frozen=True)
class UpdateVideoIdMetadata(SongAction):
    video_id: str

    def apply(self, song: Song) -> None:
        song.video_id = self.video_id
        self.set_custom_mp3_metadata(
            song.file, metadata_key=CustomId3MetadataKey.VIDEO_ID, value=self.video_id
        )


@dataclasses.dataclass(eq=True, frozen=True)
class UpdateIndexMetadata(SongAction):
    index: int

    def apply(self, song: Song) -> None:
        song.index = self.index
        self.set_custom_mp3_metadata(
            song.file, metadata_key=CustomId3MetadataKey.INDEX, value=str(self.index)
        )


@dataclasses.dataclass(eq=True, frozen=True)
class UpdateArtistMetadata(SongAction):
    artist: Optional[str]

    def apply(self, song: Song) -> None:
        song.artist = self.artist
        self.set_mp3_metadata(song.file, metadata_key="artist", value=self.artist)


@dataclasses.dataclass(eq=True, frozen=True)
class UpdateTitleMetadata(SongAction):
    title: str

    def apply(self, song: Song) -> None:
        song.title = self.title
        self.set_mp3_metadata(song.file, metadata_key="title", value=self.title)


class ProgressHook:
    def __init__(self):
        self.progress_bar = None

    def __call__(self, progress_dict: dict[str, Any]) -> None:
        if progress_dict["status"] == "downloading":
            if self.progress_bar is None and progress_dict["total_bytes"] is not None:
                self.progress_bar = tqdm.tqdm(
                    total=progress_dict["total_bytes"], unit="B", unit_scale=True
                )
            if self.progress_bar is not None:
                self.progress_bar.n = progress_dict["downloaded_bytes"]
                self.progress_bar.refresh()
        elif progress_dict["status"] == "finished" and self.progress_bar is not None:
            self.progress_bar.close()


@dataclasses.dataclass(eq=True, frozen=True)
class Download(SongAction):
    video_id: str
    output_file: Path

    def apply(self, song: Song) -> None:
        print(f"Downloading {self.output_file.name}...")

        song.video_id = self.video_id
        song.file = self.output_file

        ydl_opts = {
            "format": "bestaudio",
            "quiet": True,
            "no_warnings": True,
            "outtmpl": str(song.file.with_suffix("")),
            "progress_hooks": [ProgressHook()],
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }
            ],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.video_id])


@dataclasses.dataclass(eq=True, frozen=True)
class Delete(SongAction):
    def apply(self, song: Song) -> None:
        if song.file is None:
            raise ActionError(self, "file is None")
        if not song.file.is_file():
            raise ActionError(self, "file does not exist or is not a file")

        song.file.unlink()


@dataclasses.dataclass(eq=True, frozen=True)
class Normalize(SongAction):
    NORMALIZATION = -20

    def apply(self, song: Song) -> None:
        if song.file is None:
            raise ActionError(self, "file is None")

        audio_segment = AudioSegment.from_mp3(song.file)
        normalized = audio_segment.apply_gain(self.NORMALIZATION - audio_segment.dBFS)

        dest_temp = song.file.with_name(song.file.name + ".temp")
        normalized.export(dest_temp, bitrate="121k")
        song.file.unlink()
        dest_temp.rename(song.file)


@dataclasses.dataclass(eq=True, frozen=True)
class RenameFile(SongAction):
    new_name: str

    def apply(self, song: Song) -> None:
        if song.file is None:
            raise ActionError(self, "file is None")

        new_file = song.file.with_name(self.new_name)
        song.file.rename(new_file)
