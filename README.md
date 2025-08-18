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

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/sup_cm.git
    cd sup_cm
    ```

2.  **Create a `.env` file:**
    Create a `.env` file in the root of the project and add your OpenAI API key:
    ```
    OPENAI_API_KEY=your_api_key_here
    ```

3.  **Install Python dependencies:**
    The script will automatically install the required Python packages when you run it for the first time. Alternatively, you can install them manually:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To run the script, execute the `main.py` file from your terminal:

```bash
python3 main.py
```

The script will guide you through the process:

1.  It will check for and install any missing dependencies.
2.  It will prompt you to enter a comma-separated list of programs you want to install.
3.  On macOS and Linux, it will generate and run an Ansible playbook to configure your system.
4.  On Windows, it will use Chocolatey to install the specified programs.

## Testing

This project includes a comprehensive test suite using `pytest`. To run the tests, follow these steps:

1.  **Install testing dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the tests:**
    ```bash
    pytest
    ```

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file.

## Other Links

- [AI/ML API Hackathon](https://aimlapi.com/app/)
- [LabLab Apps](https://lablab.ai/apps/)
- [AI/ML API Documentation](https://docs.aimlapi.com/)
