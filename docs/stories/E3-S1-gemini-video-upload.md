# E3-S1: Gemini Video Upload

| Field        | Value                                  |
|--------------|----------------------------------------|
| **Story ID** | E3-S1                                  |
| **Title**    | Gemini Video Upload                    |
| **Epic**     | E3 — Gemini API Analysis               |
| **Status**   | TODO                                   |
| **Points**   | 2                                      |
| **Dependencies** | E2-S3 (compressed video ready for upload) |

---

## Overview

Implement reliable video upload to the Gemini Files API with retry logic, progress tracking, and automatic cleanup of uploaded files after analysis. This wraps the `google-generativeai` SDK's file upload functionality with production-grade error handling.

This is the bridge between local video processing and cloud-based AI analysis — reliability here is critical because upload failures waste all prior processing effort.

---

## Acceptance Criteria

- [ ] Function `upload_video()` uploads a video file to Gemini Files API and returns a file reference
- [ ] Polls for processing completion with configurable timeout (default: 300s)
- [ ] Retries on transient errors (network, rate limit) with exponential backoff (max 3 retries)
- [ ] Reports upload progress via callback
- [ ] Function `cleanup_uploaded_file()` deletes the file from Gemini after use
- [ ] Context manager `managed_upload()` auto-cleans up on exit (even on exceptions)
- [ ] API key is loaded from config (E4-S1) or environment variable
- [ ] Validates file exists and is under Gemini's size limit (2GB) before uploading
- [ ] Clear error messages for: missing API key, file too large, processing failure, timeout
- [ ] Unit tests mock the Gemini SDK for offline testing

---

## Technical Specification

### Files to Modify

- `src/screen_feedback_agent/gemini.py` — extract upload logic from `analyze_video()` into dedicated functions

### Function Signatures

```python
from contextlib import contextmanager
from typing import Generator

def upload_video(
    video_path: Path,
    api_key: str | None = None,
    timeout: int = 300,
    max_retries: int = 3,
    progress_callback: Callable[[str], None] | None = None,
    verbose: bool = False,
) -> genai.types.File:
    """Upload video to Gemini Files API.

    Args:
        video_path: Path to video file
        api_key: Gemini API key (falls back to env/config)
        timeout: Max seconds to wait for processing
        max_retries: Number of retry attempts on transient failure
        progress_callback: Called with status messages during upload/processing
        verbose: Print debug output

    Returns:
        Gemini File object ready for use in prompts

    Raises:
        ValueError: Missing API key or file too large
        TimeoutError: Processing didn't complete within timeout
        RuntimeError: Processing failed or unrecoverable API error
    """

def cleanup_uploaded_file(file_ref: genai.types.File, verbose: bool = False) -> None:
    """Delete an uploaded file from Gemini."""

@contextmanager
def managed_upload(
    video_path: Path,
    **kwargs,
) -> Generator[genai.types.File, None, None]:
    """Context manager that uploads a video and cleans up on exit.

    Usage:
        with managed_upload(Path("video.mp4")) as file_ref:
            response = model.generate_content([file_ref, prompt])
    """

def _configure_api(api_key: str | None = None) -> None:
    """Configure Gemini API with key from arg, env, or config file."""

def _wait_for_processing(
    file_ref: genai.types.File,
    timeout: int,
    poll_interval: float = 2.0,
    progress_callback: Callable[[str], None] | None = None,
) -> genai.types.File:
    """Poll until file processing is complete."""
```

### External Dependencies

- `google-generativeai>=0.3` (already in pyproject.toml)
- `screen_feedback_agent.config` — for `get_api_key()`

---

## Implementation Steps

1. **Implement `_configure_api()`** — check arg → `os.environ["GEMINI_API_KEY"]` → `config.get_api_key()`. Raise `ValueError` with clear message if none found.
2. **Implement `upload_video()`**:
   a. Validate file exists and size < 2GB.
   b. Configure API.
   c. Attempt upload with retry loop:
      - `genai.upload_file(path=str(video_path))`.
      - Catch `google.api_core.exceptions.GoogleAPIError` for transient errors.
      - Exponential backoff: 2s, 4s, 8s.
   d. Call `_wait_for_processing()`.
   e. Return file reference.
3. **Implement `_wait_for_processing()`**:
   a. Poll `genai.get_file(file_ref.name)` every `poll_interval` seconds.
   b. Check `file.state.name`: `"PROCESSING"` → continue, `"ACTIVE"` → return, `"FAILED"` → raise `RuntimeError`.
   c. If elapsed time exceeds `timeout`, raise `TimeoutError`.
   d. Call `progress_callback` with status updates.
4. **Implement `cleanup_uploaded_file()`** — `genai.delete_file(file_ref.name)`. Catch and log errors (don't fail if cleanup fails).
5. **Implement `managed_upload()`** — `yield` the uploaded file reference, call `cleanup_uploaded_file()` in the `finally` block.
6. **Refactor `analyze_video()`** — use `managed_upload()` instead of inline upload/cleanup code.

### Edge Cases

- **Missing API key** — clear `ValueError` before any network call.
- **File > 2GB** — check size before upload, raise `ValueError`.
- **Network timeout during upload** — caught by retry loop.
- **Rate limiting (429)** — caught by retry loop with backoff.
- **Processing stuck** — `_wait_for_processing` times out after `timeout` seconds.
- **Processing fails server-side** — state becomes `"FAILED"`, raise `RuntimeError`.
- **Cleanup fails** — log warning, don't raise (best-effort cleanup).

---

## Testing Requirements

### Unit Tests — `tests/test_gemini_upload.py`

```python
def test_upload_video_success(mock_genai, tmp_video):
    """Successful upload returns file reference."""

def test_upload_missing_api_key(monkeypatch, tmp_video):
    """ValueError raised when no API key is available."""

def test_upload_file_too_large(tmp_path):
    """ValueError raised for files > 2GB."""

def test_upload_retries_on_transient_error(mock_genai, tmp_video):
    """Upload retries on transient API errors."""

def test_upload_max_retries_exceeded(mock_genai, tmp_video):
    """RuntimeError after max retries exhausted."""

def test_wait_for_processing_success(mock_genai):
    """Polling returns when state becomes ACTIVE."""

def test_wait_for_processing_timeout(mock_genai):
    """TimeoutError raised when processing exceeds timeout."""

def test_wait_for_processing_failure(mock_genai):
    """RuntimeError raised when processing state is FAILED."""

def test_cleanup_uploaded_file(mock_genai):
    """File is deleted from Gemini."""

def test_cleanup_failure_logged(mock_genai, caplog):
    """Cleanup failure is logged but doesn't raise."""

def test_managed_upload_cleanup_on_exception(mock_genai, tmp_video):
    """File is cleaned up even when exception occurs in context."""

def test_progress_callback_called(mock_genai, tmp_video):
    """Progress callback receives status updates."""
```

### Mock Fixture — `tests/conftest.py`

```python
@pytest.fixture
def mock_genai(monkeypatch):
    """Mock google.generativeai module for offline tests."""
    # Mock upload_file, get_file, delete_file, configure
```

---

## Example Usage

```python
from pathlib import Path
from screen_feedback_agent.gemini import upload_video, managed_upload

# Direct upload with manual cleanup
file_ref = upload_video(Path("compressed.mp4"), verbose=True)
# ... use file_ref ...
cleanup_uploaded_file(file_ref)

# Context manager (preferred)
with managed_upload(Path("compressed.mp4"), verbose=True) as file_ref:
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content([file_ref, prompt])
    # file_ref is automatically cleaned up after this block
```
