#!/usr/bin/env python3

import sys
import subprocess
import platform
import os
import urllib.request
import shutil

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None

# Universal program lists
UNIVERSAL_BASIC_PROGRAMS = sorted(list(set([
    "vlc", "docker", "git", "vscode", "chrome"
])))

UNIVERSAL_DEVELOPER_PROGRAMS = sorted(list(set([
    "git", "docker", "vscode", "postman", "dbeaver", "libreoffice",
    "slack", "vlc", "gimp", "spotify", "adobe-reader"
])))

def check_pip():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"])
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False

def install_pip():
    print("Pip not found. Installing pip...")
    get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
    get_pip_path = "get-pip.py"
    urllib.request.urlretrieve(get_pip_url, get_pip_path)
    subprocess.check_call([sys.executable, get_pip_path, "--user"])
    os.remove(get_pip_path)
    print("Pip installed successfully.")

def _run_pip_install(package):
    """Constructs and runs a pip install command, handling virtual environments."""
    command = [sys.executable, "-m", "pip", "install", package]

    # Check for virtual environment
    in_venv = os.getenv('VIRTUAL_ENV') or (hasattr(sys, 'real_prefix')) or (sys.prefix != sys.base_prefix)

    # If not in a virtual environment, install to user site-packages
    if not in_venv:
        command.insert(4, "--user")

    subprocess.check_call(command)

def install_package(package):
    print(f"Installing {package}...")
    _run_pip_install(package)
    print(f"{package} installed successfully.")

def command_exists(cmd):
    return shutil.which(cmd) is not None

def install_homebrew():
    print("Installing Homebrew...")
    install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    subprocess.check_call(install_cmd, shell=True)
    print("Homebrew installed.")

def install_chocolatey():
    choco_path = os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "chocolatey")
    if os.path.isdir(choco_path):
        print("Warning: An existing Chocolatey directory was found.")
        print(f"If the 'choco' command is not working, your installation may be broken or your PATH may not be configured correctly.")
        print("Please inspect the contents of the directory below and consider reinstalling Chocolatey manually.")
        print(f"Directory: {choco_path}")
        print("To attempt a manual re-installation, you may need to delete this directory first.")
        sys.exit(1)

    print("Installing Chocolatey...")
    install_cmd = (
        "Set-ExecutionPolicy Bypass -Scope Process -Force; "
        "[System.Net.ServicePointManager]::SecurityProtocol = "
        "[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
        "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    )
    subprocess.check_call(["powershell.exe", "-Command", install_cmd])
    os.environ["Path"] += os.pathsep + os.path.join(choco_path, "bin")
    print("Chocolatey installed.")

def generate_playbook(client, programs, is_local=True, error=None, previous_content=None):
    os_name = platform.system().lower()
    if error:
        if is_local:
            prompt = (
                f"Fix this Ansible playbook YAML for a local {os_name} environment based on the following error: {error}\n"
                f"Previous playbook:\n{previous_content}\n"
                f"The playbook should target `hosts: localhost` with `connection: local` and install the following programs: {', '.join(programs)}. "
                f"For each program installation task, add 'ignore_errors: true'. "
                f"Do not include anything but the complete program and no text before or after answering this prompt and get rid of ''' before and after"
            )
        else:
            prompt = (
                f"Fix this universal Ansible playbook YAML based on the following error: {error}\n"
                f"Previous playbook:\n{previous_content}\n"
                f"The playbook should be a universal playbook for `hosts: all` that installs the following programs on multiple OS families (Debian, RedHat, Darwin) using Ansible facts and 'when' conditions: {', '.join(programs)}. "
                f"For each program installation task, make sure to add 'ignore_errors: true'. "
                f"Do not include anything but the complete program and no text before or after answering this prompt and get rid of ''' before and after"
            )
    else:
        if is_local:
            prompt = (
                f"Create an Ansible playbook for a local {os_name} environment.\n"
                "The playbook must:\n"
                "1. Target `hosts: localhost`.\n"
                "2. Use `connection: local`.\n"
                f"3. Install the following programs: {', '.join(programs)}.\n"
                "4. Use the appropriate Ansible module for the {os_name} OS (e.g., `apt` for Debian/Ubuntu, `homebrew` for macOS).\n"
                "5. Use 'ignore_errors: true' for each package installation task.\n"
                "6. The playbook should be complete, valid YAML. Do not include any text or explanations before or after the playbook code itself."
            )
        else:
            prompt = (
                "Create a universal Ansible playbook to install a list of required programs on multiple operating systems.\n\n"
                "The playbook must:\n"
                "1. Target all hosts in the inventory (`hosts: all`).\n"
                "2. Gather facts to determine the OS of each host.\n"
                "3. Use 'when' conditions with Ansible facts (e.g., `ansible_os_family`) to create separate tasks for each OS family (e.g., Debian, RedHat, Darwin).\n"
                f"4. For each OS, install the following programs: {', '.join(programs)}.\n"
                "5. Handle potential differences in package names across operating systems.\n"
                "6. Use 'ignore_errors: true' for each package installation task.\n"
                "7. The playbook should be complete, valid YAML. Do not include any text or explanations before or after the playbook code itself."
            )

    import time

    # --- Primary API attempts ---
    models_to_try = ["gpt-4o-mini", "gpt-5-2025-08-07"]
    max_retries_per_model = 3
    initial_sleep_duration = 7
    increment = 5

    for model in models_to_try:
        sleep_duration = initial_sleep_duration
        print(f"Attempting to generate playbook with model: {model}")
        for i in range(max_retries_per_model):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.choices[0].message.content
                if content and content.strip():
                    print(f"Successfully generated playbook with model: {model}")
                    return content
                else:
                    print(f"Warning: Model {model} returned empty content. Retrying after {sleep_duration} seconds...")
                    time.sleep(sleep_duration)
                    sleep_duration += increment
            except Exception as e:
                print(f"An error occurred with model {model}: {e}. Retrying after {sleep_duration} seconds...")
                time.sleep(sleep_duration)
                sleep_duration += increment

    # --- OpenRouter Fallback ---
    print("\nAll models on the primary API failed. Trying fallback with OpenRouter...")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if not openrouter_key:
        print("Warning: OPENROUTER_API_KEY not set. Skipping fallback.")
        return None

    try:
        openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        )

        model = "gpt5-mini"
        sleep_duration = initial_sleep_duration
        print(f"Attempting to generate playbook with fallback model: {model}")
        for i in range(max_retries_per_model):
            try:
                response = openrouter_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.choices[0].message.content
                if content and content.strip():
                    print(f"Successfully generated playbook with fallback model: {model}")
                    return content
                else:
                    print(f"Warning: Fallback model {model} returned empty content. Retrying after {sleep_duration} seconds...")
                    time.sleep(sleep_duration)
                    sleep_duration += increment
            except Exception as e:
                print(f"An error occurred with fallback model {model}: {e}. Retrying after {sleep_duration} seconds...")
                time.sleep(sleep_duration)
                sleep_duration += increment
    except Exception as e:
        print(f"Failed to initialize or use OpenRouter client: {e}")
        return None

    print("Failed to generate playbook with all models and fallbacks.")
    return None

def advise_path_update():
    local_bins = [os.path.expanduser("~/.local/bin"), os.path.expanduser("~/Library/Python/3.13/bin")]
    paths_to_add = [p for p in local_bins if os.path.isdir(p) and p not in os.environ["PATH"]]
    if paths_to_add:
        print("\n*** Important: To use Ansible from the command line, add the following to your shell profile (~/.zshrc or ~/.bash_profile):")
        export_line = 'export PATH="' + ':'.join(paths_to_add) + ':$PATH"'
        print(export_line)
        print("Then restart your terminal or run `source ~/.zshrc` (or your shell config file). ***\n")

def ensure_ansible_installed():
    # Check if ansible-playbook is available, otherwise install and set PATH
    if command_exists("ansible-playbook"):
        print("Ansible is already installed.")
        return

    print("Ansible not found. Installing Ansible...")

    os_name = platform.system().lower()
    try:
        if os_name == "darwin":
            if not command_exists("brew"):
                install_homebrew()
            try:
                subprocess.check_call(["brew", "install", "ansible"])
            except subprocess.CalledProcessError:
                print("Homebrew install failed, trying pip install...")
                _run_pip_install("ansible")
                advise_path_update()
        elif os_name == "linux":
            print("Installing Ansible with pip...")
            _run_pip_install("ansible")
            advise_path_update()
        else:
            print("Automatic Ansible install not supported for this OS.")
            sys.exit(1)
    except Exception as e:
        print(f"Ansible installation failed: {e}")
        sys.exit(1)

    if not command_exists("ansible-playbook"):
        print("Ansible installation failed or ansible-playbook still not in PATH. Please check your setup.")
        sys.exit(1)
    print("Ansible installed successfully.")

def get_program_list():
    while True:
        choice = input(
            "Choose an option:\n"
            "a. Install a basic list of applications.\n"
            "b. Install a full developer list of applications.\n"
            "c. Enter a custom list of programs.\n"
            "Your choice: "
        ).lower()

        if choice == 'a':
            return choice, UNIVERSAL_BASIC_PROGRAMS
        elif choice == 'b':
            return choice, UNIVERSAL_DEVELOPER_PROGRAMS
        elif choice == 'c':
            programs_input = input("Enter the list of programs to install, separated by commas: ").strip()
            return choice, [p.strip() for p in programs_input.split(',') if p.strip()]
        else:
            print("Invalid choice. Please enter 'a', 'b', or 'c'.")

import argparse
from importlib import metadata

def main():
    try:
        version = metadata.version("aes-cm")
    except metadata.PackageNotFoundError:
        version = "0.1"  # Fallback for local development

    parser = argparse.ArgumentParser(
        prog="program-installer",
        description="A tool to automate the setup of a development environment on macOS, Linux, and Windows."
    )
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {version}'
    )
    parser.add_argument(
        '-i', '--inventory',
        type=str,
        help='Path to the Ansible inventory file.'
    )
    args = parser.parse_args()

    os_name = platform.system().lower()

    if os_name not in ("linux", "darwin", "windows"):
        print(f"Unsupported operating system: {os_name}")
        return

    if not check_pip():
        install_pip()

    install_package("python-dotenv")
    install_package("openai")

    if load_dotenv is None:
        raise ModuleNotFoundError("python-dotenv is required. Please install it before running.")
    if OpenAI is None:
        raise ModuleNotFoundError("openai is required. Please install it before running.")

    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    client = OpenAI(
        base_url="https://api.aimlapi.com/v1",
        api_key=api_key,
    )

    if os_name in ("linux", "darwin"):
        ensure_ansible_installed()
        print("\nInstallation complete. You can now use Ansible.")
        print("Note: Ansible requires Python 3.5+ and may need additional system dependencies like SSH on Linux.")
        print("For full functionality, ensure you have the necessary prerequisites installed.")
    else:  # windows
        print("Ansible does not support Windows as a control machine natively.")
        print("Skipping Ansible installation. Proceeding with program installation if applicable.")

    # The os_name is no longer needed for program list selection.
    # The debug prints are removed as the issue is resolved.
    choice, programs = get_program_list()

    if not programs:
        print("No programs specified.")
        return

    # The direct installation logic that was previously here has been removed.
    # All package installation is now handled by the universal Ansible playbook
    # to support multi-OS remote machine setups.

    if os_name not in ("linux", "darwin"):
        print("Cannot generate and run Ansible playbook on Windows.")
        return

    print("Generating Ansible playbook...")

    is_local_run = not args.inventory
    playbook_content = generate_playbook(client, programs, is_local=is_local_run)

    if not playbook_content or not playbook_content.strip():
        print("Error: Generated playbook content is empty. Aborting.")
        return

    playbook_file = 'ansible_playbook.yml'
    with open(playbook_file, 'w') as f:
        f.write(playbook_content)
    print("Generated playbook:")
    print("===================")
    print(playbook_content)
    print("===================")

    # Build the syntax check command, including inventory if provided
    syntax_check_cmd = ['ansible-playbook', playbook_file, '--syntax-check', '-v']
    if args.inventory:
        syntax_check_cmd.extend(['-i', args.inventory])

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            print(f"Attempt {attempt + 1}: Checking playbook syntax...")
            output = subprocess.check_output(
                syntax_check_cmd,
                stderr=subprocess.STDOUT
            ).decode('utf-8')
            print("Syntax check output:")
            print(output)
            print("Syntax check passed.")
            break
        except subprocess.CalledProcessError as e:
            error_msg = e.output.decode('utf-8')
            print("Syntax check failed:")
            print(error_msg)

            # Try to fix by stripping markdown fences
            stripped_content = playbook_content.strip()
            if stripped_content.startswith('```yaml') and stripped_content.endswith('```'):
                print("Detected YAML code block fences. Removing them and retrying syntax check.")
                # Compatibility for Python < 3.9
                content = stripped_content
                if content.startswith('```yaml'):
                    content = content[len('```yaml'):]
                if content.endswith('```'):
                    content = content[:-len('```')]
                playbook_content = content.strip()
                with open(playbook_file, 'w') as f:
                    f.write(playbook_content)
                continue

            if attempt < max_attempts - 1:
                print("Attempting to fix the playbook by regenerating...")
                playbook_content = generate_playbook(client, programs, is_local=is_local_run, error=error_msg, previous_content=playbook_content)
                with open(playbook_file, 'w') as f:
                    f.write(playbook_content)
                print("Updated playbook:")
                print(playbook_content)
            else:
                print("Failed to fix playbook after maximum attempts.")
                return

    # Run the playbook
    try:
        print("Running the playbook...")
        run_cmd = ['ansible-playbook', playbook_file, '-v']
        if args.inventory:
            run_cmd.extend(['-i', args.inventory])
        subprocess.check_call(run_cmd)
        print("Playbook executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running playbook: {e}")
    except Exception as e:
        print(f"Unexpected error running playbook: {e}")

if __name__ == "__main__":
    main()
  
