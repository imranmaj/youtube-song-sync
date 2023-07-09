from pathlib import Path
from typing import Optional

import eyed3
import eyed3.id3

from ytss.constants import CustomId3MetadataKey
from ytss.exceptions import Mp3MetadataError


class Mp3Metadata:
    def __init__(self, file: Path):
        self.file = file

    def get_mp3_metadata(self, metadata_key: str) -> str:
        tag = self._get_tag()
        return getattr(tag, metadata_key)

    def set_mp3_metadata(self, metadata_key: str, value: Optional[str]) -> None:
        tag = self._get_tag()
        setattr(tag, metadata_key, value)
        tag.save()

    def get_custom_mp3_metadata(
        self, metadata_key: CustomId3MetadataKey
    ) -> Optional[str]:
        tag = self._get_tag()
        if tag.user_text_frames is None:
            raise Mp3MetadataError(f"no custom user mp3 metadata for file {self.file}")
        text_frame = tag.user_text_frames.get(description=metadata_key.value)
        if text_frame is None:
            return None
        return text_frame.text

    def set_custom_mp3_metadata(
        self,
        metadata_key: CustomId3MetadataKey,
        value: Optional[str],
    ) -> None:
        tag = self._get_tag()
        if tag.user_text_frames is None:
            raise Mp3MetadataError(f"no custom user mp3 metadata for file {self.file}")
        tag.user_text_frames.set(value, description=metadata_key.value)
        tag.save()

    def _get_tag(self) -> eyed3.id3.Tag:
        metadata = eyed3.load(self.file)
        if metadata is None:
            raise Mp3MetadataError(
                f"no mp3 metadata for file {self.file}: file is not an mp3 file"
            )
        if metadata.tag is None:
            metadata.initTag()

        return metadata.tag  # type: ignore # was initialized so cannot be None
