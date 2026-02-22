# E4-S1: CLI Framework

| Field        | Value                                  |
|--------------|----------------------------------------|
| **Story ID** | E4-S1                                  |
| **Title**    | CLI Framework                          |
| **Epic**     | E4 — CLI & Output Generation           |
| **Status**   | TODO                                   |
| **Points**   | 2                                      |
| **Dependencies** | None (can be developed in parallel with E1-E3) |

---

## Overview

Set up the complete CLI interface using Click with Rich for terminal formatting. The CLI is the primary user entry point — it exposes the `sfa analyze` command for processing videos and `sfa config` for managing API keys and settings.

This story provides the user-facing shell around all backend functionality. It can be developed in parallel with the processing pipeline since it depends only on the `run_pipeline()` interface.

---

## Acceptance Criteria

- [ ] `sfa analyze <video>` command processes a video file and outputs results
- [ ] `sfa analyze` options: `--output` / `-o`, `--project` / `-p`, `--verbose` / `-v`, `--model`, `--prompt-version`
- [ ] `sfa config set <key> <value>` stores configuration persistently
- [ ] `sfa config get <key>` retrieves a configuration value
- [ ] `sfa config list` shows all configuration
- [ ] Configuration stored in `~/.config/sfa/config.yaml`
- [ ] `GEMINI_API_KEY` environment variable is respected (overrides config file)
- [ ] `sfa --version` shows the current version
- [ ] `sfa --help` shows usage with examples
- [ ] Clear error messages for: missing video file, missing API key, invalid file format
- [ ] Supports video file extensions: `.mp4`, `.mov`, `.webm`, `.mkv`, `.avi`
- [ ] Exit codes: 0 = success, 1 = user error, 2 = processing error
- [ ] Unit tests for CLI argument parsing and config management

---

## Technical Specification

### Files to Modify

- `src/screen_feedback_agent/cli.py` — expand existing CLI with config subcommands and validation
- `src/screen_feedback_agent/config.py` — add `get_config_value()` and `list_config()`

### Function Signatures

#### cli.py

```python
@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Screen Feedback Agent — Convert screen recordings into coding tasks."""

@main.command()
@click.argument("video", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), help="Output markdown file")
@click.option("-p", "--project", type=click.Path(exists=True, path_type=Path), help="Project directory for context")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("--model", default="gemini-2.0-flash", help="Gemini model name")
@click.option("--prompt-version", default="v1", help="Prompt version to use")
def analyze(video: Path, output: Path | None, project: Path | None,
            verbose: bool, model: str, prompt_version: str) -> None:
    """Analyze a screen recording and extract coding tasks."""

@main.group()
def config() -> None:
    """Manage configuration."""

@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value."""

@config.command("get")
@click.argument("key")
def config_get(key: str) -> None:
    """Get a configuration value."""

@config.command("list")
def config_list() -> None:
    """List all configuration values."""
```

#### config.py additions

```python
def get_config_value(key: str) -> str | None:
    """Get a single configuration value."""

def list_config() -> dict:
    """Return all configuration key-value pairs."""

VALID_CONFIG_KEYS = {
    "gemini_api_key": "Gemini API key for video analysis",
    "default_model": "Default Gemini model name",
    "default_prompt_version": "Default prompt version",
    "silence_threshold": "Silence detection threshold in dB",
    "padding": "Segment padding in seconds",
}
```

### External Dependencies

- `click>=8.0` (already in pyproject.toml)
- `rich>=13.0` (already in pyproject.toml)

---

## Implementation Steps

1. **Expand `config.py`**:
   a. Add `get_config_value(key)` that returns a single value.
   b. Add `list_config()` that returns the full dict.
   c. Add `VALID_CONFIG_KEYS` dict for help text and validation.
2. **Restructure CLI in `cli.py`**:
   a. Convert `config` from a command to a `@click.group()`.
   b. Add `config set`, `config get`, `config list` subcommands.
   c. Display results with Rich formatting.
3. **Enhance `analyze` command**:
   a. Add `--model` and `--prompt-version` options.
   b. Validate video file extension against supported list.
   c. Check for API key before processing; show helpful error if missing.
   d. Wrap `run_pipeline()` call in try/except for clean error display.
   e. Set appropriate exit codes.
4. **Add Rich formatting**:
   a. Use `rich.console.Console` for all output.
   b. Use `rich.panel.Panel` for summary display.
   c. Use `rich.table.Table` for config list.
5. **Add help text with examples** — use Click's `epilog` parameter for command examples.

### Edge Cases

- **Video file doesn't exist** — Click handles this via `exists=True`, shows error.
- **Unsupported video format** — validate extension, show supported formats list.
- **Config directory doesn't exist** — `set_config()` creates it via `mkdir(parents=True)`.
- **Config file is corrupted YAML** — catch `yaml.YAMLError`, show error, suggest deleting file.
- **No API key anywhere** — check before pipeline starts, show instructions for setting it.
- **Pipeline raises unexpected error** — catch, print with `rich.traceback` in verbose mode, clean message otherwise.

---

## Testing Requirements

### Unit Tests — `tests/test_cli.py`

```python
from click.testing import CliRunner

def test_cli_version():
    """--version shows version string."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert "0.1.0" in result.output

def test_cli_help():
    """--help shows usage information."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert "Screen Feedback Agent" in result.output

def test_analyze_missing_video():
    """Analyze with nonexistent video shows error."""
    runner = CliRunner()
    result = runner.invoke(main, ["analyze", "nonexistent.mp4"])
    assert result.exit_code != 0

def test_analyze_unsupported_format(tmp_path):
    """Analyze with unsupported file extension shows error."""
    bad_file = tmp_path / "test.txt"
    bad_file.touch()
    runner = CliRunner()
    result = runner.invoke(main, ["analyze", str(bad_file)])
    assert result.exit_code != 0

def test_config_set_and_get(tmp_path, monkeypatch):
    """Config set stores value that config get retrieves."""
    monkeypatch.setattr("screen_feedback_agent.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("screen_feedback_agent.config.CONFIG_FILE", tmp_path / "config.yaml")
    runner = CliRunner()
    runner.invoke(main, ["config", "set", "gemini_api_key", "test-key"])
    result = runner.invoke(main, ["config", "get", "gemini_api_key"])
    assert "test-key" in result.output

def test_config_list(tmp_path, monkeypatch):
    """Config list shows all stored values."""
    monkeypatch.setattr("screen_feedback_agent.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("screen_feedback_agent.config.CONFIG_FILE", tmp_path / "config.yaml")
    runner = CliRunner()
    runner.invoke(main, ["config", "set", "gemini_api_key", "test-key"])
    result = runner.invoke(main, ["config", "list"])
    assert "gemini_api_key" in result.output

def test_config_get_missing_key():
    """Config get for unknown key shows appropriate message."""

def test_analyze_no_api_key(tmp_path, monkeypatch):
    """Analyze without API key shows helpful error."""
```

---

## Example Usage

```bash
# Basic analysis
sfa analyze recording.mp4

# Custom output path and project context
sfa analyze recording.mp4 -o tasks.md --project ~/repos/my-app

# Verbose mode with custom model
sfa analyze recording.mp4 -v --model gemini-2.0-pro

# Configuration
sfa config set gemini_api_key sk-xxxxx
sfa config get gemini_api_key
sfa config list

# Version and help
sfa --version
sfa analyze --help
```
