# TODO

Suggested improvements for AES_CM, organized by priority.

## Bugs / Correctness

- [ ] **Template parameter unused in playbook generation** — `generate_playbook()` accepts a `template` argument but never includes it in the OpenAI prompt. The template content is loaded from file but discarded.
- [ ] **Relative template paths break when run from another directory** — `ansible_playbook_template.yml` and `template-full.yml` are opened with relative paths in `install_programs_and_configure()`. Running `program-installer` from a different working directory will hit `FileNotFoundError`.
- [ ] **Hardcoded Python version in PATH advice** — `advise_path_update()` checks `~/Library/Python/3.13/bin` specifically. Should detect the actual Python version dynamically.
- [ ] **GUI tkinter thread safety** — `ProgramInstallerGUI.write()` calls `self.output_console.insert()` from the install thread. Tkinter widgets are not thread-safe; should use a queue or `after()` to schedule UI updates on the main thread.
- [ ] **GUI does not restore stdout/stderr on close** — `redirect_output()` replaces `sys.stdout`/`sys.stderr` but never restores them, which can cause issues if the GUI is used as a library.
- [ ] **Mid-file imports** — `argparse` and `importlib.metadata` are imported at line 193 of `main.py` instead of the top of the file.
- [ ] **`setup.py` has placeholder email** — `author_email` is set to `"your_email@example.com"`.

## Testing

- [ ] **Add tests for `gui.py`** — No test coverage exists for the GUI module.
- [ ] **Add tests for `install_programs_and_configure` edge cases** — No direct unit tests for the Linux/Windows code paths or the playbook self-healing retry loop within this function.
- [ ] **Add tests for `ensure_ansible_installed`** — Only indirectly tested through the full `main()` integration test.
- [ ] **Add tests for `advise_path_update`** — No coverage for PATH advisory logic.

## Features

- [ ] **Add `--dry-run` flag** — Show what would be installed without actually running commands. Useful for reviewing the plan before committing.
- [ ] **Add `--gui` flag to the CLI entry point** — Allow launching the GUI from `program-installer --gui` instead of requiring a separate `program-installer-gui` command.
- [ ] **Add progress indication to GUI** — The GUI shows output text but no progress bar or status indicator during installation.
- [ ] **Support a config file for saved preferences** — Allow users to save their program list and settings (e.g., `~/.aes-cm/config.yml`) so they can replay setups across machines.
- [ ] **Offer an alternative to Ansible on Windows** — Currently Windows just prints "Cannot generate and run Ansible playbook on Windows" and stops. Consider using PowerShell DSC or a script-based alternative.
- [ ] **Clean up generated `ansible_playbook.yml`** — The generated playbook is written to the current directory and never removed after execution.

## Code Quality

- [ ] **Replace `print()` calls with `logging`** — All output uses `print()`. A logging framework would allow log levels, file output, and cleaner GUI output redirection.
- [ ] **Add type hints** — No type annotations exist on any function signatures.
- [ ] **Migrate metadata from `setup.py` to `pyproject.toml`** — `pyproject.toml` only declares the build system. Project metadata, dependencies, and entry points should move there (modern packaging standard).
- [ ] **Avoid `shell=True` in `install_homebrew()`** — The Homebrew install uses `subprocess.check_call(cmd, shell=True)`. Consider using a safer subprocess invocation.

## CI/CD

- [ ] **Add a GitHub Actions workflow** — No CI pipeline is present in the repo. Add automated test runs on push/PR for Linux and macOS.
- [ ] **Add a linter** — No linting configuration exists. Consider `ruff` or `flake8`.
