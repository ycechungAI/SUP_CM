# TODO

Suggested improvements for AES_CM, organized by priority. Phase annotations reference `PLAN.md`.

## Bugs / Correctness — Phase 1

- [ ] **1.2 Template parameter unused in playbook generation** — `generate_playbook()` accepts a `template` argument but never includes it in the OpenAI prompt. The template content is loaded from file but discarded.
- [ ] **1.3 Relative template paths break when run from another directory** — `ansible_playbook_template.yml` and `template-full.yml` are opened with relative paths in `install_programs_and_configure()`. Running `program-installer` from a different working directory will hit `FileNotFoundError`.
- [ ] **1.4 Hardcoded Python version in PATH advice** — `advise_path_update()` checks `~/Library/Python/3.13/bin` specifically. Should detect the actual Python version dynamically.
- [ ] **1.5 GUI tkinter thread safety** — `ProgramInstallerGUI.write()` calls `self.output_console.insert()` from the install thread. Tkinter widgets are not thread-safe; should use a queue or `after()` to schedule UI updates on the main thread.
- [ ] **1.6 GUI does not restore stdout/stderr on close** — `redirect_output()` replaces `sys.stdout`/`sys.stderr` but never restores them, which can cause issues if the GUI is used as a library.
- [ ] **1.1 Mid-file imports** — `argparse` and `importlib.metadata` are imported at line 193 of `main.py` instead of the top of the file.
- [ ] **1.7 `setup.py` has placeholder email** — `author_email` is set to `"your_email@example.com"`.

## Code Quality — Phase 2

- [ ] **2.1 Replace `print()` calls with `logging`** — All output uses `print()`. A logging framework would allow log levels, file output, and cleaner GUI output redirection.
- [ ] **2.2 Add type hints** — No type annotations exist on any function signatures.
- [ ] **2.3 Migrate metadata from `setup.py` to `pyproject.toml`** — `pyproject.toml` only declares the build system. Project metadata, dependencies, and entry points should move there (modern packaging standard).
- [ ] **2.4 Avoid `shell=True` in `install_homebrew()`** — The Homebrew install uses `subprocess.check_call(cmd, shell=True)`. Consider using a safer subprocess invocation.

## Testing — Phase 3

- [ ] **3.4 Add tests for `gui.py`** — No test coverage exists for the GUI module.
- [ ] **3.3 Add tests for `install_programs_and_configure` edge cases** — No direct unit tests for the Linux/Windows code paths or the playbook self-healing retry loop within this function.
- [ ] **3.2 Add tests for `ensure_ansible_installed`** — Only indirectly tested through the full `main()` integration test.
- [ ] **3.1 Add tests for `advise_path_update`** — No coverage for PATH advisory logic.

## Features — Phase 4

- [ ] **4.2 Add `--dry-run` flag** — Show what would be installed without actually running commands. Useful for reviewing the plan before committing.
- [ ] **4.1 Add `--gui` flag to the CLI entry point** — Allow launching the GUI from `program-installer --gui` instead of requiring a separate `program-installer-gui` command.
- [ ] **4.4 Add progress indication to GUI** — The GUI shows output text but no progress bar or status indicator during installation.
- [ ] **4.5 Support a config file for saved preferences** — Allow users to save their program list and settings (e.g., `~/.aes-cm/config.yml`) so they can replay setups across machines.
- [ ] **4.6 Offer an alternative to Ansible on Windows** — Currently Windows just prints "Cannot generate and run Ansible playbook on Windows" and stops. Consider using PowerShell DSC or a script-based alternative.
- [ ] **4.3 Clean up generated `ansible_playbook.yml`** — The generated playbook is written to the current directory and never removed after execution.

## CI/CD — Phase 5

- [ ] **5.2 Improve GitHub Actions workflow** — Existing workflow could add macOS runner, Python 3.13, lint step, and updated action versions.
- [ ] **5.1 Add a linter** — No linting configuration exists. Consider `ruff` or `flake8`.
