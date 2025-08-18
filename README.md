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

- Python 3.5+
- An OpenAI API key

## Installation

There are two ways to install AES_CM: from PyPI or from the source.

### From PyPI (Recommended)

1.  **Install the package:**
    ```bash
    pip install aes-cm
    ```

### From Source (for development)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ycechung-cm/your_repository.git
    cd your_repository
    ```

2.  **Install in editable mode:**
    This will install the package and its dependencies. The `-e` flag allows you to edit the code and have the changes apply immediately.
    ```bash
    pip install -e .
    ```

## Configuration

Before running the program, you need to set up your OpenAI API key. Create a `.env` file in the directory where you will run the command:

```
OPENAI_API_KEY=your_api_key_here
```

The program will automatically find and use this `.env` file.

## Usage

Once installed, you can run the program from your terminal using the `program-installer` command:

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
