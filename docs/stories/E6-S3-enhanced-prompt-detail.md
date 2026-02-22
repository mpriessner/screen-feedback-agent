# Story E6-S3: Enhanced Prompt for Detailed Analysis

## Header
- **Story ID:** E6-S3
- **Title:** Enhanced Prompt Engineering for Precise Output
- **Epic:** E6 - Enhanced Analysis Pipeline
- **Status:** TODO
- **Points:** 2
- **Dependencies:** E6-S2 (Snapshots for context)

## Overview
Current Gemini analysis is too high-level and generic. We need prompts that produce extremely specific, actionable coding tasks with exact UI locations, file paths, and implementation details.

**Why this matters:** A coding agent needs precise instructions, not vague "add a button" descriptions. The output should be copy-paste ready for Claude Code or similar.

## Acceptance Criteria
- [ ] Output includes specific CSS selectors or component names
- [ ] Output references exact UI coordinates when possible
- [ ] Each task has code snippets showing expected changes
- [ ] Tasks reference specific files to modify
- [ ] Output formatted as ready-to-execute agent prompts

## Technical Specification

### Enhanced Prompt Template
```python
ENHANCED_ANALYSIS_PROMPT = """
You are a senior software engineer analyzing a screen recording to extract 
PRECISE coding tasks. The user is reviewing an application and describing 
bugs or desired features.

## Video Context
{video_description}

## Transcription with Timestamps
{timestamped_transcription}

## Screenshots (when user said "snap")
{snapshot_descriptions}

## Analysis Instructions

For EACH issue or feature request, provide:

### 1. EXACT LOCATION
- UI element name (button text, menu item, icon type)
- Position on screen (top-left, sidebar, header, etc.)
- Screenshot reference if available ("See snapshot at 12.3s")

### 2. CURRENT STATE
- What the UI looks like NOW
- What happens when interacting with it
- Any visible text/labels

### 3. DESIRED STATE
- Exactly what should change
- Expected behavior after fix
- Visual mockup description if needed

### 4. IMPLEMENTATION SPEC
```
File: [exact file path if known, or likely location]
Component: [component name]
Changes:
- Line X: Change Y to Z
- Add new function: [signature]
- CSS: [specific style changes]
```

### 5. ACCEPTANCE TEST
```
GIVEN [precondition]
WHEN [action]
THEN [expected result]
```

### 6. AGENT PROMPT
Write a complete prompt that could be given to Claude Code to implement this:
```
[Ready-to-use prompt for coding agent]
```

---

## Output Format

Respond with a markdown document containing each task in the format above.
Be EXTREMELY specific. Vague descriptions are useless.

Examples of BAD output:
- "Add a settings menu" ❌
- "Make the sidebar collapsible" ❌

Examples of GOOD output:
- "Add dropdown menu to '.workspace-header' div, triggered by clicking the workspace name. Menu items: 'Settings' (links to /settings), 'Account' (shows email), 'Logout' (calls auth.signOut())" ✅
- "Add collapse button to '#sidebar-container', position: absolute top-right. On click: animate width from 240px to 48px, show hamburger icon, persist state to localStorage key 'sidebar-collapsed'" ✅
"""
```

### Timestamped Transcription Format
```python
def format_timestamped_transcription(segments: list[SpeechSegment]) -> str:
    """Format transcription with timestamps for context."""
    lines = []
    for seg in segments:
        timestamp = f"[{seg.start:.1f}s - {seg.end:.1f}s]"
        lines.append(f"{timestamp} {seg.text}")
    return "\n".join(lines)
```

### Snapshot Description Format
```python
def format_snapshot_descriptions(snapshots: list[Snapshot]) -> str:
    """Describe snapshots for text context."""
    if not snapshots:
        return "No snapshots captured."
    
    lines = ["User captured the following screenshots by saying 'snap':"]
    for i, snap in enumerate(snapshots, 1):
        lines.append(f"\n**Snapshot {i}** (at {snap.timestamp:.1f}s)")
        lines.append(f"Context: \"{snap.context}\"")
        lines.append(f"[Image {i} attached below]")
    
    return "\n".join(lines)
```

## Implementation Steps
1. Update `ANALYSIS_PROMPT` in `gemini.py`
2. Add timestamped transcription formatting
3. Add snapshot description formatting  
4. Update prompt builder to combine all elements
5. Test with sample videos
6. Iterate on prompt based on output quality

## Testing Requirements

### Quality Tests (Manual)
```python
def test_output_specificity():
    """Output contains specific selectors, not vague descriptions."""
    result = analyze_test_video()
    
    # Should contain CSS-like selectors
    assert any(c in result for c in ['.', '#', 'className'])
    
    # Should contain file paths
    assert 'src/' in result or 'components/' in result
    
    # Should NOT contain vague phrases
    vague_phrases = ['add a button', 'make it work', 'fix the issue']
    for phrase in vague_phrases:
        assert phrase.lower() not in result.lower()
```

## Example Usage
```python
# Generate detailed analysis
prompt = build_enhanced_prompt(
    video_path=condensed_video,
    segments=speech_segments,
    snapshots=snap_screenshots,
)

response = model.generate_content(prompt)
# Response now contains copy-paste ready agent prompts
```

## Example Output
```markdown
## Task 1: Workspace Settings Dropdown

### EXACT LOCATION
- Element: Workspace name text "SciSymbioAI" in sidebar header
- Position: Top-left, first element in sidebar
- Snapshot: See snapshot at 5.2s showing the header area

### CURRENT STATE
- Static text displaying workspace name
- No click interaction
- No dropdown or menu visible

### DESIRED STATE
- Clicking workspace name opens dropdown menu
- Menu contains: Settings, Account Info, Logout
- Dropdown appears below the text, aligned left

### IMPLEMENTATION SPEC
```
File: src/components/Sidebar/WorkspaceHeader.tsx
Component: WorkspaceHeader

Changes:
- Wrap workspace name in <DropdownTrigger>
- Add <DropdownMenu> with items:
  - Settings → navigate('/settings')
  - Account → show modal with user.email
  - Logout → supabase.auth.signOut()
```

### ACCEPTANCE TEST
```
GIVEN user is logged in and viewing sidebar
WHEN user clicks on workspace name "SciSymbioAI"
THEN dropdown menu appears with Settings, Account, Logout options
```

### AGENT PROMPT
```
Implement a dropdown menu for the workspace header in the sidebar.

File: src/components/Sidebar/WorkspaceHeader.tsx

Requirements:
1. Make the workspace name clickable
2. On click, show a dropdown with 3 items:
   - "Settings" - navigates to /settings
   - "Account" - shows modal with current user email
   - "Logout" - calls supabase.auth.signOut() and redirects to /login

Use the existing DropdownMenu component from @/components/ui/dropdown-menu.
Match the styling of other dropdowns in the app.
```
```
