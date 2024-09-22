import argparse
import sys
import threading
import tkinter as tk
from os import path
from tkinter import Tk, messagebox, ttk

import mido
from PIL import Image

from config import load_config
from menu_bar import MenuBar
from midi import Midi
from theme import Theme
from tray_icon import TrayIcon

ICON_PATH = path.join(path.dirname(__file__), "icon", "favicon.ico")
ICON = Image.open(ICON_PATH)


class App(Tk):
    def __init__(self, start_minimized: bool = False):
        super().__init__()

        self.title("RIDI")
        self.iconbitmap(ICON_PATH)

        # MIDI input and output ports
        self.input_port_name = tk.StringVar()
        self.output_port_name = tk.StringVar()

        # Initialize routing_thread and stop_thread
        self.routing_thread = None
        self.stop_thread = False

        self.theme = Theme()
        self.midi = Midi
        self.menu_bar = MenuBar(
            parent=self,
            input_port_name=self.input_port_name,
            output_port_name=self.output_port_name,
            theme=self.theme,
            quit_callback=self.quit_app,
        )

        self.create_widgets()

        # Load saved configuration if exists
        load_config(
            input_port_name=self.input_port_name,
            output_port_name=self.output_port_name,
            input_names=mido.get_input_names(),
            output_names=mido.get_output_names(),
            theme=self.theme,
            callback=self.start_routing,
        )

        # Minimize to tray if argument is passed
        if start_minimized:
            self.hide_window()

    def create_widgets(self):
        # Input Port Selection
        ttk.Label(self, text="MIDI Input Port:").grid(row=0, column=0, padx=10, pady=5)
        self.input_dropdown = ttk.Combobox(self, textvariable=self.input_port_name)
        self.input_dropdown["values"] = mido.get_input_names()
        self.input_dropdown.grid(row=0, column=1, padx=10, pady=5)

        # Output Port Selection
        ttk.Label(self, text="MIDI Output Port:").grid(row=1, column=0, padx=10, pady=5)
        self.output_dropdown = ttk.Combobox(self, textvariable=self.output_port_name)
        self.output_dropdown["values"] = mido.get_output_names()
        self.output_dropdown.grid(row=1, column=1, padx=10, pady=5)

        # Button to start routing
        self.start_button = ttk.Button(self, text="Start", command=self.start_routing)
        self.start_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Button to stop routing
        self.stop_button = ttk.Button(self, text="Stop", command=self.stop_routing)
        self.stop_button.grid(row=3, column=0, columnspan=2, pady=10)

        # MIDI events display window
        self.event_log = tk.Text(self, height=10, width=50, state=tk.DISABLED)
        self.event_log.grid(row=4, column=0, columnspan=2, padx=10, pady=5)

    def log_event(self, message):
        self.event_log.config(state=tk.NORMAL)
        self.event_log.insert(tk.END, f"{message}\n")
        self.event_log.config(state=tk.DISABLED)
        self.event_log.yview(tk.END)  # Scroll to the bottom

    def start_routing(self):
        input_port = self.input_port_name.get()
        output_port = self.output_port_name.get()

        if not input_port or not output_port:
            messagebox.showwarning(
                "Selection Error", "Please select both input and output ports."
            )
            return

        # Stop any existing routing thread
        self.stop_routing()

        try:
            self.inport = mido.open_input(input_port)
            self.outport = mido.open_output(output_port)

            self.log_event(f"Listening on {input_port}, sending to {output_port}...")

            # Start a new thread for MIDI routing
            self.stop_thread = False
            self.routing_thread = threading.Thread(target=self.route_midi, daemon=True)
            self.routing_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open ports: {str(e)}")

    def route_midi(self):
        while not self.stop_thread:
            try:
                for message in self.inport.iter_pending():
                    self.log_event(f"Received: {message}")
                    self.outport.send(message)
            except Exception as e:
                self.log_event(f"Error: {str(e)}")

    def stop_routing(self):
        # Stop the thread by setting stop_thread to True
        self.stop_thread = True
        if self.routing_thread is not None:
            self.routing_thread.join()  # Wait for thread to finish
            self.log_event("MIDI routing stopped.")
        self.routing_thread = None

    # Define a function for quit the window
    def quit_window(self, icon: TrayIcon, _):
        icon.stop()
        self.destroy()

    # Define a function to show the window again
    def show_window(self, icon: TrayIcon, _):
        icon.stop()
        self.after(0, self.deiconify)

    def hide_window(self):
        self.withdraw()
        TrayIcon(icon=ICON, show_action=self.show_window, quit_action=self.quit_window)

    def quit_app(self):
        self.quit()
        sys.exit()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="MIDI App with optional minimize-to-tray startup."
    )
    parser.add_argument(
        "--minimized",
        action="store_true",
        help="Start the app minimized to the system tray.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    # Parse the command-line arguments
    args = parse_arguments()

    # Create the main application
    app = App(start_minimized=args.minimized)
    app.protocol("WM_DELETE_WINDOW", app.hide_window)
    app.mainloop()


# <a href="https://www.flaticon.com/free-icons/plug" title="plug icons">Plug icons created by Freepik - Flaticon</a>
