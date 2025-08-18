#!/usr/bin/env python3

import sys
import subprocess
import platform
import os
import urllib.request
import shutil

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
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", package])
    print(f"{package} installed successfully.")

def command_exists(cmd):
    return shutil.which(cmd) is not None

def install_homebrew():
    print("Installing Homebrew...")
    install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    subprocess.check_call(install_cmd, shell=True)
    print("Homebrew installed.")

def install_chocolatey():
    print("Installing Chocolatey...")
    install_cmd = (
        "Set-ExecutionPolicy Bypass -Scope Process -Force; "
        "[System.Net.ServicePointManager]::SecurityProtocol = "
        "[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
        "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    )
    subprocess.check_call(["powershell.exe", "-Command", install_cmd])
    os.environ["Path"] += os.pathsep + "C:\\ProgramData\\chocolatey\\bin"
    print("Chocolatey installed.")

def generate_playbook(client, os_name, programs, template=None, error=None, previous_content=None):
    if error:
        prompt = (
            f"Fix this Ansible playbook YAML for {os_name} environment based on the following error: {error}\n"
            f"Previous playbook:\n{previous_content}\n"
            f"The playbook should install a development environment and the user-required programs: {', '.join(programs)}. "
            f"For each program installation task, make sure to add 'ignore_errors: true' to prevent failures if the program is already installed. "
            f"Give me just the complete YAML code and no other text as response to this."
        )
    else:
        prompt = (
            f"Create an Ansible playbook YAML for {os_name} environment in order to install development environment "
            f"and user required programs: {', '.join(programs)}. "
            f"For each program installation task, add 'ignore_errors: true' to prevent failures if the program is already installed. "
        )
        if template:
            prompt += f"\nHere is an example of a playbook structure to follow:\n{template}\n"
        prompt += "Give me just the complete YAML code and no other text as response to this."

    from openai import OpenAI
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

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

def main():
    os_name = platform.system().lower()

    if os_name not in ("linux", "darwin", "windows"):
        print(f"Unsupported operating system: {os_name}")
        return

    if not check_pip():
        install_pip()

    install_package("python-dotenv")
    install_package("openai")

    from dotenv import load_dotenv
    from openai import OpenAI

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

    programs_input = input("Enter the list of programs to install, separated by commas: ").strip()
    programs = [p.strip() for p in programs_input.split(',') if p.strip()]

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

    - name: Install a program (example)
      homebrew_cask:
        name: example-program
        state: present
      ignore_errors: true
"""

    print("Generating Ansible playbook...")
    playbook_content = generate_playbook(client, os_name, programs, template=playbook_content_template)

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
                ['ansible-playbook', playbook_file, '--syntax-check'],
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
        subprocess.check_call(['ansible-playbook', playbook_file])
        print("Playbook executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running playbook: {e}")
    except Exception as e:
        print(f"Unexpected error running playbook: {e}")

if __name__ == "__main__":
    main()
