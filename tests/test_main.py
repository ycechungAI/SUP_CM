import pytest
from unittest.mock import patch, MagicMock, mock_open, call
from program_installer import main
import sys
import subprocess
import os

@patch('subprocess.check_call')
def test_check_pip_exists(mock_check_call):
    """
    Test that check_pip returns True when pip is found.
    """
    assert main.check_pip() is True
    mock_check_call.assert_called_once_with([sys.executable, "-m", "pip", "--version"])

@patch('subprocess.check_call', side_effect=subprocess.CalledProcessError(1, 'cmd'))
def test_check_pip_not_exists(mock_check_call):
    """
    Test that check_pip returns False when pip is not found.
    """
    assert main.check_pip() is False
    mock_check_call.assert_called_once_with([sys.executable, "-m", "pip", "--version"])

@patch('subprocess.check_call', side_effect=FileNotFoundError)
def test_check_pip_file_not_found(mock_check_call):
    """
    Test that check_pip returns False when python executable is not found.
    """
    assert main.check_pip() is False
    mock_check_call.assert_called_once_with([sys.executable, "-m", "pip", "--version"])

@patch('urllib.request.urlretrieve')
@patch('subprocess.check_call')
@patch('os.remove')
def test_install_pip(mock_remove, mock_check_call, mock_urlretrieve):
    """
    Test that install_pip downloads and installs pip.
    """
    main.install_pip()
    mock_urlretrieve.assert_called_once_with("https://bootstrap.pypa.io/get-pip.py", "get-pip.py")
    mock_check_call.assert_called_once_with([sys.executable, "get-pip.py", "--user"])
    mock_remove.assert_called_once_with("get-pip.py")

@patch('program_installer.main._run_pip_install')
def test_install_package(mock_run_pip):
    """
    Test that install_package calls _run_pip_install.
    """
    main.install_package("my-package")
    mock_run_pip.assert_called_once_with("my-package")

def test_run_pip_install_no_venv():
    """
    Test that _run_pip_install uses --user when not in a venv.
    """
    with patch('subprocess.check_call') as mock_check_call, \
         patch('os.getenv', return_value=None), \
         patch('sys.prefix', '/usr'), \
         patch('sys.base_prefix', '/usr'):
        main._run_pip_install("my-package")
        expected_command = [sys.executable, "-m", "pip", "install", "--user", "my-package"]
        mock_check_call.assert_called_once_with(expected_command)

def test_run_pip_install_in_venv_by_prefix():
    """
    Test that _run_pip_install does not use --user when in a venv (detected by sys.prefix).
    """
    with patch('subprocess.check_call') as mock_check_call, \
         patch('os.getenv', return_value=None), \
         patch('sys.prefix', '/app/.venv'), \
         patch('sys.base_prefix', '/usr'):
        main._run_pip_install("my-package")
        expected_command = [sys.executable, "-m", "pip", "install", "my-package"]
        mock_check_call.assert_called_once_with(expected_command)

def test_run_pip_install_in_venv_by_env_var():
    """
    Test that _run_pip_install does not use --user when in a venv (detected by VIRTUAL_ENV).
    """
    with patch('subprocess.check_call') as mock_check_call, \
         patch('os.getenv', return_value='/app/.venv'):
        main._run_pip_install("my-package")
        expected_command = [sys.executable, "-m", "pip", "install", "my-package"]
        mock_check_call.assert_called_once_with(expected_command)

@patch('shutil.which')
def test_command_exists(mock_which):
    """
    Test that command_exists returns True when a command exists.
    """
    mock_which.return_value = '/usr/bin/test'
    assert main.command_exists("test") is True
    mock_which.assert_called_once_with("test")

@patch('shutil.which')
def test_command_does_not_exist(mock_which):
    """
    Test that command_exists returns False when a command does not exist.
    """
    mock_which.return_value = None
    assert main.command_exists("test") is False
    mock_which.assert_called_once_with("test")

@patch('subprocess.check_call')
def test_install_homebrew(mock_check_call):
    """
    Test that install_homebrew runs the Homebrew installation script.
    """
    main.install_homebrew()
    install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    mock_check_call.assert_called_once_with(install_cmd, shell=True)

@patch('os.path.isdir', return_value=False)
@patch('subprocess.check_call')
@patch.dict(os.environ, {'Path': ''}, clear=True)
def test_install_chocolatey(mock_check_call, mock_isdir):
    """
    Test that install_chocolatey runs the Chocolatey installation script.
    """
    main.install_chocolatey()
    install_cmd = (
        "Set-ExecutionPolicy Bypass -Scope Process -Force; "
        "[System.Net.ServicePointManager]::SecurityProtocol = "
        "[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
        "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    )
    mock_check_call.assert_called_once_with(["powershell.exe", "-Command", install_cmd])

@patch('subprocess.check_call')
@patch('os.path.isdir', return_value=True)
@patch('sys.exit')
@patch.dict(os.environ, {'Path': ''}, clear=True)
def test_install_chocolatey_already_exists(mock_exit, mock_isdir, mock_check_call, capsys):
    """
    Test that install_chocolatey exits if the choco directory already exists.
    """
    mock_exit.side_effect = SystemExit(1)
    with pytest.raises(SystemExit) as e:
        main.install_chocolatey()

    assert e.value.code == 1
    mock_isdir.assert_called_once()
    mock_check_call.assert_not_called()
    captured = capsys.readouterr()
    assert "Warning: An existing Chocolatey directory was found." in captured.out

def test_generate_playbook():
    """
    Test that generate_playbook calls the OpenAI API with the correct prompt.
    """
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices[0].message.content = "playbook_content"
    template = "playbook_template"

    result = main.generate_playbook(mock_client, "macOS", ["vim", "git"], template=template)
    assert result == "playbook_content"
    mock_client.chat.completions.create.assert_called_once()
    prompt = mock_client.chat.completions.create.call_args[1]['messages'][0]['content']
    assert "Create an Ansible playbook YAML for macOS" in prompt
    assert "vim, git" in prompt
    assert "ignore_errors: true" in prompt
    assert template not in prompt

def test_generate_playbook_with_error():
    """
    Test that generate_playbook calls the OpenAI API with a prompt to fix an error.
    """
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices[0].message.content = "fixed_playbook_content"

    result = main.generate_playbook(mock_client, "macOS", ["vim", "git"], error="some error", previous_content="previous_content")
    assert result == "fixed_playbook_content"
    mock_client.chat.completions.create.assert_called_once()
    prompt = mock_client.chat.completions.create.call_args[1]['messages'][0]['content']
    assert "Fix this Ansible playbook YAML for macOS" in prompt
    assert "some error" in prompt
    assert "previous_content" in prompt
    assert "vim, git" in prompt
    assert "ignore_errors: true" in prompt

@patch('time.sleep', return_value=None)
def test_generate_playbook_fallback_succeeds(mock_sleep):
    """
    Test that generate_playbook falls back to the second model and succeeds.
    """
    mock_client = MagicMock()
    mock_response_empty = MagicMock()
    mock_response_empty.choices[0].message.content = ""
    mock_response_success = MagicMock()
    mock_response_success.choices[0].message.content = "playbook_content"

    # Fail 3 times with the first model, then succeed with the second model.
    mock_client.chat.completions.create.side_effect = [
        mock_response_empty,
        mock_response_empty,
        mock_response_empty,
        mock_response_success
    ]

    result = main.generate_playbook(mock_client, "macOS", ["vim", "git"])
    assert result == "playbook_content"
    assert mock_client.chat.completions.create.call_count == 4
    mock_sleep.assert_has_calls([call(7), call(12), call(17)])
    assert mock_sleep.call_count == 3

@patch('time.sleep', return_value=None)
def test_generate_playbook_fallback_fails(mock_sleep):
    """
    Test that generate_playbook returns None after all models and retries fail.
    """
    mock_client = MagicMock()
    mock_response_empty = MagicMock()
    mock_response_empty.choices[0].message.content = ""

    # Fail 3 times for each of the 2 models.
    mock_client.chat.completions.create.side_effect = [mock_response_empty] * 6

    result = main.generate_playbook(mock_client, "macOS", ["vim", "git"])
    assert result is None
    assert mock_client.chat.completions.create.call_count == 6
    mock_sleep.assert_has_calls([
        call(7), call(12), call(17), # First model failures
        call(7), call(12), call(17)  # Second model failures
    ])
    assert mock_sleep.call_count == 6

@patch('builtins.input', return_value='a')
def test_get_program_list_basic(mock_input):
    """
    Test that get_program_list returns the basic list when 'a' is chosen.
    """
    choice, programs = main.get_program_list('darwin')
    assert choice == 'a'
    assert programs == main.BASIC_PROGRAMS['darwin']

@patch('builtins.input', return_value='b')
def test_get_program_list_developer(mock_input):
    """
    Test that get_program_list returns the developer list when 'b' is chosen.
    """
    choice, programs = main.get_program_list('windows')
    assert choice == 'b'
    assert programs == main.DEVELOPER_PROGRAMS['windows']

@patch('builtins.input', side_effect=['c', 'custom-prog1, custom-prog2'])
def test_get_program_list_custom(mock_input):
    """
    Test that get_program_list returns a custom list when 'c' is chosen.
    """
    choice, programs = main.get_program_list('linux')
    assert choice == 'c'
    assert programs == ['custom-prog1', 'custom-prog2']

@patch('platform.system', return_value='darwin')
@patch('program_installer.main.check_pip', return_value=True)
@patch('program_installer.main.install_pip')
@patch('program_installer.main.install_package')
@patch('dotenv.load_dotenv')
@patch('openai.OpenAI')
@patch('builtins.input', side_effect=['c', 'vim, git'])
@patch('program_installer.main.command_exists')
@patch('program_installer.main.install_homebrew')
@patch('subprocess.check_call')
@patch('subprocess.check_output', return_value=b'Syntax check passed')
@patch('builtins.open', new_callable=mock_open)
@patch('program_installer.main.advise_path_update')
@patch('program_installer.main.generate_playbook', return_value='generated_playbook_content')
def test_main_macos(
    mock_generate_playbook, mock_advise, mock_open_file, mock_check_output, mock_check_call,
    mock_install_homebrew, mock_command_exists, mock_input, mock_openai,
    mock_load_dotenv, mock_install_package, mock_install_pip, mock_check_pip, mock_system
):
    """
    Test the main function on macOS.
    """
    # Simulate that brew and ansible are not installed initially, but are installed later.
    mock_command_exists.side_effect = [
        False, # ansible-playbook not found
        False, # brew not found
        True,  # ansible-playbook found after install
        True   # brew found after program install
    ]
    os.environ['OPENAI_API_KEY'] = 'test_key'

    main.main()

    # Check that the correct functions were called
    mock_check_pip.assert_called_once()
    mock_install_pip.assert_not_called()
    assert mock_install_package.call_count == 2
    mock_load_dotenv.assert_called_once()
    mock_openai.assert_called_once()
    assert mock_input.call_count == 2
    assert mock_command_exists.call_count == 4
    mock_install_homebrew.assert_called_once()

    # Check ansible installation calls
    assert any(['brew', 'install', 'ansible'] in call.args for call in mock_check_call.call_args_list)

    # Check program installation calls
    assert any(['brew', 'install', 'vim', 'git'] in call.args for call in mock_check_call.call_args_list)

    # Check playbook generation and execution
    mock_generate_playbook.assert_called_once()
    # The template loading is tested in other tests. Here we focus on the main flow.
    mock_open_file.assert_called_with('ansible_playbook.yml', 'w')
    mock_open_file().write.assert_called_once_with('generated_playbook_content')
    mock_check_output.assert_called_with(
        ['ansible-playbook', 'ansible_playbook.yml', '--syntax-check', '-v'],
        stderr=subprocess.STDOUT
    )
    assert any(['ansible-playbook', 'ansible_playbook.yml', '-v'] in call.args for call in mock_check_call.call_args_list)

@patch('sys.argv', ['program-installer', '--help'])
def test_main_help(capsys):
    """
    Test that the --help flag prints a help message and exits.
    """
    with pytest.raises(SystemExit) as e:
        main.main()
    assert e.type == SystemExit
    assert e.value.code == 0
    captured = capsys.readouterr()
    assert "usage: program-installer" in captured.out
    assert "show this help message and exit" in captured.out

@patch('sys.argv', ['program-installer', '--version'])
@patch('importlib.metadata.version', return_value='0.1')
def test_main_version(mock_version, capsys):
    """
    Test that the --version flag prints the version and exits.
    """
    with pytest.raises(SystemExit) as e:
        main.main()
    assert e.type == SystemExit
    assert e.value.code == 0
    captured = capsys.readouterr()
    assert "program-installer 0.1" in captured.out

@patch('platform.system', return_value='darwin')
@patch('program_installer.main.check_pip', return_value=True)
@patch('program_installer.main.install_pip')
@patch('program_installer.main.install_package')
@patch('dotenv.load_dotenv')
@patch('openai.OpenAI')
@patch('builtins.input', return_value='b')
@patch('program_installer.main.command_exists', return_value=True)
@patch('subprocess.check_call')
@patch('subprocess.check_output', return_value=b'Syntax check passed')
@patch('builtins.open', new_callable=mock_open)
@patch('program_installer.main.generate_playbook', return_value='generated_playbook_content')
def test_main_developer_list(
    mock_generate_playbook, mock_open_file, mock_check_output, mock_check_call,
    mock_command_exists, mock_input, mock_openai, mock_load_dotenv,
    mock_install_package, mock_install_pip, mock_check_pip, mock_system
):
    """
    Test that the full developer template is used when option 'b' is selected.
    """
    os.environ['OPENAI_API_KEY'] = 'test_key'
    main.main()

    with open('template-full.yml', 'r') as f:
        expected_template = f.read()

    mock_generate_playbook.assert_called_once()
    assert mock_generate_playbook.call_args[1]['template'] == expected_template

@patch('platform.system', return_value='linux')
@patch('program_installer.main.command_exists', return_value=False)
@patch('program_installer.main._run_pip_install')
@patch('program_installer.main.advise_path_update')
def test_ensure_ansible_installed_linux(mock_advise, mock_run_pip, mock_exists, mock_system):
    """
    Test that ensure_ansible_installed uses pip to install ansible on Linux.
    """
    mock_exists.side_effect = [False, True] # ansible-playbook not found, then found
    main.ensure_ansible_installed()
    mock_run_pip.assert_called_once_with("ansible")
    mock_advise.assert_called_once()

@patch('platform.system', return_value='darwin')
@patch('program_installer.main.command_exists', return_value=False)
@patch('subprocess.check_call')
@patch('program_installer.main._run_pip_install')
@patch('program_installer.main.advise_path_update')
def test_ensure_ansible_installed_macos_fallback(mock_advise, mock_run_pip, mock_check_call, mock_exists, mock_system):
    """
    Test that ensure_ansible_installed falls back to pip on macOS if brew fails.
    """
    def check_call_side_effect(cmd, shell=False):
        if "brew install ansible" in " ".join(cmd):
            raise subprocess.CalledProcessError(1, cmd)
        # For other calls like install_homebrew, do nothing
        pass

    mock_check_call.side_effect = check_call_side_effect
    mock_exists.side_effect = [False, False, True] # ansible not found, brew not found, then ansible found
    main.ensure_ansible_installed()
    mock_run_pip.assert_called_once_with("ansible")
    mock_advise.assert_called_once()
