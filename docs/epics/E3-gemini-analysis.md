# EPIC 3: Gemini API Analysis

## Goal
Send condensed video to Gemini and extract structured coding tasks.

## Stories

### E3-S1: Gemini Video Upload
**Points:** 2

Implement video upload to Gemini API.

**Acceptance Criteria:**
- [ ] Upload video file to Gemini Files API
- [ ] Handle large files (chunked upload if needed)
- [ ] Return file reference for prompting
- [ ] Timeout and retry logic
- [ ] Cleanup uploaded files after analysis

**Technical Notes:**
```python
import google.generativeai as genai
file = genai.upload_file(path="video.mp4")
```

---

### E3-S2: Analysis Prompt Engineering
**Points:** 3

Design and implement the analysis prompt.

**Acceptance Criteria:**
- [ ] Prompt extracts: bugs, enhancements, questions
- [ ] Structured output (JSON or Markdown sections)
- [ ] Includes transcription for context
- [ ] Optional: project context injection
- [ ] Prompt versioning for iteration

**Prompt Template:**
```
You are analyzing a screen recording where a user reviews software and comments on bugs and desired changes.

Video: [attached]
Transcription: [from Whisper]
Project Context: [optional README/structure]

Extract:
1. BUGS: Issues the user encountered or mentioned
2. ENHANCEMENTS: Features or changes the user requested
3. QUESTIONS: Unclear items that need clarification

For each item provide:
- Title (short)
- Description (what needs to change)
- Priority (High/Medium/Low based on user emphasis)
- Location hint (if visible in video or mentioned)
- Suggested approach (if obvious)

Output as structured Markdown.
```

---

### E3-S3: Response Parsing
**Points:** 2

Parse Gemini response into structured data.

**Acceptance Criteria:**
- [ ] Parse Markdown sections into objects
- [ ] Handle malformed responses gracefully
- [ ] Validate required fields present
- [ ] Support both JSON and Markdown response formats

---

## Definition of Done
- Full pipeline: video → Gemini → parsed tasks
- Response quality validated on 3+ test videos
- Error handling for API failures
