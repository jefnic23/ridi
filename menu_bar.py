from tkinter import Menu, StringVar, Tk

import mido

from config import save_config
from theme import Theme


class MenuBar(Menu):
    def __init__(
        self,
        parent: Tk,
        input_port_name: StringVar,
        output_port_name: StringVar,
        theme: Theme,
        quit_callback: callable,
    ):
        super().__init__(parent)

        parent.config(menu=self)

        # File menu
        file_menu = Menu(self, tearoff=0)
        file_menu.add_command(
            label="Save Configuration",
            command=lambda: save_config(
                input_port_name=input_port_name,
                output_port_name=output_port_name,
                theme=theme,
            ),
        )
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=quit_callback)
        self.add_cascade(label="File", menu=file_menu)

        # MIDI menu
        midi_menu = Menu(self, tearoff=0)
        self.add_cascade(label="MIDI", menu=midi_menu)

        # MIDI Input Selection
        midi_input_menu = Menu(midi_menu, tearoff=0)
        midi_menu.add_cascade(label="Select MIDI Input", menu=midi_input_menu)
        midi_input_menu.delete(0, "end")  # Clear existing entries
        available_inputs = mido.get_input_names()
        for input_port in available_inputs:
            midi_input_menu.add_radiobutton(
                label=input_port, variable=input_port_name, value=input_port
            )

        # MIDI Output Selection
        midi_output_menu = Menu(midi_menu, tearoff=0)
        midi_menu.add_cascade(label="Select MIDI Output", menu=midi_output_menu)
        midi_output_menu.delete(0, "end")  # Clear existing entries
        available_outputs = mido.get_output_names()
        for output_port in available_outputs:
            midi_output_menu.add_radiobutton(
                label=output_port, variable=output_port_name, value=output_port
            )

        # Create the "Themes" menu
        themes_menu = Menu(self, tearoff=0)
        self.add_cascade(label="Themes", menu=themes_menu)
        themes_menu.delete(0, "end")  # Clear existing entries
        for theme_name in theme.theme_names():
            themes_menu.add_radiobutton(
                label=theme_name,
                variable=theme.current_theme,
                command=lambda t=theme_name: theme.change_theme(t),
            )
