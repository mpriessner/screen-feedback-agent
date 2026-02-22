# E2-S3: Video Compression

| Field        | Value                                  |
|--------------|----------------------------------------|
| **Story ID** | E2-S3                                  |
| **Title**    | Video Compression                      |
| **Epic**     | E2 — Video Processing & Clipping       |
| **Status**   | TODO                                   |
| **Points**   | 2                                      |
| **Dependencies** | E2-S2 (concatenated video)         |

---

## Overview

Compress the concatenated video to a target file size suitable for Gemini API upload while preserving sufficient resolution for screen content readability. The compressor calculates optimal encoding parameters based on the target size and video duration.

This is the final step before API upload — balancing file size against the need for Gemini to read on-screen text and UI elements.

---

## Acceptance Criteria

- [ ] Function `compress_video()` takes input video and produces a compressed output
- [ ] Target file size is configurable (default: 50 MB)
- [ ] Maximum resolution cap of 1080p (downscale if source is larger)
- [ ] Uses H.264 (libx264) for video and AAC for audio
- [ ] Calculates appropriate CRF or bitrate to hit target size
- [ ] Two-pass encoding option for more accurate size targeting
- [ ] Reports compression statistics: original size, compressed size, ratio
- [ ] Skips compression if input is already under target size
- [ ] Preserves sufficient quality for screen text readability (minimum 720p if source allows)
- [ ] Unit tests verify output size is within tolerance of target

---

## Technical Specification

### Files to Modify

- `src/screen_feedback_agent/video.py` — replace `compress_video()` placeholder with full implementation

### New Data Structures

```python
@dataclass
class CompressionResult:
    """Statistics from video compression."""
    input_path: Path
    output_path: Path
    input_size_mb: float
    output_size_mb: float
    compression_ratio: float
    was_compressed: bool  # False if input was already under target
```

### Function Signatures

```python
def compress_video(
    video_path: Path,
    output_path: Path,
    max_size_mb: int = 50,
    max_resolution: int = 1080,
    min_resolution: int = 720,
    audio_bitrate: str = "64k",
    two_pass: bool = False,
    verbose: bool = False,
) -> CompressionResult:
    """Compress video for API upload.

    Args:
        video_path: Input video path
        output_path: Where to write compressed video
        max_size_mb: Target maximum file size in MB
        max_resolution: Maximum height in pixels
        min_resolution: Minimum height in pixels (won't downscale below this)
        audio_bitrate: Audio bitrate string for AAC
        two_pass: Use two-pass encoding for more accurate size targeting
        verbose: Print encoding progress

    Returns:
        CompressionResult with size statistics
    """

def _get_video_info(video_path: Path) -> dict:
    """Get video metadata (resolution, duration, bitrate, codec) via ffprobe.

    Returns:
        Dict with keys: width, height, duration, bitrate, codec, file_size_mb
    """

def _calculate_target_bitrate(
    target_size_mb: float,
    duration_seconds: float,
    audio_bitrate_kbps: int,
) -> int:
    """Calculate video bitrate (kbps) to hit target file size."""
```

### External Dependencies

- `ffmpeg`, `ffprobe` (system)
- Standard library: `subprocess`, `pathlib`, `json`

---

## Implementation Steps

1. **Implement `_get_video_info()`** — run `ffprobe -v quiet -print_format json -show_format -show_streams <video>`. Parse JSON to extract width, height, duration, bitrate, codec name, file size.
2. **Early exit check** — if input file size is already under `max_size_mb`, copy file to output and return `CompressionResult(was_compressed=False)`.
3. **Calculate target resolution** — if source height > `max_resolution`, compute scale factor to bring height to `max_resolution` (keep aspect ratio, ensure width is divisible by 2). If source height < `min_resolution`, keep original resolution.
4. **Calculate target bitrate** — `_calculate_target_bitrate()`: `video_bitrate = (target_size_mb * 8192 / duration_seconds) - audio_bitrate_kbps`. Ensure minimum 500 kbps.
5. **Single-pass encoding**:
   ```
   ffmpeg -y -i <input> -c:v libx264 -b:v <bitrate>k -maxrate <bitrate*1.5>k
     -bufsize <bitrate*2>k -vf scale=-2:<height>
     -c:a aac -b:a <audio_bitrate> <output>
   ```
6. **Two-pass encoding** (if enabled):
   - Pass 1: `ffmpeg -y -i <input> -c:v libx264 -b:v <bitrate>k -pass 1 -f null /dev/null`
   - Pass 2: `ffmpeg -y -i <input> -c:v libx264 -b:v <bitrate>k -pass 2 -c:a aac -b:a <audio_bitrate> <output>`
   - Clean up passlog files.
7. **Verify output** — check file exists and size is within 120% of target (some overshoot is acceptable).
8. **Return `CompressionResult`** with statistics.

### Edge Cases

- **Input already small enough** — skip compression, just copy.
- **Very short video (<5s)** — bitrate calculation may produce very high value. Cap at source bitrate.
- **Audio-only file** — no video stream. Just transcode audio with AAC.
- **Very low calculated bitrate** — if target is tiny relative to duration, enforce minimum 500 kbps and warn that target size may be exceeded.
- **Two-pass leftover files** — `ffmpeg2pass-0.log` and `.mbtree` files. Always clean up in a `finally` block.

---

## Testing Requirements

### Unit Tests — `tests/test_video_compression.py`

```python
def test_compress_reduces_file_size(large_sample_video, tmp_path):
    """Compressed output is smaller than input."""

def test_compress_skip_if_under_target(small_sample_video, tmp_path):
    """No compression if input is already under target size."""

def test_compress_respects_max_resolution(hd_sample_video, tmp_path):
    """Output resolution is capped at max_resolution."""

def test_compress_preserves_min_resolution(low_res_video, tmp_path):
    """Low-res video is not upscaled."""

def test_get_video_info(sample_video):
    """Video info returns expected metadata fields."""

def test_calculate_target_bitrate():
    """Bitrate calculation matches expected values."""
    # 50 MB target, 300s video, 64kbps audio
    bitrate = _calculate_target_bitrate(50.0, 300.0, 64)
    expected = (50 * 8192 / 300) - 64  # ~1301 kbps
    assert abs(bitrate - expected) < 1

def test_compress_output_is_valid_mp4(large_sample_video, tmp_path):
    """Compressed output is a valid MP4 probed by ffprobe."""

def test_compression_result_statistics(large_sample_video, tmp_path):
    """CompressionResult fields are populated correctly."""

def test_two_pass_cleans_up_logs(large_sample_video, tmp_path):
    """No passlog files remain after two-pass encoding."""
```

### Test Fixtures

- `large_sample_video` — generate a 10-second 1080p video with synthetic content (>5MB)
- `small_sample_video` — generate a 3-second low-bitrate video (<1MB)
- `hd_sample_video` — 5-second 4K video for resolution cap testing

---

## Example Usage

```python
from pathlib import Path
from screen_feedback_agent.video import compress_video

result = compress_video(
    Path("condensed.mp4"),
    Path("compressed.mp4"),
    max_size_mb=50,
    verbose=True,
)

print(f"Input:  {result.input_size_mb:.1f} MB")
print(f"Output: {result.output_size_mb:.1f} MB")
print(f"Ratio:  {result.compression_ratio:.1%}")
print(f"Compressed: {result.was_compressed}")
# Input:  120.3 MB
# Output: 47.8 MB
# Ratio:  39.7%
# Compressed: True
```
