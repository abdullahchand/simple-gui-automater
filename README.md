# Simple GUI Automater

A record/playback GUI automation tool for Ubuntu (X11) that matches screen
content instead of blindly replaying coordinates:

- **Click** — drag a box around a button/icon once; playback finds that exact
  image on screen (template matching) and clicks it, wherever it currently is.
- **Type** — drag a box around a field to click into, then type text. Text can
  include dynamic tokens: `{today}`, `{today+1}`, `{today-3}`, formatted with
  a strftime pattern you choose (default `%Y-%m-%d`).
- **Select** — drag a box around the closed control (dropdown/date field),
  then (after a short countdown, during which you open it yourself) drag a
  box around the options/calendar area. At playback, the control is clicked,
  the options area is OCR'd, and the resolved value (e.g. today's day number)
  is located and clicked — so "select today's date" works even though the
  actual date changes every day.

## Setup

```bash
sudo apt install tesseract-ocr python3-tk   # system deps (OCR engine + Tk)
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Run

```bash
gui-automater
```

(`pip install -e .` puts this command on your PATH inside the venv. If you'd
rather not install it as a package, `python3 run.py` still works the same way.)

You'll be asked to choose/create a project folder (holds `project.json` +
captured template images). Then use the toolbar to add Click/Type/Select
steps, reorder/delete them, save, and Run All / Run From Selected.

Move the mouse to any screen corner during playback to abort immediately
(PyAutoGUI fail-safe).

## Notes / current limitations

- Requires X11 (not Wayland) for screen capture and synthetic input.
- Template matching does a small scale sweep to tolerate minor DPI/zoom
  drift, but a control that's totally re-styled between record and playback
  won't match — re-record that step.
- OCR select matching is exact-word-first, falling back to substring; very
  small/blurry text may need the app zoomed in or a tighter search box.
