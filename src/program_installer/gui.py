import tkinter as tk
from tkinter import scrolledtext
import sys
import platform
import threading
from .main import (
    install_programs_and_configure,
    BASIC_PROGRAMS,
    DEVELOPER_PROGRAMS,
    check_pip,
    install_pip,
    install_package,
    ensure_ansible_installed,
)
from dotenv import load_dotenv
from openai import OpenAI
import os

class ProgramInstallerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Program Installer")
        self.geometry("800x600")

        self.os_name = platform.system().lower()
        self.client = None

        self.create_widgets()
        self.init_app()

    def create_widgets(self):
        # Frame for options
        options_frame = tk.Frame(self)
        options_frame.pack(pady=10)

        self.program_choice = tk.StringVar(value="a")

        tk.Radiobutton(options_frame, text="Basic Programs", variable=self.program_choice, value="a", command=self.toggle_custom_entry).pack(anchor="w")
        tk.Radiobutton(options_frame, text="Developer Programs", variable=self.program_choice, value="b", command=self.toggle_custom_entry).pack(anchor="w")
        tk.Radiobutton(options_frame, text="Custom List", variable=self.program_choice, value="c", command=self.toggle_custom_entry).pack(anchor="w")

        self.custom_entry = tk.Entry(options_frame, width=50)
        self.custom_entry.pack(anchor="w", padx=20)
        self.custom_entry.config(state="disabled")

        # Install button
        self.install_button = tk.Button(self, text="Install Programs", command=self.start_installation)
        self.install_button.pack(pady=10)

        # Output console
        self.output_console = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=25)
        self.output_console.pack(pady=10, padx=10, fill="both", expand=True)

    def toggle_custom_entry(self):
        if self.program_choice.get() == "c":
            self.custom_entry.config(state="normal")
        else:
            self.custom_entry.config(state="disabled")

    def redirect_output(self):
        sys.stdout = self
        sys.stderr = self

    def write(self, text):
        self.output_console.insert(tk.END, text)
        self.output_console.see(tk.END)

    def flush(self):
        pass

    def init_app(self):
        self.redirect_output()
        print("Welcome to the Program Installer GUI!")
        print(f"Operating System: {self.os_name.capitalize()}")

        if self.os_name not in ("linux", "darwin", "windows"):
            print(f"Unsupported operating system: {self.os_name}")
            self.install_button.config(state="disabled")
            return

        if not check_pip():
            print("pip is not installed. Attempting to install...")
            install_pip()

        install_package("python-dotenv")
        install_package("openai")

        load_dotenv()
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("OPENAI_API_KEY environment variable not set.")
            self.install_button.config(state="disabled")
            return

        self.client = OpenAI(
            base_url="https://api.aimlapi.com/v1",
            api_key=api_key,
        )

        if self.os_name in ("linux", "darwin"):
            ensure_ansible_installed()


    def start_installation(self):
        self.install_button.config(state="disabled")
        choice = self.program_choice.get()
        programs = []
        if choice == "a":
            programs = BASIC_PROGRAMS.get(self.os_name, [])
        elif choice == "b":
            programs = DEVELOPER_PROGRAMS.get(self.os_name, [])
        elif choice == "c":
            programs_input = self.custom_entry.get()
            programs = [p.strip() for p in programs_input.split(',') if p.strip()]

        if not programs:
            print("No programs selected.")
            self.install_button.config(state="normal")
            return

        print(f"Starting installation of: {', '.join(programs)}")

        install_thread = threading.Thread(
            target=install_programs_and_configure,
            args=(programs, self.os_name, self.client, choice)
        )
        install_thread.start()
        self.monitor_thread(install_thread)

    def monitor_thread(self, thread):
        if thread.is_alive():
            self.after(100, lambda: self.monitor_thread(thread))
        else:
            print("\nInstallation process finished.")
            self.install_button.config(state="normal")

def main():
    app = ProgramInstallerGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
