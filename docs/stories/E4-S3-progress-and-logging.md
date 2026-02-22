# E4-S3: Progress & Logging

| Field        | Value                                  |
|--------------|----------------------------------------|
| **Story ID** | E4-S3                                  |
| **Title**    | Progress & Logging                     |
| **Epic**     | E4 — CLI & Output Generation           |
| **Status**   | TODO                                   |
| **Points**   | 1                                      |
| **Dependencies** | E4-S1 (CLI framework)              |

---

## Overview

Add user-friendly progress indication and structured logging to the CLI. The processing pipeline runs several long stages (detection, transcription, upload, analysis) and users need visual feedback on what's happening and how long it might take.

This story transforms a "silent black box" experience into an informative, professional CLI interaction.

---

## Acceptance Criteria

- [ ] Rich progress bar shown during long operations (segment extraction, transcription, upload)
- [ ] Stage indicators show current pipeline step with elapsed time
- [ ] Stages: `Detecting speech` → `Transcribing audio` → `Processing video` → `Uploading to Gemini` → `Analyzing` → `Generating report`
- [ ] Estimated time remaining shown when possible (based on segment count or file size)
- [ ] Verbose mode (`-v`) shows detailed debug output (FFmpeg commands, API responses, etc.)
- [ ] Structured logging via Python `logging` module (not just print statements)
- [ ] Log levels: INFO (default), DEBUG (verbose), WARNING, ERROR
- [ ] Clean error messages for user-facing errors (no tracebacks unless verbose)
- [ ] Spinner shown during indeterminate operations (API calls)
- [ ] Progress output goes to stderr (stdout reserved for machine-readable output if piped)

---

## Technical Specification

### Files to Create

- `src/screen_feedback_agent/progress.py` — progress and logging utilities

### Files to Modify

- `src/screen_feedback_agent/pipeline.py` — integrate progress callbacks
- `src/screen_feedback_agent/cli.py` — configure logging based on verbose flag

### Function Signatures

```python
# progress.py

import logging
from contextlib import contextmanager
from enum import Enum
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.console import Console

logger = logging.getLogger("sfa")

class PipelineStage(Enum):
    DETECTING = "Detecting speech"
    TRANSCRIBING = "Transcribing audio"
    EXTRACTING = "Processing video"
    UPLOADING = "Uploading to Gemini"
    ANALYZING = "Analyzing video"
    GENERATING = "Generating report"

@contextmanager
def pipeline_progress(console: Console | None = None):
    """Context manager for pipeline-wide progress display.

    Yields a PipelineTracker object that manages stages and progress.
    """

class PipelineTracker:
    """Tracks progress through pipeline stages."""

    def start_stage(self, stage: PipelineStage) -> None:
        """Begin a new pipeline stage with spinner."""

    def update_progress(self, current: int, total: int) -> None:
        """Update progress bar within current stage."""

    def complete_stage(self) -> None:
        """Mark current stage as complete."""

    def set_status(self, message: str) -> None:
        """Update status message within current stage."""

def configure_logging(verbose: bool = False) -> None:
    """Configure logging for the application.

    Args:
        verbose: If True, set DEBUG level; otherwise INFO.
    """

def format_duration(seconds: float) -> str:
    """Format seconds as human-readable duration string."""
```

### External Dependencies

- `rich>=13.0` (already in pyproject.toml)
- Standard library: `logging`, `time`

---

## Implementation Steps

1. **Create `progress.py`**:
   a. Define `PipelineStage` enum with stage names.
   b. Implement `configure_logging()` — set up root logger with appropriate level and format. Use `rich.logging.RichHandler` for pretty console output.
   c. Implement `format_duration()` — convert seconds to "Xs", "Xm Ys", or "Xh Ym Zs".
2. **Implement `PipelineTracker`**:
   a. Initialize with a Rich `Progress` instance.
   b. `start_stage()` — add a new task to the progress display with spinner.
   c. `update_progress()` — switch from spinner to progress bar, update current/total.
   d. `complete_stage()` — mark task complete, show elapsed time, advance to next.
   e. `set_status()` — update the description text of the current task.
3. **Implement `pipeline_progress()` context manager**:
   a. Create `Console(stderr=True)` to keep stdout clean.
   b. Create `Progress` with columns: `SpinnerColumn`, `TextColumn`, `BarColumn`, `TimeElapsedColumn`.
   c. Yield a `PipelineTracker` instance.
   d. On exit, display total elapsed time.
4. **Integrate into `pipeline.py`**:
   a. Accept optional `tracker: PipelineTracker` parameter in `run_pipeline()`.
   b. Call `tracker.start_stage()` before each pipeline step.
   c. Pass progress callbacks to extraction/transcription functions.
   d. Call `tracker.complete_stage()` after each step.
5. **Integrate into `cli.py`**:
   a. Call `configure_logging(verbose=verbose)` at the start of `analyze`.
   b. Wrap `run_pipeline()` in `pipeline_progress()` context manager.
   c. In non-verbose mode, catch exceptions and display clean Rich error panels.
   d. In verbose mode, use `rich.traceback` for full stack traces.

### Edge Cases

- **Piped output** — detect if stdout is a TTY; disable Rich formatting if not.
- **Very fast operations** — some stages complete instantly; don't flicker the progress bar. Use minimum display time of 0.1s.
- **Keyboard interrupt** — clean up progress display on Ctrl+C.
- **Nested progress** — segment extraction has per-segment progress within the extraction stage. Use Rich's nested task support.

---

## Testing Requirements

### Unit Tests — `tests/test_progress.py`

```python
def test_configure_logging_default():
    """Default logging level is INFO."""

def test_configure_logging_verbose():
    """Verbose mode sets DEBUG level."""

def test_format_duration_seconds():
    """Short durations formatted as seconds."""
    assert format_duration(5.2) == "5s"

def test_format_duration_minutes():
    """Minute-range durations formatted as Xm Ys."""
    assert format_duration(125.0) == "2m 5s"

def test_format_duration_hours():
    """Hour-range durations formatted as Xh Ym Zs."""
    assert format_duration(3661.0) == "1h 1m 1s"

def test_pipeline_stage_enum():
    """All expected stages are defined."""
    assert len(PipelineStage) == 6

def test_pipeline_tracker_stages():
    """Tracker can cycle through all stages without error."""

def test_pipeline_progress_context_manager():
    """Context manager creates and cleans up tracker."""
```

### Integration Tests

- Run `sfa analyze` on a test video and verify progress output appears on stderr.
- Verify verbose mode shows additional debug information.

---

## Example Usage

```python
from screen_feedback_agent.progress import (
    pipeline_progress,
    PipelineStage,
    configure_logging,
)

configure_logging(verbose=True)

with pipeline_progress() as tracker:
    tracker.start_stage(PipelineStage.DETECTING)
    segments = detect_speech_segments(video)
    tracker.complete_stage()

    tracker.start_stage(PipelineStage.EXTRACTING)
    for i, seg in enumerate(segments):
        tracker.update_progress(i + 1, len(segments))
        extract_segment(video, *seg, output)
    tracker.complete_stage()

    tracker.start_stage(PipelineStage.UPLOADING)
    tracker.set_status("Uploading 47.2 MB...")
    file_ref = upload_video(compressed_video)
    tracker.complete_stage()
```

**Terminal output:**
```
 Detecting speech ━━━━━━━━━━━━━━━━━━━━ 100% 0:00:03
 Transcribing audio ━━━━━━━━━━━━━━━━━━ 100% 0:00:12
 Processing video ━━━━━━━━━━━━━━━━━━━━ 100% 0:00:08
 Uploading to Gemini ━━━━━━━━━━━━━━━━━ 100% 0:00:15
 Analyzing video ━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:22
 Generating report ━━━━━━━━━━━━━━━━━━━ 100% 0:00:01

Total time: 1m 1s
```
