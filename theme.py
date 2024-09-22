from tkinter import ttk


class Theme(ttk.Style):
    def __init__(self):
        super().__init__()

        self.current_theme: str = self.theme_use()

    def change_theme(self, theme_name):
        self.current_theme = theme_name
        self.theme_use(theme_name)
