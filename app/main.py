"""Application entry point with stub Tkinter app."""
import tkinter as tk
from tkinter import ttk
from ui.views.inspection_view import InspectionView
from ui.views.query_view import QueryView


def main():
    root = tk.Tk()
    root.title("Multi-Camera Inspection")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    inspection = InspectionView(notebook)
    notebook.add(inspection.frame, text="Inspection")

    query = QueryView(notebook)
    notebook.add(query.frame, text="Review")

    root.mainloop()


if __name__ == "__main__":
    main()
