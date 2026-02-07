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

BASIC_PROGRAMS = {
    "linux": ["vlc", "docker.io", "git", "code"],
    "darwin": ["vlc", "docker", "git", "visual-studio-code", "google-chrome"],
    "windows": ["vlc", "docker-desktop", "git", "vscode", "googlechrome"]
}

DEVELOPER_PROGRAMS = {
    "linux": ["git", "docker.io", "code", "postman", "dbeaver-ce", "libreoffice", "evince", "slack", "vlc", "gimp", "spotify-client"],
    "darwin": ["git", "docker", "visual-studio-code", "postman", "dbeaver-community", "libreoffice", "adobe-acrobat-reader", "slack", "vlc", "gimp", "spotify"],
    "windows": ["git", "docker-desktop", "vscode", "postman", "dbeaver", "libreoffice", "adobereader", "slack", "vlc", "gimp", "spotify"]
}

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

def install_package(package):
    print(f"Installing {package}...")
    command = [sys.executable, "-m", "pip", "install", package]
    # If not in a virtual environment, install to user site-packages
    if sys.prefix == sys.base_prefix:
        command.insert(4, "--user")

    subprocess.check_call(command)
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

def generate_playbook(client, os_name, programs, template=None, error=None, previous_content=None):
    if error:
        prompt = (
            f"Fix this Ansible playbook YAML for {os_name} environment based on the following error: {error}\n"
            f"Previous playbook:\n{previous_content}\n"
            f"The playbook should install a development environment and the user-required programs: {', '.join(programs)}. "
            f"For each program installation task, make sure to add 'ignore_errors: true' to prevent failures if the program is already installed. "
            f"Do not include anything but the complete program and no text before or after answering this prompt and get rid of ''' before and after"
        )
    else:
        prompt = (
            f"Create an Ansible playbook YAML for {os_name} environment in order to install development environment "
            f"and user required programs: {', '.join(programs)}. "
            f"For each program installation task, add 'ignore_errors: true' to prevent failures if the program is already installed. "
        )
        if template:
            prompt += f"\nUse the following template as a base:\n{template}\n"
        prompt += "Do not include anything but the complete program and no text before or after answering this prompt and get rid of ''' before and after"

    import time

    models_to_try = ["gpt-4o-mini", "gpt-5-2025-08-07"]
    max_retries_per_model = 3
    initial_sleep_duration = 7  # seconds
    increment = 5  # seconds

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

    print("Failed to generate playbook with all models after multiple retries.")
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
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "ansible"])
                advise_path_update()
        elif os_name == "linux":
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "ansible"])
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

def get_program_list(os_name):
    while True:
        choice = input(
            "Choose an option:\n"
            "a. Install a basic list of applications.\n"
            "b. Install a full developer list of applications.\n"
            "c. Enter a custom list of programs.\n"
            "Your choice: "
        ).lower()

        if choice == 'a':
            return choice, BASIC_PROGRAMS.get(os_name, [])
        elif choice == 'b':
            return choice, DEVELOPER_PROGRAMS.get(os_name, [])
        elif choice == 'c':
            programs_input = input("Enter the list of programs to install, separated by commas: ").strip()
            return choice, [p.strip() for p in programs_input.split(',') if p.strip()]
        else:
            print("Invalid choice. Please enter 'a', 'b', or 'c'.")

import argparse
from importlib import metadata

def install_programs_and_configure(programs, os_name, client, choice):
    """
    Installs programs and runs Ansible configuration.
    This function is designed to be called from both the CLI and GUI.
    """
    if not programs:
        print("No programs specified.")
        return

    try:
        if os_name == "linux":
            pm = None
            if command_exists("apt"):
                pm = "apt"
            elif command_exists("dnf"):
                pm = "dnf"
            elif command_exists("yum"):
                pm = "yum"
            elif command_exists("pacman"):
                pm = "pacman"
            else:
                print("No supported package manager found (apt, dnf, yum, pacman).")
                return

            print(f"Using package manager: {pm}")

            if pm == "apt":
                subprocess.check_call(["sudo", "apt", "update"])
                install_cmd = ["sudo", "apt", "install", "-y"] + programs
            elif pm == "dnf":
                install_cmd = ["sudo", "dnf", "install", "-y"] + programs
            elif pm == "yum":
                install_cmd = ["sudo", "yum", "install", "-y"] + programs
            elif pm == "pacman":
                install_cmd = ["sudo", "pacman", "-Syu", "--noconfirm"] + programs

            subprocess.check_call(install_cmd)
            print("Installation complete.")

        elif os_name == "darwin":
            if not command_exists("brew"):
                install_homebrew()
            install_cmd = ["brew", "install"] + programs
            subprocess.check_call(install_cmd)
            print("Installation complete.")

        elif os_name == "windows":
            if not command_exists("choco"):
                install_chocolatey()
            install_cmd = ["choco", "install", "-y"] + programs
            subprocess.check_call(install_cmd)
            print("Installation complete.")

    except subprocess.CalledProcessError as e:
        print(f"Error during installation: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    if os_name not in ("linux", "darwin"):
        print("Cannot generate and run Ansible playbook on Windows.")
        return

    playbook_content_template = """---
- name: Setup macOS Development Environment
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: Ensure Homebrew is installed
      homebrew:
        state: present

    - name: Install Python
      homebrew:
        name: python
        state: present

    - name: Install VLC
      homebrew_cask:
        name: vlc
        state: present

    - name: Install DuckDuckGo
      homebrew_cask:
        name: duckduckgo
        state: present

    - name: Install Zoom
      homebrew_cask:
        name: zoom
        state: present

    - name: Install UTM
      homebrew_cask:
        name: utm
        state: present

    - name: Install Docker
      homebrew_cask:
        name: docker
        state: present

    - name: Install LM Studio
      homebrew_cask:
        name: lm-studio
        state: present
"""

    print("Generating Ansible playbook...")

    # Determine which template to use
    if choice == 'b':
        template_path = 'template-full.yml'
    else:
        template_path = 'ansible_playbook_template.yml'

    try:
        with open(template_path, 'r') as f:
            playbook_content_template = f.read()
    except FileNotFoundError:
        print(f"Warning: Template file not found at {template_path}. Proceeding without a template.")
        playbook_content_template = None

    playbook_content = generate_playbook(client, os_name, programs, template=playbook_content_template)

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

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            print(f"Attempt {attempt + 1}: Checking playbook syntax...")
            output = subprocess.check_output(
                ['ansible-playbook', playbook_file, '--syntax-check', '-v'],
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
            if attempt < max_attempts - 1:
                print("Attempting to fix the playbook...")
                playbook_content = generate_playbook(client, os_name, programs, error=error_msg, previous_content=playbook_content)
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
        subprocess.check_call(['ansible-playbook', playbook_file, '-v'])
        print("Playbook executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running playbook: {e}")
    except Exception as e:
        print(f"Unexpected error running playbook: {e}")


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

    choice, programs = get_program_list(os_name)
    install_programs_and_configure(programs, os_name, client, choice)

if __name__ == "__main__":
    main()
  
