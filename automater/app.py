import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from . import actions as A
from . import capture, overlay, player
from .project import Project

RESTORE_DELAY_MS = 350  # time to let the window manager actually hide our window


def ask_form(parent, title, fields):
    """fields: list of dicts with keys: key, label, default, kind ('entry'|'choice'),
    options (for 'choice'). Returns a dict of values, or None if cancelled."""
    result = {"values": None}
    top = tk.Toplevel(parent)
    top.title(title)
    top.attributes("-topmost", True)
    top.resizable(False, False)
    top.grab_set()

    widgets = {}
    for i, f in enumerate(fields):
        tk.Label(top, text=f["label"]).grid(row=i, column=0, sticky="w", padx=8, pady=6)
        if f["kind"] == "choice":
            var = tk.StringVar(value=f.get("default", f["options"][0]))
            frame = tk.Frame(top)
            frame.grid(row=i, column=1, sticky="w", padx=8, pady=6)
            for opt in f["options"]:
                tk.Radiobutton(frame, text=opt, variable=var, value=opt).pack(side="left")
            widgets[f["key"]] = var
        else:
            var = tk.StringVar(value=f.get("default", ""))
            entry = tk.Entry(top, textvariable=var, width=32)
            entry.grid(row=i, column=1, padx=8, pady=6)
            widgets[f["key"]] = var

    def on_ok():
        result["values"] = {k: v.get() for k, v in widgets.items()}
        top.destroy()

    def on_cancel():
        result["values"] = None
        top.destroy()

    btns = tk.Frame(top)
    btns.grid(row=len(fields), column=0, columnspan=2, pady=10)
    tk.Button(btns, text="OK", width=10, command=on_ok).pack(side="left", padx=5)
    tk.Button(btns, text="Cancel", width=10, command=on_cancel).pack(side="left", padx=5)

    top.bind("<Return>", lambda _e: on_ok())
    top.bind("<Escape>", lambda _e: on_cancel())
    top.update_idletasks()
    sw, sh = top.winfo_screenwidth(), top.winfo_screenheight()
    w, h = top.winfo_width(), top.winfo_height()
    top.geometry(f"+{(sw - w) // 2}+{(sh - h) // 3}")

    parent.wait_window(top)
    return result["values"]


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple GUI Automater")
        self.project = None

        self._build_ui()
        self._new_project_prompt()

    # -- UI ---------------------------------------------------------------
    def _build_ui(self):
        toolbar = tk.Frame(self.root)
        toolbar.pack(side="top", fill="x", padx=6, pady=6)

        tk.Button(toolbar, text="+ Click", command=self.add_click).pack(side="left", padx=3)
        tk.Button(toolbar, text="+ Type", command=self.add_type).pack(side="left", padx=3)
        tk.Button(toolbar, text="+ Select", command=self.add_select).pack(side="left", padx=3)
        tk.Button(toolbar, text="Delete", command=self.delete_step).pack(side="left", padx=3)
        tk.Button(toolbar, text="Up", command=lambda: self.move_step(-1)).pack(side="left", padx=3)
        tk.Button(toolbar, text="Down", command=lambda: self.move_step(1)).pack(side="left", padx=3)

        toolbar2 = tk.Frame(self.root)
        toolbar2.pack(side="top", fill="x", padx=6, pady=(0, 6))
        tk.Button(toolbar2, text="Open Project", command=self.open_project).pack(side="left", padx=3)
        tk.Button(toolbar2, text="Save Project", command=self.save_project).pack(side="left", padx=3)
        tk.Button(toolbar2, text="Run All", command=self.run_all).pack(side="left", padx=3)
        tk.Button(toolbar2, text="Run From Selected", command=self.run_from_selected).pack(side="left", padx=3)

        self.listbox = tk.Listbox(self.root, width=80, height=18)
        self.listbox.pack(side="top", fill="both", expand=True, padx=6, pady=6)

        self.status = tk.Label(self.root, text="No project open.", anchor="w")
        self.status.pack(side="bottom", fill="x", padx=6, pady=4)

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for i, step in enumerate(self.project.steps):
            self.listbox.insert(tk.END, f"{i + 1}. {A.summary(step)}")
        self.status.config(text=f"Project: {self.project.path}  ({len(self.project.steps)} steps)")

    # -- project management -------------------------------------------------
    def _new_project_prompt(self):
        path = filedialog.askdirectory(title="Choose a folder for this automation project")
        if not path:
            path = "."
        self.project = Project(path)
        self.project.ensure_dirs()
        self._refresh_list()

    def open_project(self):
        path = filedialog.askdirectory(title="Open project folder")
        if not path:
            return
        try:
            self.project = Project.load(path)
        except FileNotFoundError:
            messagebox.showerror("Not found", "No project.json in that folder.")
            return
        self._refresh_list()

    def save_project(self):
        if self.project is None:
            return
        self.project.save()
        messagebox.showinfo("Saved", f"Project saved to {self.project.json_path}")

    # -- step editing ---------------------------------------------------------
    def selected_index(self):
        sel = self.listbox.curselection()
        return sel[0] if sel else None

    def delete_step(self):
        i = self.selected_index()
        if i is None:
            return
        del self.project.steps[i]
        self._refresh_list()

    def move_step(self, delta):
        i = self.selected_index()
        if i is None:
            return
        j = i + delta
        if 0 <= j < len(self.project.steps):
            self.project.steps[i], self.project.steps[j] = self.project.steps[j], self.project.steps[i]
            self._refresh_list()
            self.listbox.selection_set(j)

    # -- helpers to grab a region while our own window stays out of the way ---
    def _pick_region(self, prompt):
        self.root.iconify()
        self.root.update()
        time.sleep(RESTORE_DELAY_MS / 1000)
        bbox = overlay.select_region(self.root, prompt)
        return bbox

    def _restore(self):
        self.root.deiconify()
        self.root.lift()

    # -- add step: click -------------------------------------------------------
    def add_click(self):
        bbox = self._pick_region("Drag a box around the thing to CLICK  (Esc to cancel)")
        if bbox is None:
            self._restore()
            return
        img = capture.grab(bbox)
        self._restore()

        values = ask_form(
            self.root,
            "Click action",
            [
                {"key": "click_type", "label": "Click type", "kind": "choice",
                 "options": ["left", "double", "right"], "default": "left"},
                {"key": "label", "label": "Label (optional)", "kind": "entry", "default": ""},
            ],
        )
        if values is None:
            return

        path = self.project.new_image_path("click")
        self.project.save_image(path, img)
        step = A.ClickAction(template_path=path, click_type=values["click_type"], label=values["label"])
        self.project.steps.append(step)
        self._refresh_list()

    # -- add step: type ---------------------------------------------------------
    def add_type(self):
        bbox = self._pick_region("Drag a box around the field to CLICK before typing  (Esc to cancel)")
        if bbox is None:
            self._restore()
            return
        img = capture.grab(bbox)
        self._restore()

        values = ask_form(
            self.root,
            "Type action",
            [
                {"key": "text", "label": "Text to type (use {today}, {today+1}, {today-2}...)",
                 "kind": "entry", "default": ""},
                {"key": "date_format", "label": "Date format (strftime)", "kind": "entry",
                 "default": "%Y-%m-%d"},
                {"key": "label", "label": "Label (optional)", "kind": "entry", "default": ""},
            ],
        )
        if values is None:
            return

        path = self.project.new_image_path("type")
        self.project.save_image(path, img)
        step = A.TypeAction(
            template_path=path, text=values["text"], date_format=values["date_format"],
            label=values["label"],
        )
        self.project.steps.append(step)
        self._refresh_list()

    # -- add step: select (dropdown / date picker) -------------------------------
    def add_select(self):
        bbox1 = self._pick_region("Drag a box around the CLOSED control (what you click to open it)  (Esc to cancel)")
        if bbox1 is None:
            self._restore()
            return
        control_img = capture.grab(bbox1)

        overlay.countdown(
            self.root, 3,
            "Now manually open the dropdown/calendar. Capturing the options area in",
        )

        bbox2 = self._pick_region("Drag a box around the OPTIONS/CALENDAR area now showing  (Esc to cancel)")
        self._restore()
        if bbox2 is None:
            return

        dx = bbox2[0] - bbox1[0]
        dy = bbox2[1] - bbox1[1]
        search_offset = (dx, dy, bbox2[2], bbox2[3])

        values = ask_form(
            self.root,
            "Select action",
            [
                {"key": "value", "label": "Value to select (use {today}, {today+1}, {today-2}...)",
                 "kind": "entry", "default": "{today}"},
                {"key": "date_format", "label": "Date/text format (strftime, e.g. %d for day-number grids)",
                 "kind": "entry", "default": "%d"},
                {"key": "open_delay", "label": "Delay after opening, seconds", "kind": "entry", "default": "0.6"},
                {"key": "label", "label": "Label (optional)", "kind": "entry", "default": ""},
            ],
        )
        if values is None:
            return

        path = self.project.new_image_path("select")
        self.project.save_image(path, control_img)
        step = A.SelectAction(
            control_template_path=path,
            search_offset=search_offset,
            value=values["value"],
            date_format=values["date_format"],
            open_delay=float(values["open_delay"] or 0.6),
            label=values["label"],
        )
        self.project.steps.append(step)
        self._refresh_list()

    # -- playback ---------------------------------------------------------------
    def _run(self, steps):
        if not steps:
            return
        self.root.iconify()

        def worker():
            time.sleep(1.2)  # let the window manager hand focus back to the target app
            err = None
            try:
                player.run_sequence(steps)
            except Exception as e:  # noqa: BLE001 - surfaced to the user below
                err = e
            self.root.after(0, lambda: self._finish_run(err))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_run(self, err):
        self._restore()
        if err:
            messagebox.showerror("Playback failed", str(err))
        else:
            messagebox.showinfo("Done", "Playback finished.")

    def run_all(self):
        self._run(list(self.project.steps))

    def run_from_selected(self):
        i = self.selected_index()
        if i is None:
            i = 0
        self._run(list(self.project.steps[i:]))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()
