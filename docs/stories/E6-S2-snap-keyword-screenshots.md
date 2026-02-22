# Story E6-S2: "Snap" Keyword Screenshot Extraction

## Header
- **Story ID:** E6-S2
- **Title:** Extract Screenshots on "Snap" Keyword
- **Epic:** E6 - Enhanced Analysis Pipeline
- **Status:** TODO
- **Points:** 3
- **Dependencies:** E6-S1 (Whisper with word timestamps)

## Overview
When the user says "snap" during recording, extract the video frame at that exact moment and include it as an image in the Gemini prompt. This gives the AI precise visual context about what the user is pointing at.

**Why this matters:** Video analysis alone misses specific UI details. By saying "snap" and including that frame, the user can highlight exactly what needs attention.

## Acceptance Criteria
- [ ] Detect "snap" keyword in transcription
- [ ] Extract video frame at timestamp of "snap"
- [ ] Support multiple snaps per video
- [ ] Include extracted frames in Gemini prompt
- [ ] Frame quality sufficient for text readability (1080p or higher)
- [ ] Optional: support alternative keywords ("screenshot", "capture")

## Technical Specification

### Keyword Detection
```python
# src/screen_feedback_agent/snapshots.py

from dataclasses import dataclass
from pathlib import Path
import subprocess

@dataclass
class Snapshot:
    timestamp: float
    image_path: Path
    context: str  # What user said around the snap

SNAP_KEYWORDS = ["snap", "screenshot", "capture", "here"]

def detect_snap_moments(
    segments: list[SpeechSegment],
    keywords: list[str] = SNAP_KEYWORDS,
) -> list[tuple[float, str]]:
    """
    Find timestamps where user says a snap keyword.
    
    Returns:
        List of (timestamp, surrounding_context) tuples
    """
    snap_moments = []
    
    for segment in segments:
        text_lower = segment.text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                # Find approximate position of keyword
                words = segment.text.split()
                for i, word in enumerate(words):
                    if keyword in word.lower():
                        # Estimate timestamp (linear interpolation)
                        word_ratio = i / len(words)
                        timestamp = segment.start + (segment.end - segment.start) * word_ratio
                        
                        # Get surrounding context (3 words before/after)
                        start_idx = max(0, i - 3)
                        end_idx = min(len(words), i + 4)
                        context = " ".join(words[start_idx:end_idx])
                        
                        snap_moments.append((timestamp, context))
    
    return snap_moments
```

### Frame Extraction
```python
def extract_frame(
    video_path: Path,
    timestamp: float,
    output_dir: Path,
) -> Path:
    """
    Extract a single frame from video at timestamp.
    
    Returns:
        Path to extracted PNG image
    """
    output_path = output_dir / f"snap_{timestamp:.2f}.png"
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(timestamp),
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "1",  # Highest quality
        str(output_path)
    ]
    
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def extract_all_snapshots(
    video_path: Path,
    segments: list[SpeechSegment],
    output_dir: Path,
) -> list[Snapshot]:
    """
    Extract all snap-triggered screenshots from video.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    snap_moments = detect_snap_moments(segments)
    snapshots = []
    
    for timestamp, context in snap_moments:
        image_path = extract_frame(video_path, timestamp, output_dir)
        snapshots.append(Snapshot(
            timestamp=timestamp,
            image_path=image_path,
            context=context,
        ))
    
    return snapshots
```

### Integration with Gemini Prompt
```python
def build_multimodal_prompt(
    video_path: Path,
    transcription: str,
    snapshots: list[Snapshot],
) -> list:
    """
    Build Gemini prompt with video + snapshot images.
    """
    prompt_parts = []
    
    # Add video
    video_file = genai.upload_file(path=str(video_path))
    prompt_parts.append(video_file)
    
    # Add snapshots with context
    for snap in snapshots:
        prompt_parts.append(f"\n--- SNAPSHOT at {snap.timestamp:.1f}s ---")
        prompt_parts.append(f"User said: '{snap.context}'")
        prompt_parts.append(genai.upload_file(path=str(snap.image_path)))
    
    # Add analysis instructions
    prompt_parts.append(ANALYSIS_PROMPT.format(transcription=transcription))
    
    return prompt_parts
```

## Implementation Steps
1. Create `snapshots.py` module
2. Implement keyword detection with word-level timestamps
3. Add FFmpeg frame extraction
4. Update Gemini prompt builder to include images
5. Handle cleanup of temporary image files
6. Add tests

## Testing Requirements

### Unit Tests
```python
def test_detect_snap_keyword():
    """Finds 'snap' in transcription."""
    segments = [
        SpeechSegment(0.0, 5.0, "Look at this button snap here"),
    ]
    moments = detect_snap_moments(segments)
    assert len(moments) == 1
    assert 0 < moments[0][0] < 5.0

def test_extract_frame_quality():
    """Extracted frame is readable."""
    frame = extract_frame(test_video, 2.5, tmp_path)
    img = Image.open(frame)
    assert img.width >= 1280  # At least 720p

def test_multiple_snaps():
    """Handles multiple snap keywords."""
    segments = [
        SpeechSegment(0.0, 3.0, "First snap here"),
        SpeechSegment(5.0, 8.0, "Second snap there"),
    ]
    moments = detect_snap_moments(segments)
    assert len(moments) == 2
```

## Example Usage
```python
# Full pipeline with snapshots
segments = detect_speech_segments_whisper("recording.mp4")
snapshots = extract_all_snapshots("recording.mp4", segments, Path("/tmp/snaps"))

print(f"Found {len(snapshots)} snap moments:")
for snap in snapshots:
    print(f"  {snap.timestamp:.1f}s: {snap.context}")
    print(f"  Image: {snap.image_path}")
```
