"""CLI entry point for Screen Feedback Agent."""

import click
from pathlib import Path
from rich.console import Console

console = Console()


@click.group()
@click.version_option()
def main() -> None:
    """Screen Feedback Agent - Convert screen recordings into coding tasks."""
    pass


@main.command()
@click.argument("video", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), help="Output markdown file")
@click.option("-p", "--project", type=click.Path(exists=True, path_type=Path), help="Project directory for context")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
def analyze(video: Path, output: Path | None, project: Path | None, verbose: bool) -> None:
    """Analyze a screen recording and extract coding tasks.
    
    Example:
        sfa analyze recording.mp4 -o tasks.md
        sfa analyze recording.mp4 --project ~/repos/my-app
    """
    from .pipeline import run_pipeline
    
    console.print(f"[bold blue]🎬 Analyzing:[/] {video.name}")
    
    if project:
        console.print(f"[dim]Project context:[/] {project}")
    
    result = run_pipeline(
        video_path=video,
        project_path=project,
        verbose=verbose,
    )
    
    output_path = output or video.with_suffix(".tasks.md")
    output_path.write_text(result.markdown)
    
    console.print(f"\n[bold green]✅ Analysis complete![/]")
    console.print(f"[dim]Output:[/] {output_path}")
    console.print(f"\n[bold]Summary:[/]")
    console.print(f"  🐛 Bugs: {result.bug_count}")
    console.print(f"  ✨ Enhancements: {result.enhancement_count}")
    console.print(f"  ❓ Questions: {result.question_count}")


@main.command()
@click.argument("key")
@click.argument("value")
def config(key: str, value: str) -> None:
    """Set configuration values.
    
    Example:
        sfa config gemini_api_key sk-xxx
    """
    from .config import set_config
    set_config(key, value)
    console.print(f"[green]✓[/] Set {key}")


if __name__ == "__main__":
    main()
