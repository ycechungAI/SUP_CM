import pytest
from unittest.mock import patch, MagicMock, mock_open, call
import main
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

@patch('subprocess.check_call')
def test_install_package(mock_check_call):
    """
    Test that install_package calls pip to install a package.
    """
    main.install_package("my-package")
    mock_check_call.assert_called_once_with([sys.executable, "-m", "pip", "install", "--user", "my-package"])

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

@patch('subprocess.check_call')
@patch.dict(os.environ, {'Path': ''}, clear=True)
def test_install_chocolatey(mock_check_call):
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
    programs = main.get_program_list('darwin')
    assert programs == main.BASIC_PROGRAMS['darwin']

@patch('builtins.input', return_value='b')
def test_get_program_list_developer(mock_input):
    """
    Test that get_program_list returns the developer list when 'b' is chosen.
    """
    programs = main.get_program_list('windows')
    assert programs == main.DEVELOPER_PROGRAMS['windows']

@patch('builtins.input', side_effect=['c', 'custom-prog1, custom-prog2'])
def test_get_program_list_custom(mock_input):
    """
    Test that get_program_list returns a custom list when 'c' is chosen.
    """
    programs = main.get_program_list('linux')
    assert programs == ['custom-prog1', 'custom-prog2']

@patch('platform.system', return_value='darwin')
@patch('main.check_pip', return_value=True)
@patch('main.install_pip')
@patch('main.install_package')
@patch('dotenv.load_dotenv')
@patch('openai.OpenAI')
@patch('builtins.input', side_effect=['c', 'vim, git'])
@patch('main.command_exists')
@patch('main.install_homebrew')
@patch('subprocess.check_call')
@patch('subprocess.check_output', return_value=b'Syntax check passed')
@patch('builtins.open', new_callable=mock_open)
@patch('main.advise_path_update')
@patch('main.generate_playbook', return_value='generated_playbook_content')
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
    mock_open_file.assert_called_with('ansible_playbook.yml', 'w')
    mock_open_file().write.assert_called_once_with('generated_playbook_content')
    mock_check_output.assert_called_with(
        ['ansible-playbook', 'ansible_playbook.yml', '--syntax-check', '-v'],
        stderr=subprocess.STDOUT
    )
    assert any(['ansible-playbook', 'ansible_playbook.yml', '-v'] in call.args for call in mock_check_call.call_args_list)
