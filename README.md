# YouTube Song Sync

Downloads and syncs songs in YouTube playlists.

**Features:**

- Downloads entire playlists (or individual songs) to MP3 files.
- Playlist syncing with "diffing"
    - Adding songs to a YouTube playlist will only download the new songs.
    - Rearranging songs in a YouTube playlist will change their indexes and filenames locally.
    - Songs that have been deleted from a YouTube playlist are deleted locally (but you can specify to not delete them).
- Normalizes audio levels for consistent volume.
- MP3 metadata (ID3) support so that titles and artists appear in music player applications and file browsers.
    - Metadata is set automatically but can be updated manually.
- Confirmation screen before changes are applied with formatted tables showing changes that will be applied.

## Screenshot

![Screenshot](docs/images/demo.png)

## Setup

### Install Python

Supports Python 3 versions >= 3.10

### Install Python Dependencies

```
pip install -r requirements.txt
```

### Install FFMPEG

[Download FFMPEG](https://ffmpeg.org/download.html)

### License

MIT License (see LICENSE.md)
