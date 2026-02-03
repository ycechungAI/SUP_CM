# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AES_CM (Automated Environment Setup Configuration Manager) is a cross-platform tool that automates development environment setup on macOS, Linux, and Windows. It installs software via native package managers (Homebrew, Chocolatey, apt/dnf/yum/pacman) and generates Ansible playbooks using the OpenAI API for complex configurations.

Package name: `aes-cm`. Two entry points: `program-installer` (CLI) and `program-installer-gui` (Tkinter GUI).

## Build and Development Commands

```bash
# Install in editable mode for development
pip3 install -e .

# Install dev dependencies
pip3 install -r requirements.txt

# Run CLI
program-installer

# Run GUI
program-installer-gui

# Run all tests
python3 -m pytest

# Run a single test
python3 -m pytest tests/test_main.py::TestClassName::test_method_name

# Build for distribution
python3 -m build
```

Requires a `.env` file in the project root with `OPENAI_API_KEY=<key>` for runtime operation. The OpenAI client is configured to use `https://api.aimlapi.com/v1` as the base URL.

## Architecture

All source code lives in `src/program_installer/`. There are two modules:

- **`main.py`** — CLI entry point and all core logic. Contains OS detection, package manager interactions, program list definitions (`BASIC_PROGRAMS`, `DEVELOPER_PROGRAMS` with per-platform variants), dependency management (pip, Homebrew, Chocolatey), Ansible playbook generation via OpenAI, and playbook validation/execution.
- **`gui.py`** — Tkinter GUI that wraps the same core logic. Redirects stdout/stderr to a scrolled text widget and runs installation in a background thread.

Both interfaces share `install_programs_and_configure()` from `main.py` as the core orchestration function. This function:
1. Detects OS and selects the appropriate package manager
2. Installs selected programs via native package manager subprocess calls
3. On macOS/Linux: generates an Ansible playbook via OpenAI, validates syntax, self-heals on failure, then executes it

Playbook generation uses model fallback (`gpt-4o-mini` primary, `gpt-5-2025-08-07` fallback) with 3 retries per model and exponential backoff.

## Testing

Tests are in `tests/test_main.py` using pytest with `unittest.mock`. All system calls and API interactions are mocked — no real installations or API calls occur during testing. Tests cover dependency checks, package installation, package manager installation, playbook generation (including error recovery and model fallback), user input handling, and full CLI workflow integration.
