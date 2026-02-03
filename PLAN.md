# AES_CM Improvement Plan — Phased Implementation

## Current State Summary

The project consists of two Python modules (`main.py` at 428 lines, `gui.py` at 143 lines), a test file (`test_main.py` at 356 lines), two YAML template files, a CI workflow, and packaging via `setup.py` with a minimal `pyproject.toml`. The TODO.md identifies 20 items across five categories: Bugs/Correctness (7), Testing (4), Features (6), Code Quality (4), and CI/CD (2).

The plan below groups all 20 TODO items plus the three living-document maintenance tasks into six phases, ordered by dependency and risk: fix correctness first, improve tooling and quality second, expand test coverage third, add features fourth, harden CI fifth, and finalize documentation last.

## Dependency Graph

```
Phase 0 (documents)
  |
Phase 1 (bugs)         -- no code dependencies on other phases
  |
Phase 2 (code quality) -- depends on Phase 1 (template fix, import fix)
  |
Phase 3 (testing)      -- depends on Phase 2 (logging/type hints make tests cleaner)
  |
Phase 4 (features)     -- depends on Phase 3 (tests guard regressions)
  |
Phase 5 (CI/CD)        -- depends on Phase 4 (all code final before locking CI)
  |
Phase 6 (docs)         -- depends on all above
```

---

## Phase 0: Foundation — Living Documents Setup

**Why first:** Every subsequent phase will reference these documents, so their structure should be established before any code changes begin.

### 0.1 Create `Progress.md`

Create a new file at the project root with this structure:

```
# Progress

## Status
Current phase: Phase 1 — Bug Fixes and Correctness

## Completed
(nothing yet)

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| ...  | ...      | ...       |

## Discovered During Implementation
(new items found while working)
```

**File:** `Progress.md` (new)

### 0.2 Annotate `TODO.md` with phase references

Add a "Phase" column to each TODO item so it is easy to cross-reference which phase an item belongs to.

**File:** `TODO.md`

### Acceptance Criteria
- `Progress.md` exists with the template above.
- `TODO.md` items each have a phase annotation.
- `CLAUDE.md` is unchanged for now.

---

## Phase 1: Bug Fixes and Correctness

**Why first:** Bugs undermine trust in the tool and can cause runtime crashes. Every item here is a defect, not a preference. Fixing them before any refactoring prevents having to fix them twice.

### 1.1 Fix mid-file imports

Move `import argparse` and `from importlib import metadata` from line 193 to the top-level import block in `main.py`.

**File:** `src/program_installer/main.py`

**Acceptance:** `python3 -c "from program_installer import main"` succeeds. All existing tests pass. No import statements exist below line 10.

### 1.2 Fix template parameter discarded in `generate_playbook()`

The `template` argument is accepted but never included in the prompt sent to OpenAI. Append the template content to the prompt when it is not `None`:

```python
if template:
    prompt += f"\nUse the following Ansible playbook as a reference template:\n{template}\n"
```

This goes into the `else` branch (initial generation, not error recovery) of `generate_playbook()`.

**Files:** `src/program_installer/main.py`, `tests/test_main.py` (flip assertion from `assert template not in prompt` to `assert template in prompt`)

**Acceptance:** Both `test_generate_playbook` and `test_generate_playbook_with_error` pass.

### 1.3 Fix relative template paths

`install_programs_and_configure()` opens `template-full.yml` and `ansible_playbook_template.yml` using bare filenames, which breaks when the CLI is run from a different directory.

Fix: move template files into `src/program_installer/templates/` and resolve paths relative to `__file__`. Update `setup.py`/`pyproject.toml` to include `package_data`.

**Files:**
- `src/program_installer/main.py` (add `_PACKAGE_DIR` constant, update path resolution)
- `ansible_playbook_template.yml` → `src/program_installer/templates/`
- `template-full.yml` → `src/program_installer/templates/`
- `setup.py` or `pyproject.toml` (add `package_data`)

**Acceptance:** Running `cd /tmp && program-installer --help` does not crash. Templates are found regardless of working directory. All tests pass.

### 1.4 Fix hardcoded Python version in PATH advice

In `advise_path_update()`, `~/Library/Python/3.13/bin` is hardcoded. Replace with dynamic detection:

```python
python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
```

**File:** `src/program_installer/main.py`

**Acceptance:** PATH advice references the actual running Python version.

### 1.5 Fix GUI tkinter thread safety

`ProgramInstallerGUI.write()` calls `self.output_console.insert()` directly from the install thread. Replace with a `queue.Queue` and poll it from the main thread via `self.after()`.

**File:** `src/program_installer/gui.py`

**Acceptance:** GUI does not raise `RuntimeError` when receiving output from the install thread.

### 1.6 Fix GUI stdout/stderr not restored on close

Save originals before overriding and restore in `destroy()`:

```python
def redirect_output(self):
    self._orig_stdout = sys.stdout
    self._orig_stderr = sys.stderr
    sys.stdout = self
    sys.stderr = self

def destroy(self):
    sys.stdout = self._orig_stdout
    sys.stderr = self._orig_stderr
    super().destroy()
```

**File:** `src/program_installer/gui.py`

**Acceptance:** After closing the GUI window, `sys.stdout` and `sys.stderr` point to the original streams.

### 1.7 Fix placeholder email in `setup.py`

Replace `"your_email@example.com"` with the actual author email, or remove the field.

**File:** `setup.py`

### Phase 1 Document Updates
- `TODO.md`: Mark all 7 Bugs/Correctness items as done.
- `Progress.md`: Log each fix with date and any decisions made.
- `CLAUDE.md`: Update Architecture section to note templates now live in `src/program_installer/templates/`.

---

## Phase 2: Code Quality

**Why second:** Code quality improvements make Phase 3 (testing) and Phase 4 (features) significantly easier. For example, replacing `print()` with `logging` simplifies GUI output redirection. Migrating metadata to `pyproject.toml` must happen before adding linter config there.

### 2.1 Replace `print()` with `logging`

Introduce a module-level logger in `main.py`. Replace all `print()` calls with appropriate log levels. In `gui.py`, add a custom `logging.Handler` that puts messages into the queue from Phase 1.5.

**Files:** `src/program_installer/main.py`, `src/program_installer/gui.py`, `tests/test_main.py` (update `capsys` assertions to use `caplog`)

**Acceptance:** No `print()` calls remain. All tests pass using `caplog`.

### 2.2 Add type hints

Add type annotations to all function signatures. Use `from __future__ import annotations` for Python 3.8 compatibility.

**Files:** `src/program_installer/main.py`, `src/program_installer/gui.py`

**Acceptance:** `mypy src/program_installer/` produces no errors (or only expected stub issues). All tests pass.

### 2.3 Migrate metadata to `pyproject.toml`

Move all metadata from `setup.py` into `pyproject.toml` using the `[project]` table (PEP 621). Delete or stub out `setup.py`.

```toml
[project]
name = "aes-cm"
version = "0.1"
requires-python = ">=3.8"
dependencies = ["python-dotenv", "openai"]

[project.scripts]
program-installer = "program_installer.main:main"
program-installer-gui = "program_installer.gui:main"

[project.optional-dependencies]
dev = ["pytest", "build", "twine", "ruff", "mypy"]
```

**Files:** `pyproject.toml`, `setup.py` (delete or reduce to stub)

**Acceptance:** `pip install -e .` and `pip install -e ".[dev]"` both succeed. Both entry points resolve correctly.

### 2.4 Avoid `shell=True` in `install_homebrew()`

Download the Homebrew install script to a temp file and execute it directly, consistent with how `install_pip()` already works.

**File:** `src/program_installer/main.py`

**Acceptance:** `shell=True` does not appear anywhere in the codebase. Existing test updated to reflect new invocation.

### Phase 2 Document Updates
- `TODO.md`: Mark all 4 Code Quality items as done.
- `Progress.md`: Log the logging strategy, type hint approach, and packaging migration decision.
- `CLAUDE.md`: Update Build commands to reference `pip install -e ".[dev]"`. Note logging approach in Architecture.

---

## Phase 3: Test Coverage Expansion

**Why third:** With bugs fixed and code cleaned up, writing tests against clean code is far more productive. Tests here also serve as regression guards for features in Phase 4.

### 3.1 Add tests for `advise_path_update`

4 test cases covering: directory exists and not in PATH, correct Python version used, directories already in PATH, directories don't exist.

**File:** `tests/test_main.py` (new `TestAdvisePathUpdate` class)

### 3.2 Add tests for `ensure_ansible_installed`

7 test cases covering: already installed, macOS brew path, macOS brew fallback to pip, Linux pip path, unsupported OS, post-install not found.

**File:** `tests/test_main.py` (new `TestEnsureAnsibleInstalled` class)

### 3.3 Add tests for `install_programs_and_configure` edge cases

8 test cases covering: empty list, Linux apt/dnf paths, no package manager, Windows path, playbook self-healing retry, generation returning None, all syntax checks failing.

**File:** `tests/test_main.py` (new `TestInstallProgramsAndConfigure` class)

### 3.4 Add tests for `gui.py`

7 test cases covering: widget creation, toggle_custom_entry, write/queue, redirect/restore stdout, start_installation choices, empty custom input.

**File:** `tests/test_gui.py` (new file)

### Phase 3 Document Updates
- `TODO.md`: Mark all 4 Testing items as done.
- `Progress.md`: Log test counts and coverage numbers.
- `CLAUDE.md`: Update Testing section to note new test files and GUI test skip strategy.

**Acceptance:** ~26 new tests all pass. All major branches covered.

---

## Phase 4: Feature Additions

**Why fourth:** With a stable, well-tested codebase, features can be added confidently.

### 4.1 Add `--gui` flag to CLI entry point

Add `parser.add_argument('--gui', ...)` so `program-installer --gui` launches the GUI.

**Files:** `src/program_installer/main.py`, `tests/test_main.py`

### 4.2 Add `--dry-run` flag

When enabled, log what would be executed without calling `subprocess.check_call`. Thread through to `install_programs_and_configure()` as a parameter. Add a checkbox in the GUI.

**Files:** `src/program_installer/main.py`, `src/program_installer/gui.py`, `tests/test_main.py`

### 4.3 Clean up generated playbook file

Use `try/finally` to delete `ansible_playbook.yml` after execution. Consider using `tempfile` to avoid writing to the current directory.

**File:** `src/program_installer/main.py`

### 4.4 Add progress indication to GUI

Add a `ttk.Progressbar` in indeterminate mode and a status label that updates as phases change.

**File:** `src/program_installer/gui.py`

### 4.5 Support a config file for saved preferences

Add `--config` and `--save-config` flags. Config file at `~/.aes-cm/config.yml` stores program list, choice, and dry_run preference.

**Files:** `src/program_installer/main.py`, `tests/test_main.py`

### 4.6 Offer an alternative to Ansible on Windows (stretch goal)

Generate a PowerShell configuration script via OpenAI instead of just stopping after `choco install`.

**Files:** `src/program_installer/main.py`, `tests/test_main.py`

### Phase 4 Document Updates
- `TODO.md`: Mark all 6 Features items as done.
- `Progress.md`: Log each feature with design decisions.
- `CLAUDE.md`: Document new flags and Windows PowerShell alternative.

---

## Phase 5: CI/CD Hardening

**Why fifth:** With all code changes complete, the CI pipeline can be finalized to lock in quality gates.

### 5.1 Add a linter

Add `ruff` configuration to `pyproject.toml` and a lint step to the CI workflow.

```toml
[tool.ruff]
target-version = "py38"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM"]
```

**Files:** `pyproject.toml`, `.github/workflows/workflow.yml`

### 5.2 Improve GitHub Actions workflow

- Add `macos-latest` to the matrix
- Add Python 3.13 to the matrix
- Add lint step
- Add GUI test skip logic for headless CI
- Update action versions to v4/v5

**File:** `.github/workflows/workflow.yml`

### Phase 5 Document Updates
- `TODO.md`: Mark both CI/CD items as done.
- `Progress.md`: Log CI configuration decisions.
- `CLAUDE.md`: Add CI/CD section.

---

## Phase 6: Final Documentation Pass

**Why last:** With all implementation complete, documentation can accurately reflect the final state.

### 6.1 Final `TODO.md` update
All 20 original items marked done. New items discovered during implementation listed as open.

### 6.2 Final `Progress.md` update
Summary section recapping all phases, total items completed, and any deferred items.

### 6.3 Final `CLAUDE.md` update
Ensure all sections reflect the current architecture, commands, testing, and CI/CD setup.

### 6.4 Update `README.md`
- Document new CLI flags (`--dry-run`, `--gui`, `--config`, `--save-config`)
- Fix virtual environment activation command (backslash vs forward slash)
- Update Python version requirement (3.8+ instead of 3.5+)

**Acceptance:** All documentation accurately reflects the current state of the project.

---

## Total Work Breakdown

| Phase | Items | Scope |
|-------|-------|-------|
| 0 — Documents setup | 2 | Small |
| 1 — Bug fixes | 7 | Medium |
| 2 — Code quality | 4 | Medium-Large |
| 3 — Test coverage | 4 (~26 new tests) | Medium |
| 4 — Features | 6 | Large |
| 5 — CI/CD | 2 | Small |
| 6 — Documentation | 4 | Small |
| **Total** | **29 work items** | |
