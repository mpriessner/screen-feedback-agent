"""Output generation for analysis results."""

from datetime import datetime
from .gemini import AnalysisOutput, Task


def generate_markdown(analysis: AnalysisOutput, transcription: str) -> str:
    """Generate formatted Markdown output.
    
    Args:
        analysis: Structured analysis from Gemini
        transcription: Full transcription text
        
    Returns:
        Formatted Markdown string
    """
    lines = [
        "# 🎬 Screen Feedback Analysis",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "---",
        "",
        "## 📋 Summary",
        analysis.summary,
        "",
    ]
    
    # Bugs section
    if analysis.bugs:
        lines.extend([
            f"## 🐛 Bugs ({len(analysis.bugs)})",
            "",
        ])
        for i, bug in enumerate(analysis.bugs, 1):
            lines.extend(format_task(i, bug))
    
    # Enhancements section
    if analysis.enhancements:
        lines.extend([
            f"## ✨ Enhancements ({len(analysis.enhancements)})",
            "",
        ])
        for i, enh in enumerate(analysis.enhancements, 1):
            lines.extend(format_task(i, enh))
    
    # Questions section
    if analysis.questions:
        lines.extend([
            f"## ❓ Questions ({len(analysis.questions)})",
            "",
        ])
        for i, q in enumerate(analysis.questions, 1):
            lines.extend(format_task(i, q))
    
    # Transcription
    if transcription:
        lines.extend([
            "---",
            "",
            "## 📝 Full Transcription",
            "",
            "```",
            transcription,
            "```",
            "",
        ])
    
    return "\n".join(lines)


def format_task(index: int, task: Task) -> list[str]:
    """Format a single task as Markdown."""
    lines = [
        f"### {index}. {task.title} — Priority: {task.priority}",
        "",
        f"**Description:** {task.description}",
        "",
    ]
    
    if task.location:
        lines.append(f"**Location:** `{task.location}`")
        lines.append("")
    
    if task.suggested_fix:
        lines.append(f"**Suggested Fix:** {task.suggested_fix}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    return lines


def format_chat_summary(analysis: AnalysisOutput, video_duration: float) -> str:
    """Format condensed summary for chat contexts (WhatsApp).
    
    Args:
        analysis: Structured analysis
        video_duration: Original video duration in seconds
        
    Returns:
        Short formatted string for chat
    """
    duration_str = f"{int(video_duration // 60)}:{int(video_duration % 60):02d}"
    
    lines = [
        f"🎬 Analyzed {duration_str} of screen recording",
        "",
        "Found:",
    ]
    
    bug_count = len(analysis.bugs)
    enh_count = len(analysis.enhancements)
    q_count = len(analysis.questions)
    
    high_priority = sum(1 for b in analysis.bugs if b.priority == "High")
    
    if bug_count:
        hp_str = f" ({high_priority} high priority)" if high_priority else ""
        lines.append(f"🐛 {bug_count} bugs{hp_str}")
    
    if enh_count:
        lines.append(f"✨ {enh_count} enhancement requests")
    
    if q_count:
        lines.append(f"❓ {q_count} questions")
    
    if not (bug_count or enh_count or q_count):
        lines.append("✅ No issues found!")
    
    # Top priority item
    if analysis.bugs:
        top = next((b for b in analysis.bugs if b.priority == "High"), analysis.bugs[0])
        lines.extend([
            "",
            "Top priority:",
            f"• {top.title} [{top.priority.upper()}]",
        ])
    
    lines.extend([
        "",
        'Reply "full report" for complete analysis.',
    ])
    
    return "\n".join(lines)
