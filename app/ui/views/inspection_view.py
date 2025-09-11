"""Inspection view displaying 2x3 camera grid with ROI overlay."""
import tkinter as tk
from tkinter import ttk


class InspectionView:
    """Simple 2x3 grid for camera previews."""

    def __init__(self, master):
        self.frame = ttk.Frame(master)
        self.labels = []
        for i in range(2):
            for j in range(3):
                lbl = tk.Label(self.frame, text=f"CAM{(i*3)+j+1}", borderwidth=2, relief="groove", width=20, height=10)
                lbl.grid(row=i, column=j, padx=2, pady=2, sticky="nsew")
                self.labels.append(lbl)
        for i in range(2):
            self.frame.rowconfigure(i, weight=1)
        for j in range(3):
            self.frame.columnconfigure(j, weight=1)
