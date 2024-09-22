from PIL import ImageFile
from pystray import Icon, Menu, MenuItem


class TrayIcon(Icon):
    def __init__(self, icon: ImageFile, show_action: callable, quit_action: callable):
        super().__init__(
            name="ridi",
            icon=icon,
            title="RIDI",
            menu=Menu(
                MenuItem(text="Show", action=show_action),
                MenuItem(text="Quit", action=quit_action),
            ),
        )

        self.run()
