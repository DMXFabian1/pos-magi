# utils/tooltips.py
import tkinter as tk

class ToolTip:
    """Clase para crear tooltips (descripciones emergentes) en widgets de Tkinter."""
    def __init__(self, widget, text, delay=500, bg_color="#FFFFE0", font=("Helvetica", 10)):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.bg_color = bg_color
        self.font = font
        self.tooltip_window = None
        self.id = None
        self.widget.bind("<Enter>", self.schedule_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def schedule_tooltip(self, event=None):
        self.id = self.widget.after(self.delay, self.show_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window, text=self.text, background=self.bg_color, relief="solid", borderwidth=1, font=self.font)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None