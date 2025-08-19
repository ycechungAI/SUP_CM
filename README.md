# AES_CM: Automated Environment Setup_Configuration Manager

AES_CM (Auto Env Setup CM) is a powerful tool that automates the setup of a development environment on macOS, Linux, and Windows. It uses a combination of native package managers and Ansible to install and configure software, and leverages the OpenAI API to generate Ansible playbooks tailored to your needs.

Why do we need? We have billions of new devices going to be added around the world, whether you are running any type of computer operating system, smart phone or ASIC devices.  It may require initial setup for developers and geeks alike.  Hence there is the issue we all have faced when installing or doing the boring setup on a fresh OS install.  Meet AES_CM the world's automated setup tool where you just buy the system and setup on single command.

## Features

- **Cross-Platform Support**: Works on macOS, Linux, and Windows.
- **Automated Dependency Installation**: Automatically installs required Python packages.
- **Package Management**: Uses native package managers for software installation (Homebrew for macOS, Chocolatey for Windows, and apt/dnf/yum/pacman for Linux).
- **AI-Powered Configuration**: Utilizes the OpenAI API to generate Ansible playbooks for complex setups.
- **Interactive**: Prompts the user for a list of programs to install.
- **Self-Healing Ansible Playbooks**: Attempts to fix broken Ansible playbooks using AI.

## Supported Operating Systems

- **macOS**
- **Linux** (Debian, Ubuntu, Fedora, CentOS, Arch)
- **Windows**

## Prerequisites

- Python 3.9+
    - Tips for windows install python from Microsoft Store or dont forget to include it in your path
    - For Mac use homebrew
- An OpenAI API key
- Git

## Installation

There are two ways to install AES_CM: from PyPI or from the source.

### From PyPI (Recommended)

1.  **Install the package:**
    ```bash
    pip install aes-cm
    ```

### Running Locally for Development

To run the project on your local machine for development purposes, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ycechungAI/SUP_CM.git
    cd SUP_CM
    ```

2.  **Set up a virtual environment (Recommended):**
    windows
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

    ```bash
    python3 -m venv .venv
    . .\.venv\Scripts\Activate.ps1
    ```
    Linux (e.g. Ubuntu)
    sudo apt install python3-venv
    
    macOS and Linux
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```


    ```python3
    python3 -m pip install --upgrade build
    python3 -m build
    python3 -m pip install ./dist/aes_cm-0.1-py3-none-any.whl
    python3 -m pip install ./dist/aes_cm-0.1.tar.gz
    ```

4.  **Install the project in editable mode:**
    This command installs all the dependencies and makes the script available as a command-line tool. The `-e` flag means that any changes you make to the source code will be immediately effective when you run the command.
    ```bash
    pip3 install -e .
    ```

5.  **Set up your API Key:**
    Create a `.env` file in the project's root directory:
    ```
    OPENAI_API_KEY=your_api_key_here
    ```

6.  **Run the program:**
    Now you can run the program using the command:
    ```bash
    program-installer
    ```

The script will guide you through the process:

1.  It will check for and install any missing dependencies.
2.  It will prompt you to enter a comma-separated list of programs you want to install.
3.  On macOS and Linux, it will generate and run an Ansible playbook to configure your system.
4.  On Windows, it will use Chocolatey to install the specified programs.

## Testing

This project includes a comprehensive test suite using `pytest`. To run the tests, follow these steps:

1.  **Install testing dependencies:**
    On some systems, you may need to use `pip3` instead of `pip`.
    ```bash
    pip3 install -r requirements.txt
    ```

2.  **Run the tests:**
    On some systems, you may need to use `python3` to run pytest as a module.
    ```bash
    python3 -m pytest
    ```

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file.

## Other Links

- [AI/ML API Hackathon](https://aimlapi.com/app/)
- [LabLab Apps](https://lablab.ai/apps/)
- [AI/ML API Documentation](https://docs.aimlapi.com/)

## Authors
- Eugene Chung
- Google Jules AI
