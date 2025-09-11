"""Query/Review view with basic filtering and list."""
import tkinter as tk
from tkinter import ttk
from pathlib import Path


class QueryView:
    """Provides simple date and OK/NG filtering."""

    def __init__(self, master):
        self.frame = ttk.Frame(master)
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill="x")

        self.date_var = tk.StringVar()
        self.result_var = tk.StringVar()

        ttk.Label(control_frame, text="Date:").pack(side="left")
        ttk.Entry(control_frame, textvariable=self.date_var, width=10).pack(side="left")
        ttk.Label(control_frame, text="Result:").pack(side="left")
        ttk.Combobox(control_frame, textvariable=self.result_var, values=["", "OK", "NG"], width=5).pack(side="left")
        ttk.Button(control_frame, text="Refresh", command=self.refresh).pack(side="left")

        self.listbox = tk.Listbox(self.frame)
        self.listbox.pack(fill="both", expand=True)

    def refresh(self):
        """Refresh the file list based on filters."""
        self.listbox.delete(0, tk.END)
        root = Path("./captures")
        if not root.exists():
            return
        for file in sorted(root.glob("*.jpg")):
            if self.result_var.get() and self.result_var.get() not in file.stem:
                continue
            self.listbox.insert(tk.END, file.name)
