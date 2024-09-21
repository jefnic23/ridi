import argparse
import json
import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import mido
import pystray
from PIL import Image, ImageDraw

CONFIG_FILE = "config.json"


class MidiApp:
    def __init__(self, root, start_minimized=False):
        self.root = root
        self.root.title("MIDI Router")

        # MIDI input and output ports
        self.input_port_name = tk.StringVar()
        self.output_port_name = tk.StringVar()

        # Initialize routing_thread and stop_thread
        self.routing_thread = None
        self.stop_thread = False

        # UI elements
        self.create_menu_bar()
        self.create_widgets()

        # Load saved configuration if exists
        self.load_config()

        # System tray
        self.tray_icon = None
        self.create_tray_icon()

        # Minimize to tray if argument is passed
        if start_minimized:
            self.minimize_to_tray()

    def create_menu_bar(self):
        # Create the menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        #File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # MIDI menu
        self.midi_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="MIDI", menu=self.midi_menu)

        # MIDI Input Selection
        self.midi_input_menu = tk.Menu(self.midi_menu, tearoff=0)
        self.midi_menu.add_cascade(label="Select MIDI Input", menu=self.midi_input_menu)
        self.update_midi_input_menu()

        # MIDI Output Selection
        self.midi_output_menu = tk.Menu(self.midi_menu, tearoff=0)
        self.midi_menu.add_cascade(
            label="Select MIDI Output", menu=self.midi_output_menu
        )
        self.update_midi_output_menu()

        # Save Configuration
        self.midi_menu.add_separator()
        self.midi_menu.add_command(label="Save Configuration", command=self.save_config)

    def update_midi_input_menu(self):
        """Update the MIDI input menu with available ports."""
        self.midi_input_menu.delete(0, "end")  # Clear existing entries
        available_inputs = mido.get_input_names()
        for input_port in available_inputs:
            self.midi_input_menu.add_radiobutton(
                label=input_port, variable=self.input_port_name, value=input_port
            )

    def update_midi_output_menu(self):
        """Update the MIDI output menu with available ports."""
        self.midi_output_menu.delete(0, "end")  # Clear existing entries
        available_outputs = mido.get_output_names()
        for output_port in available_outputs:
            self.midi_output_menu.add_radiobutton(
                label=output_port, variable=self.output_port_name, value=output_port
            )

    def create_widgets(self):
        # Input Port Selection
        ttk.Label(self.root, text="MIDI Input Port:").grid(
            row=0, column=0, padx=10, pady=5
        )
        self.input_dropdown = ttk.Combobox(self.root, textvariable=self.input_port_name)
        self.input_dropdown["values"] = mido.get_input_names()
        self.input_dropdown.grid(row=0, column=1, padx=10, pady=5)

        # Output Port Selection
        ttk.Label(self.root, text="MIDI Output Port:").grid(
            row=1, column=0, padx=10, pady=5
        )
        self.output_dropdown = ttk.Combobox(
            self.root, textvariable=self.output_port_name
        )
        self.output_dropdown["values"] = mido.get_output_names()
        self.output_dropdown.grid(row=1, column=1, padx=10, pady=5)

        # Button to start routing
        self.start_button = ttk.Button(
            self.root, text="Start", command=self.start_routing
        )
        self.start_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Button to stop routing
        self.stop_button = ttk.Button(self.root, text="Stop", command=self.stop_routing)
        self.stop_button.grid(row=3, column=0, columnspan=2, pady=10)

        # MIDI events display window
        self.event_log = tk.Text(self.root, height=10, width=50, state=tk.DISABLED)
        self.event_log.grid(row=4, column=0, columnspan=2, padx=10, pady=5)

        # Save configuration button
        self.save_button = ttk.Button(
            self.root, text="Save Configuration", command=self.save_config
        )
        self.save_button.grid(row=5, column=0, columnspan=2, pady=10)

        # Add minimize to tray button
        self.minimize_button = ttk.Button(
            self.root, text="Minimize to Tray", command=self.minimize_to_tray
        )
        self.minimize_button.grid(row=6, column=0, columnspan=2, pady=10)

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

    def create_tray_icon(self):
        # Create a blank image for the tray icon
        image = Image.new("RGB", (64, 64), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill="blue")

        # Set up tray icon and menu
        self.tray_icon = pystray.Icon(
            "midi_app",
            image,
            "MIDI App",
            menu=pystray.Menu(
                pystray.MenuItem("Show", self.show_window),
                pystray.MenuItem("Exit", self.quit_app),
            ),
        )

        # Run the tray icon in detached mode (no need to pass any custom callback here)
        self.tray_icon.run_detached()

    def minimize_to_tray(self):
        """Minimizes the window and shows the system tray icon"""
        self.hide_window()

    def hide_window(self):
        """Hides the application window"""
        self.root.withdraw()

    def show_window(self, icon=None, item=None):
        """Restores the application window from the system tray"""
        self.root.deiconify()
        self.root.attributes("-topmost", True)  # Bring window to the front
        self.root.attributes("-topmost", False)  # Restore normal behavior

    def quit_app(self):
        self.tray_icon.stop()
        self.root.quit()
        sys.exit()

    def save_config(self):
        config = {
            "input_port": self.input_port_name.get(),
            "output_port": self.output_port_name.get(),
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        messagebox.showinfo("Success", "Configuration saved!")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                input_port = config.get("input_port", "")
                output_port = config.get("output_port", "")

                # Check if the saved input and output ports are available
                if (
                    input_port in mido.get_input_names()
                    and output_port in mido.get_output_names()
                ):
                    self.input_port_name.set(input_port)
                    self.output_port_name.set(output_port)

                    # Automatically start routing if valid input/output are loaded
                    self.start_routing()
                else:
                    messagebox.showwarning(
                        "Config Error",
                        "Saved ports not available. Please select new ports.",
                    )
        else:
            messagebox.showinfo(
                "No Config",
                "No configuration found. Please set up input and output ports.",
            )


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
    root = tk.Tk()
    app = MidiApp(root, start_minimized=args.minimized)
    root.mainloop()


# <a href="https://www.flaticon.com/free-icons/plug" title="plug icons">Plug icons created by Freepik - Flaticon</a>
