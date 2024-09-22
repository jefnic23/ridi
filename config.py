import json
from os import path
from tkinter import StringVar, messagebox

from theme import Theme

CONFIG_FILE = "config.json"


def save_config(input_port_name: StringVar, output_port_name: StringVar, theme: Theme):
    config = {
        "input_port": input_port_name.get(),
        "output_port": output_port_name.get(),
        "theme": theme.current_theme,
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)
    messagebox.showinfo("Success", "Configuration saved!")


def load_config(
    input_port_name: StringVar,
    output_port_name: StringVar,
    input_names: list[str],
    output_names: list[str],
    theme: Theme,
    callback: callable,
) -> None:
    if path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            input_port = config.get("input_port", "")
            output_port = config.get("output_port", "")
            theme_name = config.get("theme", "")

            if theme_name:
                theme.change_theme(theme_name=theme_name)

            # Check if the saved input and output ports are available
            if input_port in input_names and output_port in output_names:
                input_port_name.set(input_port)
                output_port_name.set(output_port)

                callback()
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
