import tkinter as tk


def select_region(root, prompt: str = "Drag to select a region  (Esc to cancel)"):
    """Blocking region picker. Returns (x, y, w, h) in screen coords, or None."""
    result = {"bbox": None}

    top = tk.Toplevel(root)
    top.attributes("-fullscreen", True)
    top.attributes("-alpha", 0.25)
    top.attributes("-topmost", True)
    top.configure(bg="grey")
    top.focus_force()

    canvas = tk.Canvas(top, cursor="cross", bg="grey", highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_text(
        20, 20, anchor="nw", fill="yellow", font=("Sans", 14, "bold"), text=prompt
    )

    state = {"x0": 0, "y0": 0, "rect": None}

    def on_press(event):
        state["x0"], state["y0"] = event.x_root, event.y_root
        state["rect"] = canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="red", width=2
        )

    def on_drag(event):
        if state["rect"] is not None:
            x0, y0 = canvas.canvasx(0), canvas.canvasy(0)
            start_x = state["x0"] - top.winfo_rootx()
            start_y = state["y0"] - top.winfo_rooty()
            canvas.coords(state["rect"], start_x, start_y, event.x, event.y)

    def on_release(event):
        x1, y1 = state["x0"], state["y0"]
        x2, y2 = event.x_root, event.y_root
        x, y = min(x1, x2), min(y1, y2)
        w, h = abs(x2 - x1), abs(y2 - y1)
        if w > 3 and h > 3:
            result["bbox"] = (x, y, w, h)
        top.destroy()

    def on_escape(_event):
        result["bbox"] = None
        top.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    top.bind("<Escape>", on_escape)

    top.grab_set()
    root.wait_window(top)
    return result["bbox"]


def countdown(root, seconds: int, message: str):
    """Blocking on-screen countdown, e.g. to give the user time to open a
    dropdown/calendar manually before the next capture."""
    top = tk.Toplevel(root)
    top.overrideredirect(True)
    top.attributes("-topmost", True)
    top.configure(bg="black")
    label = tk.Label(
        top, fg="yellow", bg="black", font=("Sans", 18, "bold"), padx=20, pady=12
    )
    label.pack()
    top.update_idletasks()
    sw, sh = top.winfo_screenwidth(), top.winfo_screenheight()
    w, h = top.winfo_width(), top.winfo_height()
    top.geometry(f"+{(sw - w) // 2}+{40}")

    remaining = {"n": seconds}

    def tick():
        label.config(text=f"{message} {remaining['n']}...")
        if remaining["n"] <= 0:
            top.destroy()
            return
        remaining["n"] -= 1
        top.after(1000, tick)

    tick()
    root.wait_window(top)
