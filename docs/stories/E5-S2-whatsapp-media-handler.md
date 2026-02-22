# E5-S2: WhatsApp Media Handler

| Field        | Value                                  |
|--------------|----------------------------------------|
| **Story ID** | E5-S2                                  |
| **Title**    | WhatsApp Media Handler                 |
| **Epic**     | E5 — Clawdbot Integration              |
| **Status**   | TODO                                   |
| **Points**   | 2                                      |
| **Dependencies** | E5-S1 (skill package structure)    |

---

## Overview

Handle video files received through WhatsApp messages via Clawdbot. This includes detecting video attachments, downloading them to a temporary directory, validating format and size, and providing the local file path to the analysis script.

This story abstracts the complexity of WhatsApp media handling so the analysis pipeline receives a clean local file path regardless of the source.

---

## Acceptance Criteria

- [ ] Function `detect_video_attachment()` identifies video attachments in incoming messages
- [ ] Function `download_media()` downloads the video to a local temp directory
- [ ] Supports common video formats: `.mp4`, `.mov`, `.webm`, `.mkv`, `.avi`, `.3gp`
- [ ] Validates file size before downloading — warn if >100MB, reject if >500MB
- [ ] Detects MIME type to confirm it's actually a video (not a renamed file)
- [ ] Generates a unique temp file path to avoid collisions
- [ ] Automatic cleanup of downloaded files after processing (configurable retention)
- [ ] Handles download failures gracefully (network timeout, partial download)
- [ ] Logs download progress for large files
- [ ] Unit tests cover detection, download, and validation logic

---

## Technical Specification

### Files to Create

- `src/screen_feedback_agent/media.py` — media detection, download, and validation

### Data Structures

```python
from dataclasses import dataclass

@dataclass
class MediaAttachment:
    """Represents a media attachment from a chat message."""
    media_id: str
    mime_type: str
    file_size: int  # bytes
    filename: str | None = None

@dataclass
class DownloadedMedia:
    """A downloaded media file on local disk."""
    local_path: Path
    original_filename: str
    mime_type: str
    file_size_mb: float
```

### Function Signatures

```python
SUPPORTED_VIDEO_MIMES = {
    "video/mp4", "video/quicktime", "video/webm",
    "video/x-matroska", "video/x-msvideo", "video/3gpp",
}

SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".3gp"}

MAX_FILE_SIZE_MB = 500
WARN_FILE_SIZE_MB = 100

def detect_video_attachment(message: dict) -> MediaAttachment | None:
    """Detect video attachment in a chat message.

    Args:
        message: Raw message dict from Clawdbot/WhatsApp API.
                 Expected to have 'media' or 'attachments' field.

    Returns:
        MediaAttachment if a video is found, None otherwise.
    """

def validate_media(attachment: MediaAttachment) -> tuple[bool, str]:
    """Validate media attachment before downloading.

    Returns:
        Tuple of (is_valid, reason_if_invalid)
    """

def download_media(
    attachment: MediaAttachment,
    download_dir: Path | None = None,
    api_client: object | None = None,
    verbose: bool = False,
) -> DownloadedMedia:
    """Download media attachment to local disk.

    Args:
        attachment: Media attachment metadata
        download_dir: Target directory (default: system temp)
        api_client: WhatsApp/Clawdbot API client for downloading
        verbose: Print download progress

    Returns:
        DownloadedMedia with local file path

    Raises:
        ValueError: File too large or unsupported format
        RuntimeError: Download failed
    """

def cleanup_media(downloaded: DownloadedMedia) -> None:
    """Remove downloaded media file from disk."""

@contextmanager
def managed_media_download(
    attachment: MediaAttachment,
    **kwargs,
) -> Generator[DownloadedMedia, None, None]:
    """Context manager that downloads and auto-cleans up media."""
```

### External Dependencies

- Standard library: `pathlib`, `tempfile`, `mimetypes`, `uuid`
- Clawdbot API client (interface only — actual implementation depends on Clawdbot SDK)

---

## Implementation Steps

1. **Define data classes** — `MediaAttachment` and `DownloadedMedia`.
2. **Implement `detect_video_attachment()`**:
   a. Check message dict for `media`, `attachments`, or `document` fields (WhatsApp API format).
   b. Filter by MIME type against `SUPPORTED_VIDEO_MIMES`.
   c. Return first video attachment found, or `None`.
3. **Implement `validate_media()`**:
   a. Check MIME type is in `SUPPORTED_VIDEO_MIMES`.
   b. Check file size < `MAX_FILE_SIZE_MB * 1024 * 1024`.
   c. Warn (via logging) if size > `WARN_FILE_SIZE_MB`.
   d. Return `(True, "")` if valid, `(False, reason)` if not.
4. **Implement `download_media()`**:
   a. Validate attachment first.
   b. Create temp directory if none provided.
   c. Generate unique filename: `{uuid}_{original_filename}`.
   d. Download via API client's download method (abstract interface).
   e. Verify downloaded file size matches expected size.
   f. Verify MIME type of downloaded file with `mimetypes.guess_type()`.
   g. Return `DownloadedMedia` object.
5. **Implement `cleanup_media()`** — delete local file if it exists.
6. **Implement `managed_media_download()`** — yield `DownloadedMedia`, cleanup in `finally`.
7. **Integrate with `scripts/analyze.sh`** — the shell script receives the local path from the Clawdbot framework, which calls these functions.

### Edge Cases

- **No video in message** — `detect_video_attachment()` returns `None`. Skill should not trigger.
- **Multiple videos in one message** — return only the first; log a warning about others.
- **WhatsApp video compression** — WhatsApp re-encodes videos; quality may be reduced. Not our concern.
- **File size exactly at limit** — use strict `<` comparison (500MB is too large, 499MB is OK).
- **Download interrupted** — partial file on disk. Delete and raise `RuntimeError`.
- **Filename contains special characters** — sanitize filename before creating on disk.
- **MIME type mismatch** — server says `video/mp4` but file is actually an image. Verify with `ffprobe` after download.

---

## Testing Requirements

### Unit Tests — `tests/test_media_handler.py`

```python
def test_detect_video_mp4():
    """MP4 video attachment is detected."""
    msg = {"media": {"mime_type": "video/mp4", "id": "123", "file_size": 1000}}
    result = detect_video_attachment(msg)
    assert result is not None
    assert result.mime_type == "video/mp4"

def test_detect_video_none_for_image():
    """Image attachment returns None."""
    msg = {"media": {"mime_type": "image/jpeg", "id": "123", "file_size": 1000}}
    assert detect_video_attachment(msg) is None

def test_detect_video_none_for_text_only():
    """Text-only message returns None."""
    msg = {"text": "hello"}
    assert detect_video_attachment(msg) is None

def test_validate_media_valid():
    """Valid video passes validation."""
    att = MediaAttachment("id", "video/mp4", 50_000_000)
    valid, _ = validate_media(att)
    assert valid is True

def test_validate_media_too_large():
    """File over 500MB fails validation."""
    att = MediaAttachment("id", "video/mp4", 600_000_000)
    valid, reason = validate_media(att)
    assert valid is False
    assert "size" in reason.lower()

def test_validate_media_unsupported_mime():
    """Unsupported MIME type fails validation."""
    att = MediaAttachment("id", "audio/mpeg", 1000)
    valid, reason = validate_media(att)
    assert valid is False

def test_download_media_success(mock_api_client, tmp_path):
    """Video is downloaded to local path."""

def test_download_media_size_mismatch(mock_api_client, tmp_path):
    """RuntimeError raised when download size doesn't match."""

def test_cleanup_media(tmp_path):
    """Downloaded file is deleted."""
    filepath = tmp_path / "test.mp4"
    filepath.touch()
    dm = DownloadedMedia(filepath, "test.mp4", "video/mp4", 1.0)
    cleanup_media(dm)
    assert not filepath.exists()

def test_managed_media_download_cleanup(mock_api_client, tmp_path):
    """File is cleaned up after context manager exits."""

def test_managed_media_download_cleanup_on_error(mock_api_client, tmp_path):
    """File is cleaned up even when exception occurs."""
```

---

## Example Usage

```python
from screen_feedback_agent.media import (
    detect_video_attachment,
    managed_media_download,
)

# Incoming WhatsApp message (from Clawdbot)
message = {
    "text": "analyze this recording",
    "media": {
        "id": "wa_media_12345",
        "mime_type": "video/mp4",
        "file_size": 52_428_800,  # 50 MB
        "filename": "screen-recording.mp4",
    }
}

attachment = detect_video_attachment(message)
if attachment:
    with managed_media_download(attachment, api_client=wa_client) as media:
        print(f"Downloaded: {media.local_path} ({media.file_size_mb:.1f} MB)")
        # Pass media.local_path to sfa analyze
    # File auto-cleaned up
```
