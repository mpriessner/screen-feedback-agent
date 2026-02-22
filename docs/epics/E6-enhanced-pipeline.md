# EPIC 6: Enhanced Analysis Pipeline

## Goal
Improve video processing and analysis to produce precise, actionable coding prompts.

Based on user feedback from initial testing:
1. Video not properly condensed (clicks counted as speech)
2. Analysis too high-level (needs specific UI details)
3. Need "snap" keyword to capture exact UI moments

## Stories

- [E6-S1: Improved Speech Detection](../stories/E6-S1-improved-speech-detection.md) — 3 points
- [E6-S2: Snap Keyword Screenshots](../stories/E6-S2-snap-keyword-screenshots.md) — 3 points
- [E6-S3: Enhanced Prompt Detail](../stories/E6-S3-enhanced-prompt-detail.md) — 2 points

**Total: 8 points**

## User Flow (After Implementation)

1. User records screen while talking
2. Says "snap" when pointing at specific UI element
3. Uploads video to tool
4. Tool:
   - Extracts only speech segments (ignores clicks)
   - Finds "snap" keywords, extracts frames
   - Sends condensed video + frames to Gemini
   - Returns precise, copy-paste-ready agent prompts

## Definition of Done
- Speech detection ignores mechanical sounds
- "snap" keyword triggers frame extraction
- Output contains specific selectors, file paths, code snippets
- Output can be directly fed to Claude Code
