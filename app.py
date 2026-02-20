"""
Music Concierge Support Dashboard
==================================
A lightweight customtkinter-based support dashboard.
"""

import os
import re
import sys
import tkinter as tk
from datetime import datetime
from tkinter import Canvas
from xml.etree import ElementTree as ET

import customtkinter as ctk

import customtkinter as ctk

# ── Theme ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Minimalist Palette ─────────────────────────────────────────────────────────
BG_COLOR      = "#1A1A1A"  # Simple dark background
CARD_BG       = "#242424"  # Slightly lighter for cards
SIDEBAR_BG    = "#141414"  # Sidebar background
ACCENT        = "#B87D4B"  # Muted accent
TEXT_DIM      = "#888888"  # Dimmed text
TEXT_BRIGHT   = "#E0E0E0"  # Bright text
TEXT_GREEN    = "#4CAF50"  # Green status
TEXT_RED      = "#EF5350"  # Red status
DIVIDER       = "#333333"  # Divider lines
CORNER        = 6          # Smaller corner radius
SIDEBAR_W     = 200        # Narrower sidebar

KV_BASE     = r"C:\Kaleidovision\config\kv"

# ── Folder-name datetime parser ────────────────────────────────────────────────
# Format: YYYY-MM-DD-HHMM  e.g. 2025-10-02-0242  → 2025-10-02 02:42
_FOLDER_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(\d{2})(\d{2})$")


def _folder_datetime(name: str):
    """Return a datetime for a folder name matching YYYY-MM-DD-HHMM, else None."""
    m = _FOLDER_RE.match(name)
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                        int(m.group(4)), int(m.group(5)))
    except ValueError:
        return None


def find_latest_xml_file(filename: str, base: str = KV_BASE):
    """
    Scan *base* for sub-folders matching YYYY-MM-DD-HHMM, pick the latest
    by datetime, and return (folder_name, full_path_to_xml_file).
    Returns (None, None) if nothing is found.
    """
    if not os.path.isdir(base):
        return None, None
    candidates = []
    for entry in os.scandir(base):
        if not entry.is_dir():
            continue
        dt = _folder_datetime(entry.name)
        if dt is not None:
            candidates.append((dt, entry.name))
    if not candidates:
        return None, None
    candidates.sort(key=lambda x: x[0], reverse=True)
    latest_name = candidates[0][1]
    xml_path = os.path.join(base, latest_name, filename)
    return latest_name, xml_path


def find_latest_cores_xml(base: str = KV_BASE):
    """Wrapper for backwards compatibility."""
    return find_latest_xml_file("cores.xml", base)


def pretty_xml(xml_path: str):
    """Return (readable_text, raw_xml) from a cores.xml file."""
    try:
        with open(xml_path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()
    except OSError as e:
        return f"[Error reading file: {e}]", ""

    # Build readable summary by walking the XML tree
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        return f"[XML parse error: {e}]", raw

    lines = []
    lines.append(f"Root element : <{root.tag}>")
    if root.attrib:
        for k, v in root.attrib.items():
            lines.append(f"  @{k} = {v}")
    lines.append("")

    def walk(el, depth=0):
        indent = "  " * depth
        attribs = "  ".join(f"{k}={v}" for k, v in el.attrib.items())
        text = (el.text or "").strip()
        row = f"{indent}<{el.tag}>"
        if attribs:
            row += f"  [{attribs}]"
        if text:
            row += f"  {text}"
        lines.append(row)
        for child in el:
            walk(child, depth + 1)

    for child in root:
        walk(child)

    return "\n".join(lines), raw


# ── Simple background (no gradient) ───────────────────────────────────────────
def set_background(canvas: Canvas, width: int, height: int):
    """Set solid background color."""
    canvas.delete("all")
    canvas.create_rectangle(0, 0, width, height, fill=BG_COLOR, outline="")


# ── Stat Card ──────────────────────────────────────────────────────────────────
class StatCard(ctk.CTkFrame):
    def __init__(self, master, title: str, value: str,
                 change: str, positive: bool = True, **kw):
        super().__init__(master, corner_radius=CORNER, fg_color=CARD_BG, **kw)
        self.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text=title.upper(),
            font=ctk.CTkFont(size=10), text_color=TEXT_DIM, anchor="w"
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 2))

        ctk.CTkLabel(
            self, text=value,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=TEXT_BRIGHT, anchor="w"
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=2)

        ctk.CTkLabel(
            self, text=change,
            font=ctk.CTkFont(size=11),
            text_color=TEXT_GREEN if positive else TEXT_RED, anchor="w"
        ).grid(row=2, column=0, sticky="ew", padx=14, pady=(2, 14))


# ── Shortcut Button ────────────────────────────────────────────────────────────
class ShortcutButton(ctk.CTkButton):
    def __init__(self, master, label: str, icon: str = "[ ]", **kw):
        super().__init__(
            master,
            text=f"{icon}\n{label}",
            font=ctk.CTkFont(size=11),
            fg_color="#2A1E1A",
            hover_color="#3D2B22",
            text_color=TEXT_BRIGHT,
            corner_radius=CORNER,
            width=100,
            height=80,
            **kw,
        )


# ── Sidebar ────────────────────────────────────────────────────────────────────
class Sidebar(ctk.CTkFrame):
    _NAV = [
        ("⌂", "Overview"),
        ("📁", "C:\\Kaleidovision"),
        ("🔊", "Sound Device Setting"),
        ("🔓", "Unlock Windows Shell"),
        ("📊", "Windows Reliability Reports"),
        ("📝", "Windows Event Viewer"),
        ("❌", "Quit MC Support Dashboard"),
    ]

    def __init__(self, master, on_navigate=None, **kw):
        super().__init__(master, width=SIDEBAR_W, corner_radius=0,
                         fg_color=SIDEBAR_BG, **kw)
        self.pack_propagate(False)
        self._on_navigate = on_navigate or (lambda page: None)
        self._buttons = {}
        self._active = "Overview"
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self, text="🎵  MC Support",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ACCENT, anchor="w"
        ).pack(fill="x", padx=18, pady=(28, 2))

        # Live time display under title
        self._date_lbl = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_BRIGHT, anchor="w"
        )
        self._date_lbl.pack(fill="x", padx=18, pady=(0, 0))

        self._time_lbl = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ACCENT, anchor="w"
        )
        self._time_lbl.pack(fill="x", padx=18, pady=(0, 0))

        self._tz_lbl = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=10),
            text_color=TEXT_DIM, anchor="w"
        )
        self._tz_lbl.pack(fill="x", padx=18, pady=(0, 8))

        ctk.CTkFrame(self, height=1, fg_color=DIVIDER).pack(fill="x", padx=12, pady=(0, 16))

        for icon, label in self._NAV:
            is_active = (label == self._active)
            btn = ctk.CTkButton(
                self,
                text=f"{icon} {label}",
                font=ctk.CTkFont(size=13),
                fg_color="#2E1F1A" if is_active else "transparent",
                hover_color="#2E1F1A",
                text_color=ACCENT if is_active else TEXT_BRIGHT,
                anchor="w",
                corner_radius=8,
                height=40,
                command=lambda l=label: self._navigate(l),
            )
            btn.pack(fill="x", padx=(10, 0), pady=2)
            self._buttons[label] = btn

        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)
        ctk.CTkFrame(self, height=1, fg_color=DIVIDER).pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(
            self, text="👤  Agent: You",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM, anchor="w"
        ).pack(fill="x", padx=18, pady=(0, 22))

    def update_time(self):
        from datetime import datetime, timezone
        import time
        now = datetime.now()
        # Get timezone offset in hours (e.g., +7 for Bangkok)
        tz_offset_hours = -time.timezone // 3600 if time.daylight == 0 else -time.altzone // 3600
        tz_offset_str = f"{tz_offset_hours:+d}"
        self._date_lbl.configure(text=now.strftime("(%A) %d/%m/%Y"))
        self._time_lbl.configure(text=now.strftime("%I:%M:%S %p").lstrip("0"))
        self._tz_lbl.configure(text=f"{time.tzname[0] if time.daylight == 0 else time.tzname[1]} ({tz_offset_str})")

    def _navigate(self, label: str):
        # Handle special launch cases
        if label == "C:\\Kaleidovision":
            self._launch_kaleidovision()
            return
        elif label == "Quit MC Support Dashboard":
            self._confirm_quit()
            return
        
        # Always keep Overview highlighted, others remain unhighlighted
        for name, btn in self._buttons.items():
            if name == "Overview":
                btn.configure(fg_color="#2E1F1A", text_color=ACCENT)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_BRIGHT)
        self._active = "Overview"  # Always keep Overview as active
        self._on_navigate(label)
    
    def _launch_kaleidovision(self):
        """Launch Kaleidovision directory, trying both cases"""
        import subprocess
        import os
        
        # Try both cases for the directory
        paths_to_try = [
            "C:\\Kaleidovision",
            "C:\\kaleidovision"
        ]
        
        for path in paths_to_try:
            if os.path.exists(path):
                try:
                    subprocess.Popen(['explorer', path])
                    return
                except Exception:
                    pass
        
        # If neither exists, show error
        try:
            subprocess.Popen(['explorer', 'C:\\'])  # Open C: drive as fallback
        except Exception:
            pass
    
    def _confirm_quit(self):
        """Show confirmation dialog before quitting"""
        import customtkinter as ctk
        
        # Create confirmation dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Quit")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        # Content
        ctk.CTkLabel(
            dialog,
            text="Are you sure you want to quit?",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            dialog,
            text="This will close the MC Support Dashboard.",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        ).pack(pady=(0, 20))
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=10)
        
        ctk.CTkButton(
            button_frame,
            text="Quit",
            width=100,
            fg_color="#FF5722",
            hover_color="#FF7043",
            command=lambda: self._quit_application()
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=100,
            fg_color="#333333",
            hover_color="#555555",
            command=dialog.destroy
        ).pack(side="left", padx=10)
    
    def _quit_application(self):
        """Actually quit the application"""
        import os
        # Get the root window and close it
        root = self.winfo_toplevel()
        try:
            root.destroy()
        except:
            pass
        # Force exit if destroy doesn't work
        os._exit(0)


# ── Weather Widget ─────────────────────────────────────────────────────────────
class WeatherWidget(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        ctk.CTkLabel(
            self, text="McLean, VA",
            font=ctk.CTkFont(size=12), text_color=TEXT_DIM
        ).pack(anchor="e")
        ctk.CTkLabel(
            self, text="68°",
            font=ctk.CTkFont(size=34), text_color=TEXT_BRIGHT
        ).pack(anchor="e")
        ctk.CTkLabel(
            self, text="☀  Partly Cloudy",
            font=ctk.CTkFont(size=11), text_color=TEXT_DIM
        ).pack(anchor="e")


# ── Recent Activity Row ────────────────────────────────────────────────────────
class ActivityRow(ctk.CTkFrame):
    def __init__(self, master, time: str, client: str, action: str,
                 status: str, status_ok: bool = True, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.columnconfigure((0, 1, 2, 3), weight=1)

        for col, (text, color) in enumerate([
            (time,   TEXT_DIM),
            (client, TEXT_BRIGHT),
            (action, TEXT_DIM),
            (status, TEXT_GREEN if status_ok else TEXT_RED),
        ]):
            ctk.CTkLabel(
                self, text=text, font=ctk.CTkFont(size=12),
                text_color=color, anchor="w"
            ).grid(row=0, column=col, sticky="ew", padx=6, pady=4)


class ConfigXMLPage(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()

    def _build(self):
        # ── Page title bar with buttons ─────────────────────────────────────────
        title_bar = ctk.CTkFrame(self, fg_color="transparent")
        title_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 4))
        title_bar.columnconfigure(0, weight=1)
        title_bar.columnconfigure(1, weight=0)

        # Left side: title and source path
        left_frame = ctk.CTkFrame(title_bar, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w")
        left_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_frame, text="Config.XML Viewer",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_BRIGHT, anchor="w"
        ).grid(row=0, column=0, sticky="w")

        self._source_lbl = ctk.CTkLabel(
            left_frame, text="Scanning…",
            font=ctk.CTkFont(size=11), text_color=TEXT_DIM, anchor="w"
        )
        self._source_lbl.grid(row=1, column=0, sticky="w")

        # Right side: buttons
        btn_frame = ctk.CTkFrame(title_bar, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            btn_frame, text="📋 Copy Cores.XML Texts",
            fg_color="#2A1E1A", hover_color="#3D2B22",
            text_color=TEXT_BRIGHT, font=ctk.CTkFont(size=12),
            corner_radius=8, height=34, width=130,
            command=self._copy_content,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="⟳ Refresh",
            fg_color=ACCENT, hover_color="#A06840",
            text_color="#1A0F0A", font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8, height=34, width=100,
            command=self._load,
        ).pack(side="left")

        # ── Tab view ───────────────────────────────────────────────────────────
        tab_container = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=CORNER)
        tab_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))
        tab_container.columnconfigure(0, weight=1)
        tab_container.rowconfigure(1, weight=1)

        # Tab selector row
        tab_sel = ctk.CTkFrame(tab_container, fg_color="transparent")
        tab_sel.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 0))

        self._tab_readable_btn = ctk.CTkButton(
            tab_sel, text="Readable View",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=ACCENT, hover_color="#A06840",
            text_color="#1A0F0A", corner_radius=6, height=30, width=140,
            command=lambda: self._switch_tab("readable"),
        )
        self._tab_readable_btn.pack(side="left", padx=(0, 6))

        self._tab_raw_btn = ctk.CTkButton(
            tab_sel, text="Raw XML",
            font=ctk.CTkFont(size=12),
            fg_color="#2A1E1A", hover_color="#3D2B22",
            text_color=TEXT_BRIGHT, corner_radius=6, height=30, width=140,
            command=lambda: self._switch_tab("raw"),
        )
        self._tab_raw_btn.pack(side="left")

        ctk.CTkFrame(tab_container, height=1, fg_color=DIVIDER).grid(
            row=0, column=0, sticky="ew", padx=0, pady=(46, 0)
        )

        # Content area — two overlapping textboxes, one shown at a time
        content = ctk.CTkFrame(tab_container, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        common = dict(
            corner_radius=8,
            fg_color="#150D0D",
            text_color=TEXT_BRIGHT,
            font=ctk.CTkFont(family="Consolas", size=12),
            border_color=DIVIDER,
            border_width=1,
            wrap="none",
            state="disabled",
        )

        self._readable_box = ctk.CTkTextbox(content, **common)
        self._readable_box.grid(row=0, column=0, sticky="nsew")

        self._raw_box = ctk.CTkTextbox(content, **common)
        self._raw_box.grid(row=0, column=0, sticky="nsew")

        self._active_tab = "readable"
        self._switch_tab("readable")
        self._load()

    def _copy_content(self):
        content = ""
        if self._active_tab == "readable":
            content = self._readable_box.get("0.0", "end")
        else:
            content = self._raw_box.get("0.0", "end")
        self.clipboard_clear()
        self.clipboard_append(content)

    def _switch_tab(self, tab: str):
        self._active_tab = tab
        if tab == "readable":
            self._readable_box.lift()
            self._tab_readable_btn.configure(fg_color=ACCENT, text_color="#1A0F0A",
                                             font=ctk.CTkFont(size=12, weight="bold"))
            self._tab_raw_btn.configure(fg_color="#2A1E1A", text_color=TEXT_BRIGHT,
                                        font=ctk.CTkFont(size=12))
        else:
            self._raw_box.lift()
            self._tab_raw_btn.configure(fg_color=ACCENT, text_color="#1A0F0A",
                                        font=ctk.CTkFont(size=12, weight="bold"))
            self._tab_readable_btn.configure(fg_color="#2A1E1A", text_color=TEXT_BRIGHT,
                                             font=ctk.CTkFont(size=12))

    def _set_textbox(self, box: ctk.CTkTextbox, content: str):
        box.configure(state="normal")
        box.delete("0.0", "end")
        box.insert("0.0", content)
        box.configure(state="disabled")

    def _load(self):
        folder_name, xml_path = find_latest_cores_xml()

        if folder_name is None:
            self._source_lbl.configure(
                text=f"Base path not found: {KV_BASE}", text_color=TEXT_RED
            )
            self._show_error_in_readable(
                f"[Directory not found]\n\nExpected base path:\n  {KV_BASE}\n\n"
                "Please ensure Kaleidovision is installed and the config folder exists.")
            self._set_textbox(self._raw_box, "")
            return

        if not os.path.isfile(xml_path):
            self._source_lbl.configure(
                text=f"cores.xml not found in: {folder_name}", text_color=TEXT_RED
            )
            self._show_error_in_readable(
                f"[File not found]\n\nLooked for:\n  {xml_path}")
            self._set_textbox(self._raw_box, "")
            return

        dt = _folder_datetime(folder_name)
        if dt:
            ts = dt.strftime("%d %b %Y at %I:%M %p")
        else:
            ts = folder_name

        self._source_lbl.configure(
            text=f"Latest config folder: {folder_name}  —  {xml_path}",
            text_color=TEXT_DIM
        )
        
        # Create stylish date badge for ConfigXMLPage
        if not hasattr(self, '_date_badge'):
            self._date_badge = ctk.CTkLabel(
                left_frame, text="",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=ACCENT,
                fg_color="#2A1E1A",
                corner_radius=6,
                padx=10, pady=4
            )
            self._date_badge.grid(row=2, column=0, sticky="w", pady=(6, 0))
        self._date_badge.configure(text=f"📅 {ts}" if dt else ts)

        readable, raw = pretty_xml(xml_path)
        self._build_readable_view(xml_path, readable)
        self._set_textbox(self._raw_box, raw)
        self._switch_tab(self._active_tab)


# ── Cores.XML Page ─────────────────────────────────────────────────────────────
class CoresXMLPage(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()

    def _load(self):
        """Load cores.xml data and build the view."""
        folder_name, xml_path = find_latest_cores_xml()

        if folder_name is None:
            self._source_lbl.configure(
                text=f"Base path not found: {KV_BASE}", text_color=TEXT_RED
            )
            self._show_error_in_readable(
                f"[Directory not found]\n\nExpected base path:\n  {KV_BASE}\n\n"
                "Please ensure Kaleidovision is installed and the config folder exists.")
            self._set_textbox(self._raw_box, "")
            return

        if not os.path.isfile(xml_path):
            self._source_lbl.configure(
                text=f"cores.xml not found in: {folder_name}", text_color=TEXT_RED
            )
            self._show_error_in_readable(
                f"[File not found]\n\nLooked for:\n  {xml_path}")
            self._set_textbox(self._raw_box, "")
            return

        dt = _folder_datetime(folder_name)
        if dt:
            ts = dt.strftime("%d %b %Y at %I:%M %p")
        else:
            ts = folder_name

        self._source_lbl.configure(
            text=f"Latest config folder: {folder_name}  —  {xml_path}",
            text_color=TEXT_DIM
        )
        
        # Create stylish date badge for CoresXMLPage
        if not hasattr(self, '_date_badge'):
            self._date_badge = ctk.CTkLabel(
                self._left_frame, text="",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=ACCENT,
                fg_color="#2A1E1A",
                corner_radius=6,
                padx=10, pady=4
            )
            self._date_badge.grid(row=2, column=0, sticky="w", pady=(6, 0))
        self._date_badge.configure(text=f"📅 Latest Cores Build Date: {ts}" if dt else f"Latest Cores Build Date: {ts}")

        readable, raw = pretty_xml(xml_path)
        self._build_readable_view(xml_path, readable)
        self._set_textbox(self._raw_box, raw)
        self._switch_tab(self._active_tab)

    def _build(self):
        # ── Page title bar with buttons ─────────────────────────────────────────
        title_bar = ctk.CTkFrame(self, fg_color="transparent")
        title_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 4))
        title_bar.columnconfigure(0, weight=1)
        title_bar.columnconfigure(1, weight=0)

        # Left side: title and source path
        left_frame = ctk.CTkFrame(title_bar, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w")
        left_frame.columnconfigure(0, weight=1)
        self._left_frame = left_frame  # Store for _load to access

        ctk.CTkLabel(
            left_frame, text="Overview",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_BRIGHT, anchor="w"
        ).grid(row=0, column=0, sticky="w")

        self._source_lbl = ctk.CTkLabel(
            left_frame, text="Scanning…",
            font=ctk.CTkFont(size=11), text_color=TEXT_DIM, anchor="w"
        )
        self._source_lbl.grid(row=1, column=0, sticky="w")

        # Right side: buttons
        btn_frame = ctk.CTkFrame(title_bar, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            btn_frame, text="📋 Copy Cores Texts",
            fg_color="#2A1E1A", hover_color="#3D2B22",
            text_color=TEXT_BRIGHT, font=ctk.CTkFont(size=12),
            corner_radius=8, height=34, width=130,
            command=self._copy_content,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="✏️ Edit Cores",
            fg_color="#2A1E1A", hover_color="#3D2B22",
            text_color=TEXT_BRIGHT, font=ctk.CTkFont(size=12),
            corner_radius=8, height=34, width=100,
            command=self._edit_cores,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="⟳ Refresh",
            fg_color=ACCENT, hover_color="#A06840",
            text_color="#1A0F0A", font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8, height=34, width=100,
            command=self._load,
        ).pack(side="left")

        # ── Tab view ───────────────────────────────────────────────────────────
        tab_container = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=CORNER)
        tab_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))
        tab_container.columnconfigure(0, weight=1)
        tab_container.rowconfigure(1, weight=1)

        # Tab selector row
        tab_sel = ctk.CTkFrame(tab_container, fg_color="transparent")
        tab_sel.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 0))

        self._tab_readable_btn = ctk.CTkButton(
            tab_sel, text="Readable View",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=ACCENT, hover_color="#A06840",
            text_color="#1A0F0A", corner_radius=6, height=30, width=140,
            command=lambda: self._switch_tab("readable"),
        )
        self._tab_readable_btn.pack(side="left", padx=(0, 6))

        self._tab_raw_btn = ctk.CTkButton(
            tab_sel, text="Raw XML",
            font=ctk.CTkFont(size=12),
            fg_color="#2A1E1A", hover_color="#3D2B22",
            text_color=TEXT_BRIGHT, corner_radius=6, height=30, width=140,
            command=lambda: self._switch_tab("raw"),
        )
        self._tab_raw_btn.pack(side="left")

        ctk.CTkFrame(tab_container, height=1, fg_color=DIVIDER).grid(
            row=0, column=0, sticky="ew", padx=0, pady=(46, 0)
        )

        # Content area — scrollable frame for readable, textbox container for raw
        # Readable tab: scrollable frame with custom UI
        self._readable_frame = ctk.CTkScrollableFrame(
            tab_container, fg_color="transparent",
            scrollbar_button_color=DIVIDER,
            scrollbar_button_hover_color=ACCENT,
        )
        self._readable_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)
        self._readable_frame.columnconfigure(0, weight=1)

        # Raw tab: textbox container
        self._raw_content_frame = ctk.CTkFrame(tab_container, fg_color="transparent")
        self._raw_content_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)
        self._raw_content_frame.columnconfigure(0, weight=1)
        self._raw_content_frame.rowconfigure(0, weight=1)

        common = dict(
            corner_radius=8,
            fg_color="#150D0D",
            text_color=TEXT_BRIGHT,
            font=ctk.CTkFont(family="Consolas", size=12),
            border_color=DIVIDER,
            border_width=1,
            wrap="none",
            state="disabled",
        )

        self._raw_box = ctk.CTkTextbox(self._raw_content_frame, **common)
        self._raw_box.grid(row=0, column=0, sticky="nsew")

        self._active_tab = "readable"
        self._switch_tab("readable")
        self._load()

    # ── Copy content to clipboard ──────────────────────────────────────────────
    def _copy_content(self):
        content = ""
        if self._active_tab == "readable":
            content = self._raw_box.get("0.0", "end")
        else:
            content = self._raw_box.get("0.0", "end")
        self.clipboard_clear()
        self.clipboard_append(content)

    # ── Tab switching ──────────────────────────────────────────────────────────
    def _switch_tab(self, tab: str):
        self._active_tab = tab
        if tab == "readable":
            self._readable_frame.lift()
            self._tab_readable_btn.configure(fg_color=ACCENT, text_color="#1A0F0A",
                                             font=ctk.CTkFont(size=12, weight="bold"))
            self._tab_raw_btn.configure(fg_color="#2A1E1A", text_color=TEXT_BRIGHT,
                                        font=ctk.CTkFont(size=12))
        else:
            self._raw_content_frame.lift()
            self._tab_raw_btn.configure(fg_color=ACCENT, text_color="#1A0F0A",
                                        font=ctk.CTkFont(size=12, weight="bold"))
            self._tab_readable_btn.configure(fg_color="#2A1E1A", text_color=TEXT_BRIGHT,
                                             font=ctk.CTkFont(size=12))

    # ── Load / Refresh ─────────────────────────────────────────────────────────
    def _set_textbox(self, box: ctk.CTkTextbox, content: str):
        box.configure(state="normal")
        box.delete("0.0", "end")
        box.insert("0.0", content)
        box.configure(state="disabled")

    def _clear_readable_frame(self):
        """Remove all widgets from the readable frame."""
        for widget in self._readable_frame.winfo_children():
            widget.destroy()

    def _show_error_in_readable(self, message: str):
        """Display an error message in the readable frame."""
        self._clear_readable_frame()
        ctk.CTkLabel(
            self._readable_frame, text=message,
            font=ctk.CTkFont(size=12), text_color=TEXT_RED
        ).grid(row=0, column=0, sticky="w")

    def _extract_mcservice_url(self, root) -> str | None:
        """Extract the URL from McServiceApp's misc settings."""
        for kvcore in root.findall("KvCore"):
            if kvcore.get("APPLICATION") == "McServiceApp":
                programs = kvcore.find("Programs")
                if programs is not None:
                    program = programs.find("Program")
                    if program is not None:
                        settings = program.find("Settings")
                        if settings is not None:
                            misc = settings.find("misc")
                            if misc is not None:
                                return misc.get("url")
        return None

    def _edit_cores(self):
        """Open the cores.xml file in Notepad after password verification."""
        import subprocess
        
        # Create password dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Password Required")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.configure(fg_color="#1A0F0A")
        
        # Center the dialog
        dialog.update_idletasks()
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        x = (sw - 400) // 2
        y = (sh - 250) // 2
        dialog.geometry(f"400x250+{x}+{y}")
        
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        
        # Content frame
        frame = ctk.CTkFrame(dialog, fg_color=CARD_BG, corner_radius=CORNER)
        frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=0)  # Password entry row
        
        # Warning message
        ctk.CTkLabel(
            frame,
            text="🔐 Password Required",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ACCENT, anchor="center"
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            frame,
            text="Enter password to edit cores.xml:",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_BRIGHT, anchor="center", justify="center"
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        
        # Password entry
        password_entry = ctk.CTkEntry(
            frame,
            font=ctk.CTkFont(size=12),
            fg_color="#2A1E1A",
            border_color=DIVIDER,
            border_width=1,
            show="*"
        )
        password_entry.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        # Button frame
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        
        def on_submit():
            if password_entry.get() == _get_edit_cores_password():
                folder_name, xml_path = find_latest_cores_xml()
                if xml_path and os.path.isfile(xml_path):
                    subprocess.Popen(["notepad.exe", xml_path])
                dialog.destroy()
            else:
                # Show error message
                password_entry.delete(0, "end")
                password_entry.configure(border_color="#FF6B35")
                dialog.after(1500, lambda: password_entry.configure(border_color=DIVIDER))
        
        def on_cancel():
            dialog.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="Submit",
            font=ctk.CTkFont(size=12),
            fg_color=ACCENT,
            hover_color="#E8A87C",
            text_color="#1A0F0A",
            width=100,
            height=35,
            command=on_submit
        ).grid(row=0, column=0, sticky="e", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=ctk.CTkFont(size=12),
            fg_color=DIVIDER,
            hover_color=ACCENT,
            text_color=TEXT_BRIGHT,
            width=100,
            height=35,
            command=on_cancel
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))
        
        # Bind Enter key to submit
        password_entry.bind("<Return>", lambda e: on_submit())
        
        # Focus on password entry
        password_entry.focus_set()
        
        dialog.grab_set()
        dialog.wait_window(dialog)

    def _extract_kl4_channels(self, root) -> list[dict]:
        """Extract channel data from KL4's Channels section."""
        channels = []
        for kvcore in root.findall("KvCore"):
            if kvcore.get("APPLICATION") == "KL4":
                programs = kvcore.find("Programs")
                if programs is not None:
                    program = programs.find("Program")
                    if program is not None:
                        channels_elem = program.find("Channels")
                        if channels_elem is not None:
                            for channel in channels_elem.findall("Channel"):
                                full_name = channel.get("Name", "")
                                entity_id = channel.get("EntityId", "")
                                
                                # Extract short name from full name
                                # Format: "BKK Office BMax B4 Mini for Testing SYS1 1 Main"
                                # Extract "Main" or "Safe Entity" (everything after the channel number)
                                short_name = full_name
                                if full_name:
                                    # Split by spaces and find the pattern
                                    parts = full_name.split()
                                    # Look for pattern like "SYS1 1 Main" - extract after the number
                                    for i, part in enumerate(parts):
                                        if part.isdigit() and i + 1 < len(parts):
                                            # Take everything after the number
                                            short_name = " ".join(parts[i + 1:])
                                            break
                                
                                tracking_period = ""
                                mc_app_enabled = False

                                # Get Settings/Misc for TrackingPeriod
                                settings = channel.find("Settings")
                                if settings is not None:
                                    misc = settings.find("Misc")
                                    if misc is None:
                                        misc = settings.find("misc")
                                    if misc is not None:
                                        tracking_period = misc.get("TrackingPeriod", "")

                                    # Get ManagementApp Enabled status
                                    mgmt_app = settings.find("ManagementApp")
                                    if mgmt_app is not None:
                                        enabled_attr = mgmt_app.get("Enabled", "NO")
                                        mc_app_enabled = enabled_attr.upper() == "YES"

                                if short_name:
                                    channels.append({
                                        "name": short_name,
                                        "full_name": full_name,
                                        "entity_id": entity_id,
                                        "tracking_period": tracking_period,
                                        "mc_app_enabled": mc_app_enabled
                                    })
        return channels

    # ── Build readable view with split layout ────────────────────────────────
    def _build_readable_view(self, xml_path: str, raw_content: str):
        """Build the readable view with channels on left and details panel on right."""
        self._clear_readable_frame()

        try:
            tree = ET.parse(xml_path)
            self._xml_root = tree.getroot()
        except Exception as e:
            self._show_error_in_readable(f"[Error parsing XML: {e}]")
            return

        # ── MC Service App URL ────────────────────────────────────────────────
        mc_url = self._extract_mcservice_url(self._xml_root)
        url_frame = ctk.CTkFrame(self._readable_frame, fg_color=CARD_BG, corner_radius=CORNER)
        url_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        url_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            url_frame, text="MC Service App URL",
            font=ctk.CTkFont(size=10), text_color=TEXT_DIM, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 2))

        url_text = mc_url if mc_url else "Not configured"
        ctk.CTkLabel(
            url_frame, text=url_text,
            font=ctk.CTkFont(size=14, weight="bold"), text_color=ACCENT, anchor="w"
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(2, 10))

        # ── Channels Section ────────────────────────────────────────────────────
        channels = self._extract_kl4_channels(self._xml_root)
        channel_count = len(channels)

        count_frame = ctk.CTkFrame(self._readable_frame, fg_color="transparent")
        count_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        count_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            count_frame,
            text=f"No. of channels: {channel_count}",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_BRIGHT, anchor="w"
        ).grid(row=0, column=0, sticky="w")

        if channel_count == 0:
            ctk.CTkLabel(
                self._readable_frame, text="No channels found in KL4 configuration.",
                font=ctk.CTkFont(size=12), text_color=TEXT_DIM
            ).grid(row=2, column=0, sticky="w", pady=(10, 0))
            return

        # ── Main Content Area: Channels (left) + Details Panel (right) ──────────
        # Use grid with weight to force both panels to fill full height
        content_frame = ctk.CTkFrame(self._readable_frame, fg_color="transparent")
        content_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 20))
        content_frame.columnconfigure(0, weight=20, minsize=250)  # Left panel: 20%
        content_frame.columnconfigure(1, weight=0, minsize=4)   # Sash column
        content_frame.columnconfigure(2, weight=80, minsize=700)  # Right panel: 80%
        content_frame.rowconfigure(0, weight=1)     # Both fill full height
        self._readable_frame.rowconfigure(2, weight=1)
        self._readable_frame.columnconfigure(0, weight=1)

        # Left side: Channel boxes with header
        left_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_container.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_container.columnconfigure(0, weight=1)
        left_container.rowconfigure(1, weight=1)

        # Channel List header
        left_header = ctk.CTkFrame(left_container, fg_color=CARD_BG, corner_radius=CORNER)
        left_header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        left_header.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_header, text="Channel List",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=ACCENT, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=12, pady=8)

        left_frame = ctk.CTkScrollableFrame(
            left_container, fg_color="transparent",
            scrollbar_button_color=DIVIDER,
            scrollbar_button_hover_color=ACCENT,
            width=420
        )
        left_frame.grid(row=1, column=0, sticky="nsew")
        left_frame.columnconfigure(0, weight=1)
        # Configure scrollable frame to expand
        left_frame._parent_canvas.configure(height=0)
        left_frame.grid_rowconfigure(0, weight=1)

        # Store reference for dynamic resizing
        self._left_scrollable = left_frame

        # Store channel data and button references for toggle logic
        self._channel_buttons = {}
        self._current_channel = None
        self._current_menu = None

        for idx, channel in enumerate(channels, start=1):
            channel_box = self._create_channel_box(left_frame, idx, channel)
            channel_box.grid(row=idx - 1, column=0, sticky="ew", pady=8)

        # Draggable sash between panels
        sash = ctk.CTkFrame(content_frame, fg_color=DIVIDER, width=4, cursor="sb_h_double_arrow")
        sash.grid(row=0, column=1, sticky="ns")
        sash.bind("<Button-1>", lambda e: self._start_sash_drag(e, content_frame))
        sash.bind("<B1-Motion>", lambda e: self._on_sash_drag(e, content_frame, left_container, right_container))
        sash.bind("<ButtonRelease-1>", lambda e: self._end_sash_drag())
        self._sash = sash
        self._sash_dragging = False

        # Right side: Details panel with Viewer header
        right_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_container.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        right_container.columnconfigure(0, weight=1)
        right_container.rowconfigure(1, weight=1)

        # Viewer header
        right_header = ctk.CTkFrame(right_container, fg_color=CARD_BG, corner_radius=CORNER)
        right_header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        right_header.columnconfigure(0, weight=1)

        self._viewer_title = ctk.CTkLabel(
            right_header, text="Viewer",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=ACCENT, anchor="w"
        )
        self._viewer_title.grid(row=0, column=0, sticky="w", padx=12, pady=8)

        self._details_scroll_frame = ctk.CTkScrollableFrame(
            right_container, fg_color=CARD_BG, corner_radius=CORNER,
            scrollbar_button_color=DIVIDER,
            scrollbar_button_hover_color=ACCENT,
        )
        self._details_scroll_frame.grid(row=1, column=0, sticky="nsew")
        self._details_scroll_frame.columnconfigure(0, weight=1)

        # Store reference for dynamic resizing
        self._right_scrollable = self._details_scroll_frame

        # Set initial large height for scrollable frames
        left_frame._parent_canvas.configure(height=800)
        self._details_scroll_frame._parent_canvas.configure(height=800)

        # Details panel header
        self._details_header = ctk.CTkLabel(
            self._details_scroll_frame, text="Select a channel and menu",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_BRIGHT, anchor="w"
        )
        self._details_header.grid(row=0, column=0, sticky="w", padx=14, pady=14)

        # Details content area
        self._details_content = ctk.CTkFrame(self._details_scroll_frame, fg_color="transparent")
        self._details_content.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self._details_content.columnconfigure(0, weight=1)
        self._details_content.rowconfigure(0, weight=1)

    def _create_channel_box(self, parent, idx: int, channel: dict) -> ctk.CTkFrame:
        """Create a channel box with menu buttons."""
        channel_box = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=CORNER)
        channel_box.columnconfigure(1, weight=1)

        # Sequence number badge
        seq_frame = ctk.CTkFrame(channel_box, fg_color=ACCENT, corner_radius=6, width=36, height=36)
        seq_frame.grid(row=0, column=0, rowspan=2, padx=(14, 10), pady=14)
        seq_frame.grid_propagate(False)

        ctk.CTkLabel(
            seq_frame, text=str(idx),
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#1A0F0A", anchor="center"
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Channel name with Entity ID: "Main [30211]"
        name_text = f"{channel['name']} [{channel['entity_id']}]"

        ctk.CTkLabel(
            channel_box, text=name_text,
            font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT_BRIGHT, anchor="w"
        ).grid(row=0, column=1, sticky="w", padx=(0, 14), pady=(14, 4))

        # Info row: Tracking Period and MC App status
        info_frame = ctk.CTkFrame(channel_box, fg_color="transparent")
        info_frame.grid(row=1, column=1, sticky="w", padx=(0, 14), pady=(2, 4))

        tracking_text = f"Tracking Period: {channel['tracking_period'] if channel['tracking_period'] else 'N/A'}"
        ctk.CTkLabel(
            info_frame, text=tracking_text,
            font=ctk.CTkFont(size=11), text_color=TEXT_DIM, anchor="w"
        ).pack(side="left", padx=(0, 12))

        mc_status = "Enabled" if channel['mc_app_enabled'] else "Disabled"
        mc_color = TEXT_GREEN if channel['mc_app_enabled'] else TEXT_RED
        mc_text = f"MC App: {mc_status}"
        ctk.CTkLabel(
            info_frame, text=mc_text,
            font=ctk.CTkFont(size=11), text_color=mc_color, anchor="w"
        ).pack(side="left")

        # Menu buttons row
        btn_frame = ctk.CTkFrame(channel_box, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=(8, 14))

        menu_buttons = {}
        channel_id = f"channel_{idx}"
        # Store channel number for file path lookups
        channel['channel_number'] = idx

        for menu_name in ["Music Schedules", "Overriding Schedules", "Logs"]:
            # Capture channel_number directly in lambda to avoid closure issues
            ch_num = idx
            btn = ctk.CTkButton(
                btn_frame, text=menu_name,
                fg_color="#2A1E1A", hover_color="#3D2B22",
                text_color=TEXT_BRIGHT, font=ctk.CTkFont(size=11),
                corner_radius=6, height=28, width=110,
                command=lambda cid=channel_id, ch=channel, m=menu_name, num=ch_num: self._on_menu_click(cid, ch, m, num)
            )
            btn.pack(side="left", padx=(0, 6))
            menu_buttons[menu_name] = btn

        self._channel_buttons[channel_id] = {
            "channel": channel,
            "buttons": menu_buttons,
            "box": channel_box
        }

        return channel_box

    def _on_menu_click(self, channel_id: str, channel: dict, menu_name: str, channel_num: int = 0):
        """Handle menu button click - toggle display in details panel."""
        # Store channel number directly
        if channel_num > 0:
            channel['channel_number'] = channel_num
        
        # If clicking same channel and same menu, do nothing
        if self._current_channel == channel_id and self._current_menu == menu_name:
            return

        # Reset ALL buttons to default state (defensive - ensure clean slate)
        for ch_id, ch_data in self._channel_buttons.items():
            for btn in ch_data["buttons"].values():
                btn.configure(fg_color="#2A1E1A", text_color=TEXT_BRIGHT)

        # Set new active button styling
        new_buttons = self._channel_buttons[channel_id]["buttons"]
        new_buttons[menu_name].configure(fg_color=ACCENT, text_color="#1A0F0A")

        # Update state
        self._current_channel = channel_id
        self._current_menu = menu_name

        # Update details panel
        self._update_details_panel(channel, menu_name)

    def _update_details_panel(self, channel: dict, menu_name: str):
        """Update the details panel with content based on channel and menu."""
        # Clear existing content
        for widget in self._details_content.winfo_children():
            widget.destroy()

        # Update header
        self._details_header.configure(
            text=f"{channel['name']} — {menu_name}"
        )

        # Update Viewer panel header
        self._viewer_title.configure(
            text=f"{channel['name']} — {menu_name}"
        )

        # Reset scroll position to top
        self._details_scroll_frame._parent_canvas.yview_moveto(0)

        # Create content based on menu type
        if menu_name == "Music Schedules":
            self._show_music_schedules(channel)
        elif menu_name == "Overriding Schedules":
            self._show_overriding_schedules(channel)
        elif menu_name == "Logs":
            self._show_logs(channel)

    def _show_music_schedules(self, channel: dict):
        """Display Music Schedules content with files from Channel[N]\\Profiles folder."""
        # Get channel number (sequential index) - NOT entity_id
        channel_num = channel.get('channel_number', 0)
        if not channel_num:
            ctk.CTkLabel(
                self._details_content, text="No channel number available.",
                font=ctk.CTkFont(size=12), text_color=TEXT_DIM, anchor="w"
            ).grid(row=0, column=0, sticky="w", pady=(0, 10))
            return

        # Build base folder path: C:\Kaleidovision\music\Channel[N]
        base_folder = f"C:\\Kaleidovision\\music\\Channel{channel_num}"

        # Check if base folder exists
        if not os.path.exists(base_folder):
            ctk.CTkLabel(
                self._details_content,
                text=f"Music folder not found:\n{base_folder}",
                font=ctk.CTkFont(size=12), text_color=TEXT_DIM, anchor="w"
            ).grid(row=0, column=0, sticky="w", pady=(0, 10))
            return

        # Find the most recent subfolder (format: YYYY-MM-DD-HHMM)
        most_recent_folder = self._find_most_recent_folder(base_folder)
        if not most_recent_folder:
            ctk.CTkLabel(
                self._details_content,
                text=f"No valid date folders found in:\n{base_folder}",
                font=ctk.CTkFont(size=12), text_color=TEXT_DIM, anchor="w"
            ).grid(row=0, column=0, sticky="w", pady=(0, 10))
            return

        # Build full path to Profiles folder within the most recent date folder
        profiles_folder = os.path.join(most_recent_folder, "Profiles")

        if not os.path.exists(profiles_folder):
            ctk.CTkLabel(
                self._details_content,
                text=f"Profiles folder not found:\n{profiles_folder}",
                font=ctk.CTkFont(size=12), text_color=TEXT_DIM, anchor="w"
            ).grid(row=0, column=0, sticky="w", pady=(0, 10))
            return

        # Scan for .olp and .djv files in Profiles folder and its subfolders
        music_files_by_folder = self._scan_music_files(profiles_folder)
        
        # Separate files into two groups
        overlay_files = []
        normal_files = []
        
        for folder_name, file_list in music_files_by_folder.items():
            for file_info in file_list:
                if file_info['name'].lower().endswith('.olp'):
                    overlay_files.append(file_info)
                elif file_info['name'].lower().endswith('.djv'):
                    normal_files.append(file_info)
        
        # Sort each group by name
        overlay_files.sort(key=lambda x: x['name'].lower())
        normal_files.sort(key=lambda x: x['name'].lower())

        # Display folder info header
        folder_frame = ctk.CTkFrame(self._details_content, fg_color=CARD_BG, corner_radius=CORNER)
        folder_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        folder_frame.columnconfigure(0, weight=1)

        # Extract folder name for display (show hierarchy: Channel1 → 2026-02-09-1002 → Profiles)
        folder_name = os.path.basename(most_recent_folder)
        ctk.CTkLabel(
            folder_frame,
            text=f"📁 Channel{channel_num} → {folder_name} → Profiles",
            font=ctk.CTkFont(size=11), text_color=ACCENT, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=12, pady=8)

        if not overlay_files and not normal_files:
            ctk.CTkLabel(
                folder_frame,
                text="No .olp or .djv files found",
                font=ctk.CTkFont(size=10), text_color=TEXT_DIM, anchor="w"
            ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))
            return

        # Calculate total file count
        total_files = len(overlay_files) + len(normal_files)
        ctk.CTkLabel(
            folder_frame,
            text=f"{total_files} files found ({len(overlay_files)} overlays, {len(normal_files)} profiles)",
            font=ctk.CTkFont(size=10), text_color=TEXT_DIM, anchor="w"
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))

        # Display all files in a single clean table
        files_frame = ctk.CTkFrame(self._details_content, fg_color="transparent")
        files_frame.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        files_frame.columnconfigure(0, weight=1)

        # Display Normal Profiles section first
        next_row = 0
        if normal_files:
            # Normal Profiles header
            normal_header = ctk.CTkFrame(files_frame, fg_color=CARD_BG, corner_radius=CORNER)
            normal_header.grid(row=next_row, column=0, sticky="ew", pady=(0, 8))
            normal_header.columnconfigure(0, weight=1)
            
            ctk.CTkLabel(
                normal_header,
                text="📁 Normal Profiles/Intersubs/On-Demands",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=ACCENT, anchor="w"
            ).grid(row=0, column=0, sticky="w", padx=12, pady=8)
            
            # Normal Profiles table header
            normal_table_header = ctk.CTkFrame(files_frame, fg_color=CARD_BG, corner_radius=CORNER)
            normal_table_header.grid(row=next_row + 1, column=0, sticky="ew", pady=(0, 2))
            normal_table_header.columnconfigure(0, weight=3, minsize=200)  # Name
            normal_table_header.columnconfigure(1, weight=0, minsize=80)  # Size
            normal_table_header.columnconfigure(2, weight=0, minsize=120)  # Modified
            normal_table_header.columnconfigure(3, weight=0, minsize=120)  # Actions
            
            headers = ["File Name", "Size", "Modified", "Actions"]
            for col, text in enumerate(headers):
                anchor = "w" if col < 2 else "center"
                ctk.CTkLabel(
                    normal_table_header,
                    text=text.upper(),
                    font=ctk.CTkFont(size=9, weight="bold"),
                    text_color=TEXT_DIM, anchor=anchor
                ).grid(row=0, column=col, sticky="w" if col == 0 else "ew", padx=(12 if col == 0 else 8, 8), pady=6)
            
            # Normal Profile files
            normal_row = next_row + 2
            for file_info in normal_files:
                file_card = self._create_music_file_card(files_frame, file_info, normal_row - 1)
                file_card.grid(row=normal_row, column=0, sticky="ew", pady=1)
                normal_row += 1
            
            next_row = normal_row
        
        # Display Overlays section second
        if overlay_files:
            # Add spacing if normal profiles were shown
            if normal_files:
                spacing_frame = ctk.CTkFrame(files_frame, fg_color="transparent")
                spacing_frame.grid(row=next_row, column=0, sticky="ew", pady=(0, 4))
                next_row += 1
            
            # Overlays header
            overlay_header = ctk.CTkFrame(files_frame, fg_color=CARD_BG, corner_radius=CORNER)
            overlay_header.grid(row=next_row, column=0, sticky="ew", pady=(0, 8))
            overlay_header.columnconfigure(0, weight=1)
            
            ctk.CTkLabel(
                overlay_header,
                text="🎭 Overlays",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=ACCENT, anchor="w"
            ).grid(row=0, column=0, sticky="w", padx=12, pady=8)
            
            # Overlays table header
            overlay_table_header = ctk.CTkFrame(files_frame, fg_color=CARD_BG, corner_radius=CORNER)
            overlay_table_header.grid(row=next_row + 1, column=0, sticky="ew", pady=(0, 2))
            overlay_table_header.columnconfigure(0, weight=3, minsize=200)  # Name
            overlay_table_header.columnconfigure(1, weight=0, minsize=80)  # Size
            overlay_table_header.columnconfigure(2, weight=0, minsize=120)  # Modified
            overlay_table_header.columnconfigure(3, weight=0, minsize=120)  # Actions
            
            headers = ["File Name", "Size", "Modified", "Actions"]
            for col, text in enumerate(headers):
                anchor = "w" if col < 2 else "center"
                ctk.CTkLabel(
                    overlay_table_header,
                    text=text.upper(),
                    font=ctk.CTkFont(size=9, weight="bold"),
                    text_color=TEXT_DIM, anchor=anchor
                ).grid(row=0, column=col, sticky="w" if col == 0 else "ew", padx=(12 if col == 0 else 8, 8), pady=6)
            
            # Overlay files
            overlay_row = next_row + 2
            for file_info in overlay_files:
                file_card = self._create_music_file_card(files_frame, file_info, overlay_row - 1)
                file_card.grid(row=overlay_row, column=0, sticky="ew", pady=1)
                overlay_row += 1

    def _extract_music_schedule(self, entity_id: str) -> dict | None:
        """Extract music schedule data for a specific channel from the stored XML root."""
        if not hasattr(self, '_xml_root') or self._xml_root is None:
            return None

        root = self._xml_root

        for kvcore in root.findall("KvCore"):
            if kvcore.get("APPLICATION") == "KL4":
                programs = kvcore.find("Programs")
                if programs is not None:
                    program = programs.find("Program")
                    if program is not None:
                        channels_elem = program.find("Channels")
                        if channels_elem is not None:
                            for channel in channels_elem.findall("Channel"):
                                if channel.get("EntityId") == entity_id:
                                    # Found the channel, now find Schedule ENGINE="Music"
                                    for schedule in channel.findall("Schedule"):
                                        if schedule.get("ENGINE") == "Music":
                                            # Found the music schedule, extract Day and Zone data
                                            schedule_data = {
                                                'day_id': None,
                                                'zone_id': None,
                                                'properties': {}
                                            }

                                            # Get Day with ID="0"
                                            day = schedule.find("Day[@ID='0']")
                                            if day is not None:
                                                schedule_data['day_id'] = day.get("ID")

                                                # Get Zone with ID="1"
                                                zone = day.find("Zone[@ID='1']")
                                                if zone is not None:
                                                    schedule_data['zone_id'] = zone.get("ID")

                                                    # Extract all Property tags
                                                    for prop in zone.findall("Property"):
                                                        key = prop.get("KEY")
                                                        value = prop.get("VALUE")
                                                        if key and value is not None:
                                                            schedule_data['properties'][key] = value

                                            return schedule_data
        return None

    def _find_most_recent_folder(self, base_folder: str) -> str | None:
        """Find the most recent folder by parsing date from folder names (format: YYYY-MM-DD-HHMM)."""
        try:
            folders = []
            for entry in os.scandir(base_folder):
                if entry.is_dir():
                    folder_name = entry.name
                    # Parse format: YYYY-MM-DD-HHMM (e.g., 2026-02-09-1002)
                    try:
                        parts = folder_name.split('-')
                        if len(parts) == 4:
                            year = int(parts[0])
                            month = int(parts[1])
                            day = int(parts[2])
                            time_str = parts[3]
                            hour = int(time_str[:2]) if len(time_str) >= 2 else 0
                            minute = int(time_str[2:4]) if len(time_str) >= 4 else 0
                            
                            # Create datetime for comparison
                            dt = datetime(year, month, day, hour, minute)
                            folders.append((dt, entry.path))
                    except (ValueError, IndexError):
                        # Skip folders that don't match the expected format
                        continue
            
            if not folders:
                return None
            
            # Sort by datetime (most recent first) and return the path
            folders.sort(reverse=True)
            return folders[0][1]
        except Exception as e:
            print(f"Error finding most recent folder in {base_folder}: {e}")
            return None

    def _scan_music_files(self, folder_path: str) -> dict[str, list[dict]]:
        """Scan folder and its subfolders for .olp and .djv music profile files.
        
        Returns a dictionary with subfolder names as keys and lists of file info as values.
        """
        files_by_folder = {}
        try:
            # Walk through the folder and all subfolders
            for root, dirs, filenames in os.walk(folder_path):
                # Get relative path from base folder
                rel_path = os.path.relpath(root, folder_path)
                folder_name = "Normal Profiles" if rel_path == "." else os.path.basename(root)
                
                folder_files = []
                for filename in filenames:
                    # Only process .olp and .djv files
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in ['.olp', '.djv']:
                        continue

                    full_path = os.path.join(root, filename)
                    
                    # Get file stats
                    stat = os.stat(full_path)
                    size_bytes = stat.st_size
                    size_kb = size_bytes / 1024
                    modified_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

                    # Determine file type
                    if ext == '.olp':
                        file_type = "OLP Profile"
                    elif ext == '.djv':
                        file_type = "DJV Profile"
                    else:
                        file_type = "Unknown"

                    folder_files.append({
                        'name': filename,
                        'path': full_path,
                        'rel_path': rel_path,
                        'type': file_type,
                        'size': f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB",
                        'modified': modified_time
                    })

                if folder_files:
                    # Sort by name
                    folder_files.sort(key=lambda x: x['name'].lower())
                    files_by_folder[folder_name] = folder_files
                    
        except Exception as e:
            print(f"Error scanning folder {folder_path}: {e}")

        return files_by_folder

    def _parse_music_file_schedule(self, file_path: str) -> dict:
        """Parse .olp or .djv file to extract schedule info (StartTime, EndTime, DayOfWeek, Name, FrequencyRanges)."""
        schedule = {
            'start_time': '',
            'end_time': '',
            'day_of_week': '',
            'name': '',
            'raw_start': '',
            'raw_end': '',
            'indate': '',
            'outdate': '',
            'hidden': 'NO',  # Default to not hidden
            'frequency_ranges': []  # List of dicts with frequency, indate, outdate, starttime, endtime
        }
        
        try:
            if not os.path.exists(file_path):
                return schedule
            
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Find INFO element
            info = root.find('INFO')
            if info is not None:
                start_time = info.get('StartTime', '')
                end_time = info.get('FinishTime', '')
                day_of_week = info.get('DayOfWeek', '')
                name = info.get('NAME', '')
                indate = info.get('INDATE', '')
                outdate = info.get('OUTDATE', '')
                hidden = info.get('HIDDEN', 'NO')
                
                schedule['raw_start'] = start_time
                schedule['raw_end'] = end_time
                schedule['start_time'] = self._format_time(start_time)
                schedule['end_time'] = self._format_time(end_time)
                schedule['day_of_week'] = self._map_day_of_week(day_of_week)
                schedule['name'] = name
                schedule['indate'] = indate
                schedule['outdate'] = outdate
                schedule['hidden'] = hidden
            
            # Find INTER-PROFILE and FREQUENCY-RANGES for overlay files
            inter_profile = root.find('INTER-PROFILE')
            if inter_profile is not None:
                freq_ranges = inter_profile.find('FREQUENCY-RANGES')
                if freq_ranges is not None:
                    for freq_range in freq_ranges.findall('FREQUENCY-RANGE'):
                        schedule['frequency_ranges'].append({
                            'frequency': freq_range.get('FREQUENCY', '0'),
                            'indate': freq_range.get('INDATE', ''),
                            'outdate': freq_range.get('OUTDATE', ''),
                            'starttime': freq_range.get('STARTTIME', ''),
                            'endtime': freq_range.get('ENDTIME', '')
                        })
        except Exception:
            # If parsing fails, return empty schedule
            pass
        
        return schedule
    
    def _format_date_range(self, date_str: str) -> str:
        """Format date from 'YYYY09010000' to '1 September YYYY'."""
        if len(date_str) >= 8 and date_str.startswith('YYYY'):
            # Format: YYYYMMddHHmm or similar
            month_map = {
                '01': 'January', '02': 'February', '03': 'March', '04': 'April',
                '05': 'May', '06': 'June', '07': 'July', '08': 'August',
                '09': 'September', '10': 'October', '11': 'November', '12': 'December'
            }
            month = date_str[4:6]
            day = date_str[6:8].lstrip('0') or '1'  # Remove leading zeros, default to 1
            month_name = month_map.get(month, month)
            return f"{day} {month_name} YYYY"
        return date_str
    
    def _format_in_out_date(self, date_str: str) -> tuple[str, str]:
        """Format INDATE/OUTDATE as 'DD/MM/YYYY (HH:MM)' and return color based on past/future."""
        if not date_str or len(date_str) < 8:
            return date_str, "#808080"
        
        try:
            # Parse the date string (format: YYYYMMDDHHmm)
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            hour = int(date_str[8:10]) if len(date_str) >= 10 else 0
            minute = int(date_str[10:12]) if len(date_str) >= 12 else 0
            
            # Use 'datetime' directly (imported as: from datetime import datetime)
            file_date = datetime(year, month, day, hour, minute)
            now = datetime.now()
            
            # Format as DD/MM/YYYY (HH:MM)
            formatted = f"{day:02d}/{month:02d}/{year} ({hour:02d}:{minute:02d})"
            
            # Determine color based on past/future
            color = "#E57373" if file_date < now else "#81C784"
            
            return formatted, color
        except Exception:
            return date_str, "#808080"
    
    def _format_time(self, time_str: str) -> str:
        """Format time from '0600' to '06:00'."""
        if len(time_str) == 4 and time_str.isdigit():
            return f"{time_str[:2]}:{time_str[2:]}"
        return time_str
    
    def _map_day_of_week(self, dow: str) -> str:
        """Map DayOfWeek value to display text."""
        mapping = {
            '0': 'Every day',
            '1': 'Sunday',
            '2': 'Monday',
            '3': 'Tuesday',
            '4': 'Wednesday',
            '5': 'Thursday',
            '6': 'Friday',
            '7': 'Saturday'
        }
        return mapping.get(dow, dow)

    def _create_music_file_card(self, parent, file_info: dict, row: int) -> ctk.CTkFrame:
        """Create a file entry row with View and Edit buttons."""
        card = ctk.CTkFrame(parent, fg_color=CARD_BG if row % 2 == 0 else "#2A2A2A", corner_radius=0)
        card.columnconfigure(0, weight=3, minsize=200)  # Name
        card.columnconfigure(1, weight=0, minsize=80)   # Size
        card.columnconfigure(2, weight=0, minsize=120)  # Modified
        card.columnconfigure(3, weight=0, minsize=120)  # Actions

        # Parse schedule info from file
        schedule = self._parse_music_file_schedule(file_info['path'])
        
        # Create name column frame to hold filename and schedule
        name_frame = ctk.CTkFrame(card, fg_color="transparent")
        name_frame.grid(row=0, column=0, sticky="w", padx=(12, 8), pady=(8, 4))
        name_frame.columnconfigure(0, weight=1)

        # File icon based on type
        icon = "🎵" if file_info['type'] == "OLP Profile" else "🎶"

        # Name with icon
        ctk.CTkLabel(
            name_frame,
            text=f"{icon} {file_info['name']}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_BRIGHT, anchor="w"
        ).grid(row=0, column=0, sticky="w")
        
        # Track current row for dynamic placement
        current_row = 1

        # Schedule info below filename with color coding
        if schedule['start_time'] and schedule['end_time'] and schedule['day_of_week']:
            # Determine colors based on file type and time values
            is_midnight = (schedule['raw_start'] in ['0000', '00:00'] and 
                          schedule['raw_end'] in ['0000', '00:00'])
            is_olp = file_info['type'] == "OLP Profile"
            
            if is_midnight:
                # Grey for midnight schedules
                text_color = "#808080"
                bg_color = "#2A2A2A"
            elif is_olp:
                # Green for .olp files
                text_color = "#4CAF50"
                bg_color = "#1A3A1A"
            else:
                # Blue for .djv files
                text_color = "#2196F3"
                bg_color = "#1A2A3A"
            
            # Schedule time line
            schedule_text = f"⏰ {schedule['start_time']} - {schedule['end_time']} ({schedule['day_of_week']})"
            
            schedule_label = ctk.CTkLabel(
                name_frame,
                text=schedule_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=text_color,
                fg_color=bg_color,
                corner_radius=4,
                padx=8,
                pady=2,
                anchor="w"
            )
            schedule_label.grid(row=current_row, column=0, sticky="w", pady=(2, 2))
            current_row += 1
            
            # Profile name on its own line
            name_display = schedule['name'] if schedule['name'] else "Unknown"
            ctk.CTkLabel(
                name_frame,
                text=f"🎶 {name_display}",
                font=ctk.CTkFont(size=11),
                text_color=text_color,
                anchor="w"
            ).grid(row=current_row, column=0, sticky="w", pady=(0, 4))
            current_row += 1
        
        # In-Out Dates line for all files
        if schedule.get('indate') and schedule.get('outdate'):
            # Format dates with color coding
            in_formatted, in_color = self._format_in_out_date(schedule['indate'])
            out_formatted, out_color = self._format_in_out_date(schedule['outdate'])
            
            # Create separate labels for colored dates
            in_out_frame = ctk.CTkFrame(name_frame, fg_color="transparent")
            in_out_frame.grid(row=current_row, column=0, sticky="w", pady=(2, 4))
            current_row += 1
            
            # Prefix
            ctk.CTkLabel(
                in_out_frame,
                text="In-Out Dates: ",
                font=ctk.CTkFont(size=9),
                text_color=TEXT_DIM,
                anchor="w"
            ).pack(side="left")
            
            # INDATE with color
            ctk.CTkLabel(
                in_out_frame,
                text=in_formatted,
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=in_color,
                anchor="w"
            ).pack(side="left", padx=(0, 8))
            
            # Separator
            ctk.CTkLabel(
                in_out_frame,
                text=" - ",
                font=ctk.CTkFont(size=9),
                text_color=TEXT_DIM,
                anchor="w"
            ).pack(side="left")
            
            # OUTDATE with color
            ctk.CTkLabel(
                in_out_frame,
                text=out_formatted,
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=out_color,
                anchor="w"
            ).pack(side="left")
        
        # For overlay files, display frequency ranges from INTER-PROFILE
        if file_info['type'] == "OLP Profile" and schedule['frequency_ranges']:
            freq_container = ctk.CTkFrame(name_frame, fg_color="transparent")
            freq_container.grid(row=current_row, column=0, sticky="w", pady=(4, 4))
            freq_container.columnconfigure(0, weight=1)
            current_row += 1
            
            for idx, freq_range in enumerate(schedule['frequency_ranges']):
                # Calculate "1 in every N tracks" (frequency + 1)
                frequency_val = int(freq_range['frequency']) if freq_range['frequency'].isdigit() else 0
                tracks_text = f"1 in every {frequency_val + 1} tracks"
                
                # Format dates
                in_date = self._format_date_range(freq_range['indate'])
                out_date = self._format_date_range(freq_range['outdate'])
                
                # Format times
                start_time = self._format_time(freq_range['starttime'])
                end_time = self._format_time(freq_range['endtime'])
                
                # Card per frequency range
                range_card = ctk.CTkFrame(freq_container, fg_color="#1E1E2A", corner_radius=6)
                range_card.grid(row=idx, column=0, sticky="w", pady=(0, 6), padx=(4, 0))
                range_card.columnconfigure(0, weight=0)
                range_card.columnconfigure(1, weight=1)
                
                # Left: pink badge
                ctk.CTkLabel(
                    range_card,
                    text=tracks_text,
                    font=ctk.CTkFont(size=9, weight="bold"),
                    text_color="white",
                    fg_color="#E91E63",
                    corner_radius=10,
                    padx=10,
                    pady=3
                ).grid(row=0, column=0, rowspan=3, sticky="ns", padx=(8, 12), pady=8)
                
                # Right: In, Out, Time on separate lines
                ctk.CTkLabel(
                    range_card,
                    text=f"In:    {in_date}",
                    font=ctk.CTkFont(size=9),
                    text_color="#FF6B6B",
                    anchor="w"
                ).grid(row=0, column=1, sticky="w", padx=(0, 12), pady=(6, 0))
                
                ctk.CTkLabel(
                    range_card,
                    text=f"Out:  {out_date}",
                    font=ctk.CTkFont(size=9),
                    text_color="#FF9E9E",
                    anchor="w"
                ).grid(row=1, column=1, sticky="w", padx=(0, 12), pady=0)
                
                ctk.CTkLabel(
                    range_card,
                    text=f"Time: {start_time} - {end_time}",
                    font=ctk.CTkFont(size=9),
                    text_color=TEXT_DIM,
                    anchor="w"
                ).grid(row=2, column=1, sticky="w", padx=(0, 12), pady=(0, 6))
        
        # HIDDEN status indicator - moved to bottom of all file information
        hidden_status = schedule.get('hidden', 'NO')
        if hidden_status == 'YES':
            # Hidden file - warning style with eye-slash icon
            hidden_frame = ctk.CTkFrame(name_frame, fg_color="transparent")
            hidden_frame.grid(row=current_row, column=0, sticky="w", pady=(6, 4))
            current_row += 1
            
            # Warning badge for hidden files
            ctk.CTkLabel(
                hidden_frame,
                text="🚫",
                font=ctk.CTkFont(size=12),
                anchor="w"
            ).pack(side="left", padx=(0, 4))
            
            ctk.CTkLabel(
                hidden_frame,
                text="HIDDEN",
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color="white",
                fg_color="#FF5722",  # Deep orange for warning
                corner_radius=6,
                padx=8,
                pady=2
            ).pack(side="left")
            
            ctk.CTkLabel(
                hidden_frame,
                text="(Not visible in player)",
                font=ctk.CTkFont(size=9),
                text_color="#FF9E80",
                anchor="w"
            ).pack(side="left", padx=(6, 0))
        else:
            # Not hidden - subtle visible indicator
            hidden_frame = ctk.CTkFrame(name_frame, fg_color="transparent")
            hidden_frame.grid(row=current_row, column=0, sticky="w", pady=(4, 4))
            current_row += 1
            
            ctk.CTkLabel(
                hidden_frame,
                text="👁️",
                font=ctk.CTkFont(size=11),
                anchor="w"
            ).pack(side="left", padx=(0, 4))
            
            ctk.CTkLabel(
                hidden_frame,
                text="VISIBLE",
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color="#4CAF50",  # Green for visible
                anchor="w"
            ).pack(side="left")

        # Size
        ctk.CTkLabel(
            card,
            text=file_info['size'],
            font=ctk.CTkFont(size=10),
            text_color=TEXT_DIM, anchor="center"
        ).grid(row=0, column=1, sticky="ew", padx=8, pady=8)

        # Modified date
        ctk.CTkLabel(
            card,
            text=file_info['modified'],
            font=ctk.CTkFont(size=10),
            text_color=TEXT_DIM, anchor="center"
        ).grid(row=0, column=2, sticky="ew", padx=8, pady=8)

        # Action buttons frame
        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.grid(row=0, column=3, sticky="e", padx=(8, 12), pady=8)

        # View button
        view_btn = ctk.CTkButton(
            actions_frame,
            text="View",
            width=50,
            height=28,
            corner_radius=4,
            fg_color=DIVIDER,
            hover_color=ACCENT,
            text_color=TEXT_BRIGHT,
            font=ctk.CTkFont(size=10),
            command=lambda path=file_info['path']: self._view_file_popup(path)
        )
        view_btn.pack(side="left", padx=(0, 4))

        # Edit button
        edit_btn = ctk.CTkButton(
            actions_frame,
            text="Edit",
            width=50,
            height=28,
            corner_radius=4,
            fg_color=DIVIDER,
            hover_color=ACCENT,
            text_color=TEXT_BRIGHT,
            font=ctk.CTkFont(size=10),
            command=lambda path=file_info['path']: self._edit_file_with_notepad(path)
        )
        edit_btn.pack(side="left")

        return card

    def _view_file_popup(self, file_path: str):
        """Open a popup window showing file contents in a read-only textarea."""
        popup = ctk.CTkToplevel(self)
        popup.title(f"View: {os.path.basename(file_path)}")
        popup.geometry("800x600")
        popup.resizable(True, True)
        
        # Center the popup
        popup.update_idletasks()
        sw = popup.winfo_screenwidth()
        sh = popup.winfo_screenheight()
        x = (sw - 800) // 2
        y = (sh - 600) // 2
        popup.geometry(f"800x600+{x}+{y}")
        
        popup.columnconfigure(0, weight=1)
        popup.rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(popup, fg_color=CARD_BG, corner_radius=CORNER)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        header.columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            header,
            text=f"📄 {os.path.basename(file_path)}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ACCENT, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=12, pady=8)
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            content = f"[Error reading file: {e}]"
        
        # Text area (read-only)
        text_frame = ctk.CTkFrame(popup, fg_color=CARD_BG)
        text_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        textbox = ctk.CTkTextbox(
            text_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#1A1A1A",
            text_color=TEXT_BRIGHT,
            border_color=DIVIDER,
            border_width=1,
            corner_radius=CORNER,
            wrap="word"
        )
        textbox.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        textbox.insert("0.0", content)
        textbox.configure(state="disabled")
        
        # Close button
        close_btn = ctk.CTkButton(
            popup,
            text="Close",
            width=100,
            fg_color=DIVIDER,
            hover_color=ACCENT,
            text_color=TEXT_BRIGHT,
            command=popup.destroy
        )
        close_btn.grid(row=2, column=0, pady=(0, 12))
        
        # Make modal
        popup.transient(self)
        popup.grab_set()
        popup.focus_set()
    
    def _edit_file_with_notepad(self, file_path: str):
        """Open the file with Notepad for editing."""
        try:
            import subprocess
            subprocess.Popen(['notepad.exe', file_path], shell=True)
        except Exception as e:
            print(f"Error opening file with Notepad: {e}")
            # Fallback: try with os.startfile
            try:
                os.startfile(file_path, 'open')
            except Exception as e2:
                print(f"Error opening file: {e2}")

    def _show_overriding_schedules(self, channel: dict):
        """Display Overriding Schedules content from xmlfeed.musicoverrideschedule.Channel[N].xml."""
        # Get channel number (sequential index)
        channel_num = channel.get('channel_number', 0)
        if not channel_num:
            ctk.CTkLabel(
                self._details_content, text="No channel number available.",
                font=ctk.CTkFont(size=12), text_color=TEXT_DIM, anchor="w"
            ).grid(row=0, column=0, sticky="w", pady=(0, 10))
            return

        # Store channel and file path for refresh
        self._current_overriding_channel = channel
        self._current_overriding_file_path = f"C:\\Kaleidovision\\local\\xmlFeeds\\xmlfeed.musicoverrideschedule.Channel{channel_num}.xml"

        # Build file path: C:\Kaleidovision\local\xmlFeeds\xmlfeed.musicoverrideschedule.Channel[N].xml
        file_path = self._current_overriding_file_path

        # Display file path header with refresh button
        header_frame = ctk.CTkFrame(self._details_content, fg_color=CARD_BG, corner_radius=CORNER)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=0)

        ctk.CTkLabel(
            header_frame,
            text=f"📄 {file_path}",
            font=ctk.CTkFont(size=11), text_color=ACCENT, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=12, pady=8)

        # Refresh button
        refresh_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Refresh",
            width=80,
            height=28,
            corner_radius=4,
            fg_color=DIVIDER,
            hover_color=ACCENT,
            text_color=TEXT_BRIGHT,
            font=ctk.CTkFont(size=10),
            command=lambda: self._refresh_overriding_schedules()
        )
        refresh_btn.grid(row=0, column=1, sticky="e", padx=(8, 12), pady=8)

        # Check if file exists
        if not os.path.exists(file_path):
            ctk.CTkLabel(
                header_frame,
                text="File not found",
                font=ctk.CTkFont(size=10), text_color=TEXT_DIM, anchor="w"
            ).grid(row=1, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 8))
            return

        # Read and display file content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            content = f"[Error reading file: {e}]"

        # Content textbox - fill available vertical space
        text_frame = ctk.CTkFrame(self._details_content, fg_color=CARD_BG, corner_radius=CORNER)
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        # Make details_content expand to fill available space
        self._details_content.rowconfigure(1, weight=1)

        content_box = ctk.CTkTextbox(
            text_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#1A1A1A",
            text_color=TEXT_BRIGHT,
            border_color=DIVIDER,
            border_width=1,
            corner_radius=CORNER,
            wrap="word"
        )
        content_box.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        content_box.insert("0.0", content)
        content_box.configure(state="disabled")
        
        # Store reference to content box for refresh
        self._overriding_content_box = content_box

    def _refresh_overriding_schedules(self):
        """Refresh the Overriding Schedules view with latest file content."""
        if hasattr(self, '_current_overriding_file_path') and self._current_overriding_file_path:
            try:
                with open(self._current_overriding_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Update the content box if it exists
                if hasattr(self, '_overriding_content_box') and self._overriding_content_box:
                    self._overriding_content_box.configure(state="normal")
                    self._overriding_content_box.delete("0.0", "end")
                    self._overriding_content_box.insert("0.0", content)
                    self._overriding_content_box.configure(state="disabled")
            except Exception as e:
                print(f"Error refreshing file: {e}")

    def _show_logs(self, channel: dict):
        """Display Logs content with 2-column file list sorted by date (newest first)."""
        import subprocess
        import re

        # Get channel number and name
        channel_num = channel.get('channel_number', 0)
        channel_name = channel.get('name', 'Unknown')

        # Check if log folder exists
        log_folder = r"C:\Kaleidovision\logfiles"
        if not os.path.exists(log_folder):
            ctk.CTkLabel(
                self._details_content,
                text=f"'{log_folder}' doesn't exist.",
                font=ctk.CTkFont(size=12), text_color=TEXT_DIM, anchor="w"
            ).grid(row=1, column=0, sticky="w", pady=(10, 0))
            return

        # Open folder button
        def open_log_folder():
            try:
                subprocess.Popen(['explorer', log_folder])
            except Exception as e:
                print(f"Error opening folder: {e}")

        folder_btn_frame = ctk.CTkFrame(self._details_content, fg_color="transparent")
        folder_btn_frame.grid(row=1, column=0, sticky="w", pady=(0, 15))

        ctk.CTkButton(
            folder_btn_frame,
            text="📁 Open Log Folder",
            font=ctk.CTkFont(size=11),
            fg_color=DIVIDER,
            hover_color=ACCENT,
            text_color=TEXT_BRIGHT,
            width=150,
            height=32,
            command=open_log_folder
        ).grid(row=0, column=0, sticky="w")

        # Check for McServiceAppLog.log and add button if exists
        mcservice_log_path = os.path.join(log_folder, "McServiceAppLog.log")
        if os.path.exists(mcservice_log_path):
            ctk.CTkButton(
                folder_btn_frame,
                text="📄 View McServiceAppLog",
                font=ctk.CTkFont(size=11),
                fg_color=DIVIDER,
                hover_color=ACCENT,
                text_color=TEXT_BRIGHT,
                width=180,
                height=32,
                command=lambda: view_log_in_popup(mcservice_log_path, "McServiceAppLog.log", "service", "")
            ).grid(row=0, column=1, sticky="w", padx=(10, 0))

        # Scan for log files - now storing full_path as well
        kl4_pattern = re.compile(rf"^KL4MusicScheduler\.Channel{channel_num}\.(\d{{8}})\.log$")
        track_pattern = re.compile(rf"^DJVPlaybackDebug\.Channel{channel_num}\.(\d{{8}})\.log$")

        kl4_files = []  # (filename, date_str, full_path)
        track_files = []  # (filename, date_str, full_path)

        try:
            for filename in os.listdir(log_folder):
                full_path = os.path.join(log_folder, filename)
                kl4_match = kl4_pattern.match(filename)
                if kl4_match:
                    kl4_files.append((filename, kl4_match.group(1), full_path))
                    continue
                track_match = track_pattern.match(filename)
                if track_match:
                    track_files.append((filename, track_match.group(1), full_path))
        except Exception as e:
            print(f"Error scanning log folder: {e}")

        # Sort state - default to descending (newest first)
        if not hasattr(self, '_logs_sort_state'):
            self._logs_sort_state = {'asc': False}

        # Create 3-column layout: KL4 | Date | Track
        columns_frame = ctk.CTkFrame(self._details_content, fg_color="transparent")
        columns_frame.grid(row=2, column=0, sticky="nsew")
        columns_frame.columnconfigure(0, weight=3)
        columns_frame.columnconfigure(1, weight=2)  # Date center
        columns_frame.columnconfigure(2, weight=3)
        columns_frame.rowconfigure(1, weight=1)

        # Sort toggle (shared - sorts all three columns together by date)
        def sort_toggle():
            self._logs_sort_state['asc'] = not self._logs_sort_state['asc']
            refresh_file_lists()

        # KL4 Logs Column Header
        kl4_header = ctk.CTkFrame(columns_frame, fg_color=CARD_BG, corner_radius=CORNER)
        kl4_header.grid(row=0, column=0, sticky="ew", padx=(0, 3), pady=(0, 4))
        kl4_header.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            kl4_header, text="KL4 Logs",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=ACCENT, anchor="center"
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=8)

        # Date center column header with sort button
        date_header = ctk.CTkFrame(columns_frame, fg_color=CARD_BG, corner_radius=CORNER)
        date_header.grid(row=0, column=1, sticky="ew", padx=3, pady=(0, 4))
        date_header.columnconfigure(0, weight=1)
        sort_btn = ctk.CTkButton(
            date_header,
            text="📅 Date 🔼" if self._logs_sort_state['asc'] else "📅 Date 🔽",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent",
            hover_color=DIVIDER,
            text_color=ACCENT,
            anchor="center",
            command=sort_toggle
        )
        sort_btn.grid(row=0, column=0, sticky="ew", padx=10, pady=8)

        # Track logs Column Header
        track_header = ctk.CTkFrame(columns_frame, fg_color=CARD_BG, corner_radius=CORNER)
        track_header.grid(row=0, column=2, sticky="ew", padx=(3, 0), pady=(0, 4))
        track_header.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            track_header, text="Track Logs",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=ACCENT, anchor="center"
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=8)

        # File list containers (plain CTkFrame - no independent scrollbars)
        kl4_container = ctk.CTkFrame(columns_frame, fg_color="transparent")
        kl4_container.grid(row=1, column=0, sticky="nsew", padx=(0, 3))
        kl4_container.columnconfigure(0, weight=1)

        date_container = ctk.CTkFrame(columns_frame, fg_color="transparent")
        date_container.grid(row=1, column=1, sticky="nsew", padx=3)
        date_container.columnconfigure(0, weight=1)

        track_container = ctk.CTkFrame(columns_frame, fg_color="transparent")
        track_container.grid(row=1, column=2, sticky="nsew", padx=(3, 0))
        track_container.columnconfigure(0, weight=1)

        def open_with_notepad(file_path: str):
            """Open the log file with Notepad."""
            try:
                subprocess.Popen(['notepad.exe', file_path], shell=True)
            except Exception as e:
                print(f"Error opening file with Notepad: {e}")

        def view_log_in_popup(file_path: str, file_name: str, log_type: str, date_str: str):
            """Open log file in a popup window with search functionality."""
            # Format date for title: YYYYMMDD -> DD/MM/YYYY
            year = date_str[:4]
            month = date_str[4:6]
            day = date_str[6:]
            display_date = f"{day}/{month}/{year}"
            
            # Determine title based on log type
            if log_type == "kl4":
                title = f"[CH{channel_num}] KL4 logs - {display_date} ({channel_name})"
            elif log_type == "track":
                title = f"[CH{channel_num}] Track logs - {display_date} ({channel_name})"
            else:
                title = f"McServiceAppLog ({channel_name})"
            
            # Create popup window (independent - not modal)
            popup = ctk.CTkToplevel(self)
            popup.title(title)
            popup.geometry("900x700")
            popup.resizable(True, True)
            popup.configure(fg_color="#1A0F0A")
            
            # Center the popup
            popup.update_idletasks()
            sw = popup.winfo_screenwidth()
            sh = popup.winfo_screenheight()
            x = (sw - 900) // 2
            y = (sh - 700) // 2
            popup.geometry(f"900x700+{x}+{y}")
            
            popup.columnconfigure(0, weight=1)
            popup.rowconfigure(2, weight=1)
            
            # Header with file info
            header_frame = ctk.CTkFrame(popup, fg_color=CARD_BG, corner_radius=CORNER)
            header_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
            header_frame.columnconfigure(0, weight=1)
            
            ctk.CTkLabel(
                header_frame,
                text=f"📄 {file_name}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=ACCENT, anchor="w"
            ).grid(row=0, column=0, sticky="w", padx=12, pady=8)
            
            # Search frame
            search_frame = ctk.CTkFrame(popup, fg_color="transparent")
            search_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
            search_frame.columnconfigure(0, weight=0)  # A- button
            search_frame.columnconfigure(1, weight=0)  # A+ button
            search_frame.columnconfigure(2, weight=1)  # Search field
            search_frame.columnconfigure(3, weight=0)  # Search button
            
            # Text size controls
            def increase_text_size():
                """Increase font size for both textboxes"""
                current_font = textbox.cget("font")
                current_size = current_font.cget("size")
                new_size = min(current_size + 1, 20)  # Max size 20
                
                new_font = ctk.CTkFont(family="Consolas", size=new_size)
                textbox.configure(font=new_font)
                line_numbers.configure(font=new_font)
                popup._current_font_size = new_size
            
            def decrease_text_size():
                """Decrease font size for both textboxes"""
                current_font = textbox.cget("font")
                current_size = current_font.cget("size")
                new_size = max(current_size - 1, 6)  # Min size 6
                
                new_font = ctk.CTkFont(family="Consolas", size=new_size)
                textbox.configure(font=new_font)
                line_numbers.configure(font=new_font)
                popup._current_font_size = new_size
            
            # Decrease text size button
            decrease_btn = ctk.CTkButton(
                search_frame,
                text="A-",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=DIVIDER,
                hover_color=ACCENT,
                text_color=TEXT_BRIGHT,
                width=35,
                height=32,
                command=decrease_text_size
            )
            decrease_btn.grid(row=0, column=0, padx=(0, 4))
            
            # Increase text size button
            increase_btn = ctk.CTkButton(
                search_frame,
                text="A+",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=DIVIDER,
                hover_color=ACCENT,
                text_color=TEXT_BRIGHT,
                width=35,
                height=32,
                command=increase_text_size
            )
            increase_btn.grid(row=0, column=1, padx=(0, 8))
            
            search_entry = ctk.CTkEntry(
                search_frame,
                placeholder_text="Search in log...",
                font=ctk.CTkFont(size=12),
                fg_color="#150D0D",
                text_color=TEXT_BRIGHT,
                border_color=DIVIDER,
                border_width=1,
                height=32
            )
            search_entry.grid(row=0, column=2, sticky="ew", padx=(0, 8))
            
            # Content textbox with line numbers
            content_frame = ctk.CTkFrame(popup, fg_color=CARD_BG, corner_radius=CORNER)
            content_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
            content_frame.columnconfigure(0, weight=0)  # Line numbers
            content_frame.columnconfigure(1, weight=1)  # Content
            content_frame.rowconfigure(0, weight=1)
            
            # Line numbers textbox (scrollbar hidden)
            line_numbers = ctk.CTkTextbox(
                content_frame,
                font=ctk.CTkFont(family="Consolas", size=10),
                fg_color="#1A1A1A",
                text_color=TEXT_DIM,
                border_color=DIVIDER,
                border_width=1,
                corner_radius=0,
                wrap="none",
                width=50,
                state="disabled",
                scrollbar_button_color="#1A1A1A",
                scrollbar_button_hover_color="#1A1A1A"
            )
            line_numbers.grid(row=0, column=0, sticky="ns", padx=(8, 0), pady=8)
            
            # Content textbox
            textbox = ctk.CTkTextbox(
                content_frame,
                font=ctk.CTkFont(family="Consolas", size=10),
                fg_color="#1A1A1A",
                text_color=TEXT_BRIGHT,
                border_color=DIVIDER,
                border_width=1,
                corner_radius=0,
                wrap="none"
            )
            textbox.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=8)
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    content = ''.join(lines)
                    total_lines = len(lines)
            except Exception as e:
                content = f"[Error reading file: {e}]"
                total_lines = 1
            
            # Insert line numbers
            line_numbers.configure(state="normal")
            line_numbers.delete("1.0", "end")
            line_nums = '\n'.join(str(i) for i in range(1, total_lines + 1))
            line_numbers.insert("1.0", line_nums)
            line_numbers.configure(state="disabled")
            
            # Insert content
            textbox.insert("1.0", content)
            textbox.configure(state="disabled")
            
            # Get inner tk Text widgets for direct binding
            _tb = textbox._textbox
            _ln = line_numbers._textbox
            
            # Sync line numbers on every scroll (mouse wheel AND scrollbar drag)
            def _on_scroll(first, last):
                _ln.yview_moveto(first)
                if textbox._y_scrollbar:
                    textbox._y_scrollbar.set(first, last)
            
            _tb.configure(yscrollcommand=_on_scroll)
            
            # Also intercept the scrollbar's own command so dragging syncs line numbers
            if textbox._y_scrollbar:
                _sb = textbox._y_scrollbar
                def _scrollbar_cmd(*args):
                    _tb.yview(*args)
                    _ln.yview_moveto(_tb.yview()[0])
                _sb.configure(command=_scrollbar_cmd)
            
            # Block ALL interaction on the inner line_numbers Text widget
            def _block(event):
                return "break"
            
            def _block_scroll(event):
                units = int(-event.delta / 120)
                _tb.yview_scroll(units, "units")
                return "break"
            
            _ln.bind("<MouseWheel>", _block_scroll)
            _ln.bind("<Button-4>", lambda e: (_tb.yview_scroll(-3, "units"), "break")[-1])
            _ln.bind("<Button-5>", lambda e: (_tb.yview_scroll(3, "units"), "break")[-1])
            _ln.bind("<Button-1>", _block)
            _ln.bind("<B1-Motion>", _block)
            _ln.bind("<ButtonRelease-1>", _block)
            _ln.bind("<Key>", _block)
            _ln.bind("<KeyPress>", _block)
            _ln.configure(takefocus=0)
            
            # Visible date/time tracking based on first visible line
            import re
            # KL4 format: "dd/mm/yyyy hh:mm:ss.mmm" (e.g., "18/02/2026 23:50:27.769")
            kl4_time_pattern = re.compile(r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\.\d{3})")
            # DVJ format: '"dd/mm/yyyy hh:mm:ss"' (e.g., '"18/02/2026 06:21:07"')
            dvj_time_pattern = re.compile(r'"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})"')
            
            def update_visible_time(*args):
                """Update the visible time label based on first visible line with date/time."""
                try:
                    # Get first visible line index
                    first_visible = _tb.index("@0,0")
                    if first_visible:
                        line_num = int(first_visible.split(".")[0])
                        # Search forward for a line with date/time
                        for offset in range(50):  # Check next 50 lines max
                            check_line = line_num + offset
                            line_start = f"{check_line}.0"
                            line_end = f"{check_line}.end"
                            line_content = _tb.get(line_start, line_end)
                            
                            # Try KL4 pattern first, then DVJ
                            match = None
                            if log_type == "kl4":
                                match = kl4_time_pattern.search(line_content)
                            elif log_type == "track":
                                match = dvj_time_pattern.search(line_content)
                            else:
                                # Try both patterns for service logs
                                match = kl4_time_pattern.search(line_content) or dvj_time_pattern.search(line_content)
                            
                            if match:
                                visible_time_lbl.configure(text=match.group(1))
                                return
                        
                        # No date found in visible area
                        visible_time_lbl.configure(text="")
                except Exception:
                    pass
            
            # Bind to scroll events with dynamic font size effect
            _tb.bind("<MouseWheel>", lambda e: (on_scroll_start(), _tb.yview_scroll(int(-e.delta/120), "units"), update_visible_time(), on_scroll_stop(), "break")[4], add=True)
            _tb.bind("<Button-4>", lambda e: (on_scroll_start(), _tb.yview_scroll(-3, "units"), update_visible_time(), on_scroll_stop(), "break")[4], add=True)
            _tb.bind("<Button-5>", lambda e: (on_scroll_start(), _tb.yview_scroll(3, "units"), update_visible_time(), on_scroll_stop(), "break")[4], add=True)
            
            # Also update on scrollbar drag (hook into existing scrollbar command) with dynamic font
            if textbox._y_scrollbar:
                orig_cmd = textbox._y_scrollbar.cget("command")
                def _scrollbar_with_time(*args):
                    on_scroll_start()
                    _tb.yview(*args)
                    _ln.yview_moveto(_tb.yview()[0])
                    update_visible_time()
                    on_scroll_stop()
                textbox._y_scrollbar.configure(command=_scrollbar_with_time)
                
                # Bind scrollbar button press/release for font size effect
                textbox._y_scrollbar.bind("<ButtonPress-1>", lambda e: on_scroll_start())
                textbox._y_scrollbar.bind("<ButtonRelease-1>", lambda e: on_scroll_stop())
                textbox._y_scrollbar.bind("<B1-Motion>", lambda e: on_scroll_start())
            
            # Initial update
            popup.after(100, update_visible_time)
            
            # Search state for cycling through matches
            popup._search_matches = []
            popup._current_match_index = -1
            popup._current_query = ""
            
            # Search functionality with cycling
            def search_text():
                query = search_entry.get().strip()
                if not query:
                    return
                
                textbox.configure(state="normal")
                textbox.tag_remove("highlight", "1.0", "end")
                textbox.tag_remove("current_highlight", "1.0", "end")
                
                # If new search or same query, find all matches
                if query != popup._current_query:
                    popup._current_query = query
                    popup._search_matches = []
                    popup._current_match_index = -1
                    
                    start_pos = "1.0"
                    while True:
                        pos = textbox.search(query, start_pos, stopindex="end", nocase=True)
                        if not pos:
                            break
                        end_pos = f"{pos}+{len(query)}c"
                        popup._search_matches.append((pos, end_pos))
                        textbox.tag_add("highlight", pos, end_pos)
                        start_pos = end_pos
                    
                    if popup._search_matches:
                        textbox.tag_config("highlight", background="#5A4A3A", foreground=TEXT_BRIGHT)
                
                # Cycle to next match
                if popup._search_matches:
                    popup._current_match_index = (popup._current_match_index + 1) % len(popup._search_matches)
                    pos, end_pos = popup._search_matches[popup._current_match_index]
                    
                    # Clear previous current highlight and set new one
                    textbox.tag_remove("current_highlight", "1.0", "end")
                    textbox.tag_add("current_highlight", pos, end_pos)
                    textbox.tag_config("current_highlight", background="#C1784A", foreground="#1A0F0A")
                    
                    # Scroll to show the match
                    textbox.see(pos)
                    popup.after(1, update_visible_time)
                
                textbox.configure(state="disabled")
            
            def clear_search():
                textbox.configure(state="normal")
                textbox.tag_remove("highlight", "1.0", "end")
                textbox.tag_remove("current_highlight", "1.0", "end")
                textbox.configure(state="disabled")
                search_entry.delete(0, "end")
                popup._search_matches = []
                popup._current_match_index = -1
                popup._current_query = ""
            
            search_btn = ctk.CTkButton(
                search_frame,
                text="🔍 Search",
                font=ctk.CTkFont(size=11),
                fg_color=DIVIDER,
                hover_color=ACCENT,
                text_color=TEXT_BRIGHT,
                width=80,
                height=32,
                command=search_text
            )
            search_btn.grid(row=0, column=3, sticky="e")
            
            # Bind Enter key to search
            search_entry.bind("<Return>", lambda e: search_text())
            
            # Button frame with visible time at center-bottom
            btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
            btn_frame.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))
            btn_frame.columnconfigure(0, weight=1)  # Left side (clear btn)
            btn_frame.columnconfigure(1, weight=0)  # Center (time)
            btn_frame.columnconfigure(2, weight=1)  # Right side (close btn)
            
            # Clear search button
            clear_btn = ctk.CTkButton(
                btn_frame,
                text="Clear Search",
                font=ctk.CTkFont(size=11),
                fg_color=DIVIDER,
                hover_color=ACCENT,
                text_color=TEXT_BRIGHT,
                width=100,
                height=32,
                command=clear_search
            )
            clear_btn.grid(row=0, column=0, sticky="w")
            
            # Visible date/time display at center (updates on scroll)
            visible_time_lbl = ctk.CTkLabel(
                btn_frame,
                text="",
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color="#E8A87C",  # Distinct warm color
                anchor="center"
            )
            visible_time_lbl.grid(row=0, column=1, sticky="ew", padx=12)
            
            # Close button
            close_btn = ctk.CTkButton(
                btn_frame,
                text="Close",
                font=ctk.CTkFont(size=11),
                fg_color=DIVIDER,
                hover_color=ACCENT,
                text_color=TEXT_BRIGHT,
                width=100,
                height=32,
                command=popup.destroy
            )
            close_btn.grid(row=0, column=2, sticky="e")
            
            # Scrolling state for dynamic font size
            popup._is_scrolling = False
            popup._scroll_timer = None
            
            def set_scrolling_state(is_scrolling):
                """Update font size and color based on scrolling state."""
                popup._is_scrolling = is_scrolling
                if is_scrolling:
                    visible_time_lbl.configure(
                        font=ctk.CTkFont(size=24, weight="bold"),
                        text_color="#FF6B35"  # Bright orange when changing
                    )
                else:
                    visible_time_lbl.configure(
                        font=ctk.CTkFont(size=20, weight="bold"),
                        text_color="#E8A87C"  # Warm color normal
                    )
            
            def on_scroll_start(event=None):
                """Called when user starts scrolling."""
                if not popup._is_scrolling:
                    set_scrolling_state(True)
                # Cancel any pending scroll stop
                if popup._scroll_timer:
                    popup.after_cancel(popup._scroll_timer)
                    popup._scroll_timer = None
            
            def on_scroll_stop(event=None):
                """Called when scrolling stops (delayed)."""
                if popup._scroll_timer:
                    popup.after_cancel(popup._scroll_timer)
                popup._scroll_timer = popup.after(300, lambda: set_scrolling_state(False))
            
            # Focus the popup using Windows API on the inner Tk window handle
            def set_focus():
                try:
                    import ctypes
                    popup_hwnd = ctypes.windll.user32.FindWindowW(None, title)
                    if popup_hwnd:
                        ctypes.windll.user32.ShowWindow(popup_hwnd, 9)  # SW_RESTORE
                        ctypes.windll.user32.SetForegroundWindow(popup_hwnd)
                except Exception:
                    pass
                popup.lift()
                popup.focus_force()
            
            popup.after(200, set_focus)
            
            # Ensure proper cleanup when closing
            def on_closing():
                popup.destroy()
            
            popup.protocol("WM_DELETE_WINDOW", on_closing)

        def refresh_file_lists():
            # Clear all three columns
            for widget in kl4_container.winfo_children():
                widget.destroy()
            for widget in date_container.winfo_children():
                widget.destroy()
            for widget in track_container.winfo_children():
                widget.destroy()

            # Update sort button
            sort_btn.configure(
                text="📅 Date 🔼" if self._logs_sort_state['asc'] else "📅 Date 🔽"
            )

            # Build lookup dicts: date_str -> (filename, full_path)
            kl4_by_date = {ds: (fn, fp) for fn, ds, fp in kl4_files}
            track_by_date = {ds: (fn, fp) for fn, ds, fp in track_files}

            # Collect all unique dates from both lists
            all_dates = sorted(
                set(kl4_by_date.keys()) | set(track_by_date.keys()),
                reverse=not self._logs_sort_state['asc']
            )

            if not all_dates:
                ctk.CTkLabel(
                    date_container, text="No log files found",
                    font=ctk.CTkFont(size=10), text_color=TEXT_DIM, anchor="center"
                ).grid(row=0, column=0, sticky="ew", pady=5)
                return

            ROW_HEIGHT = 52  # approximate px per row for uniform height

            from datetime import datetime
            # Day of week abbreviations
            DOW_ABBR = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

            for idx, date_str in enumerate(all_dates):
                # Parse date and get day of week
                year, month, day = date_str[:4], date_str[4:6], date_str[6:]
                dt = datetime(int(year), int(month), int(day))
                dow = DOW_ABBR[dt.weekday()]  # weekday(): Monday=0, Sunday=6
                display_date = f"({dow}) {day}-{month}-{year}"
                
                # Check if weekend
                is_weekend = dt.weekday() >= 5  # SAT=5, SUN=6
                
                if is_weekend:
                    row_bg = "#2D1F1F"  # Dark reddish background for weekends
                    date_color = "#E8A87C"  # Lighter accent for weekends
                else:
                    row_bg = CARD_BG if idx % 2 == 0 else "#2A2A2A"
                    date_color = ACCENT

                # Configure row height on all three containers to keep alignment
                kl4_container.rowconfigure(idx, minsize=ROW_HEIGHT)
                date_container.rowconfigure(idx, minsize=ROW_HEIGHT)
                track_container.rowconfigure(idx, minsize=ROW_HEIGHT)

                # ── KL4 cell ──────────────────────────────────────────────
                kl4_cell = ctk.CTkFrame(kl4_container, fg_color=row_bg, corner_radius=0, height=ROW_HEIGHT)
                kl4_cell.grid(row=idx, column=0, sticky="nsew", pady=1)
                kl4_cell.grid_propagate(False)
                kl4_cell.columnconfigure(0, weight=1)
                kl4_cell.rowconfigure(0, weight=1)

                if date_str in kl4_by_date:
                    fn, fp = kl4_by_date[date_str]
                    ctk.CTkButton(
                        kl4_cell, text="View KL4Logs",
                        font=ctk.CTkFont(size=10),
                        fg_color=DIVIDER, hover_color=ACCENT,
                        text_color=TEXT_BRIGHT, height=32,
                        command=lambda path=fp, name=fn, ds=date_str: view_log_in_popup(path, name, "kl4", ds)
                    ).grid(row=0, column=0, sticky="ew", padx=12, pady=8)
                else:
                    ctk.CTkLabel(
                        kl4_cell, text="No KL4 log",
                        font=ctk.CTkFont(size=10),
                        text_color="#5A4A3A", anchor="center"
                    ).grid(row=0, column=0, sticky="ew", padx=12, pady=8)

                # ── Date cell (center) ────────────────────────────────────
                date_cell = ctk.CTkFrame(date_container, fg_color=row_bg, corner_radius=0, height=ROW_HEIGHT)
                date_cell.grid(row=idx, column=0, sticky="nsew", pady=1)
                date_cell.grid_propagate(False)
                date_cell.columnconfigure(0, weight=1)
                date_cell.rowconfigure(0, weight=1)
                ctk.CTkLabel(
                    date_cell, text=f"📅 {display_date}",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=date_color, anchor="center"
                ).grid(row=0, column=0, sticky="nsew", padx=6, pady=0)

                # ── Track cell ────────────────────────────────────────────
                track_cell = ctk.CTkFrame(track_container, fg_color=row_bg, corner_radius=0, height=ROW_HEIGHT)
                track_cell.grid(row=idx, column=0, sticky="nsew", pady=1)
                track_cell.grid_propagate(False)
                track_cell.columnconfigure(0, weight=1)
                track_cell.rowconfigure(0, weight=1)

                if date_str in track_by_date:
                    fn, fp = track_by_date[date_str]
                    ctk.CTkButton(
                        track_cell, text="View Track Logs",
                        font=ctk.CTkFont(size=10),
                        fg_color=DIVIDER, hover_color=ACCENT,
                        text_color=TEXT_BRIGHT, height=32,
                        command=lambda path=fp, name=fn, ds=date_str: view_log_in_popup(path, name, "track", ds)
                    ).grid(row=0, column=0, sticky="ew", padx=12, pady=8)
                else:
                    ctk.CTkLabel(
                        track_cell, text="No Track log",
                        font=ctk.CTkFont(size=10),
                        text_color="#5A4A3A", anchor="center"
                    ).grid(row=0, column=0, sticky="ew", padx=12, pady=8)

        # Initial population
        refresh_file_lists()

    def _start_sash_drag(self, event, content_frame):
        """Start dragging the sash to resize panels."""
        self._sash_dragging = True
        self._sash_last_x = event.x_root
        # Store the actual current widths at drag start
        total_width = content_frame.winfo_width()
        left_width = content_frame.grid_bbox(0, 0)[2] if content_frame.grid_bbox(0, 0) else int(total_width * 0.3)
        self._sash_left_width = left_width

    def _on_sash_drag(self, event, content_frame, left_container, right_container):
        """Handle sash drag motion to resize panels."""
        if not self._sash_dragging:
            return
        
        # Calculate movement delta
        delta_x = event.x_root - self._sash_last_x
        self._sash_last_x = event.x_root
        
        # Update left width
        self._sash_left_width += delta_x
        
        # Constrain to reasonable bounds
        total_width = content_frame.winfo_width()
        min_left = 200
        max_left = total_width - 304  # Leave room for sash (4) + right panel min (300)
        new_left_width = max(min_left, min(self._sash_left_width, max_left))
        
        # Update stored width
        self._sash_left_width = new_left_width
        new_right_width = total_width - 4 - new_left_width
        
        # Update weights proportionally (use larger numbers for finer control)
        left_weight = max(1, int(new_left_width / 10))
        right_weight = max(1, int(new_right_width / 10))
        
        content_frame.columnconfigure(0, weight=left_weight)
        content_frame.columnconfigure(2, weight=right_weight)

    def _end_sash_drag(self):
        """End sash dragging."""
        self._sash_dragging = False


# ── Main Dashboard ─────────────────────────────────────────────────────────────
class DashboardApp(ctk.CTk):
    _STATS = [
        ("Open Tickets",    "142",  "▲ 12 since yesterday",  False),
        ("Resolved Today",  "87",   "▲ 5 from avg",          True),
        ("Active Agents",   "14",   "▼ 2 on break",          False),
        ("Avg Handle Time", "4:32", "▼ 0:18 improvement",    True),
        ("CSAT Score",      "94%",  "▲ 2% this week",        True),
        ("Escalations",     "6",    "▼ 3 from yesterday",    True),
    ]

    _SHORTCUTS = [
        ("New Ticket",   "[ + ]"),
        ("Knowledge",    "[ 📖 ]"),
        ("Escalate",     "[ ↑ ]"),
        ("Templates",    "[ ≡ ]"),
        ("Reports",      "[ 📊 ]"),
        ("Schedule",     "[ 📅 ]"),
        ("Contacts",     "[ 👥 ]"),
        ("Settings",     "[ ⚙ ]"),
    ]

    _ACTIVITY = [
        ("09:41 AM", "James H.",    "Playlist request",    "Resolved",  True),
        ("09:38 AM", "Sara M.",     "Billing inquiry",     "Pending",   False),
        ("09:30 AM", "Tom K.",      "Song ID request",     "Resolved",  True),
        ("09:22 AM", "Lily P.",     "Account access",      "Escalated", False),
        ("09:15 AM", "Marcus D.",   "Recommendation",      "Resolved",  True),
    ]

    def __init__(self):
        super().__init__()
        self.title("Music Concierge — Support Dashboard")
        self.geometry("1280x780")
        self._center_window(1280, 780)
        self.minsize(960, 640)

        self._build_ui()
        self.bind("<Configure>", self._on_resize)

    # ── Centering ──────────────────────────────────────────────────────────────
    def _center_window(self, w: int, h: int):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── UI Construction ────────────────────────────────────────────────────────
    def _build_ui(self):
        self._canvas = Canvas(self, highlightthickness=0, bd=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)

        overlay = ctk.CTkFrame(self, fg_color="transparent")
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        overlay.columnconfigure(1, weight=1)
        overlay.rowconfigure(0, weight=1)

        # ── Sidebar with navigation callback ───────────────────────────────────
        self._sidebar = Sidebar(overlay, on_navigate=self._navigate)
        self._sidebar.grid(row=0, column=0, sticky="nsew")

        # ── Page container (column 1) ──────────────────────────────────────────
        self._page_container = ctk.CTkFrame(overlay, fg_color="transparent")
        self._page_container.grid(row=0, column=1, sticky="nsew")
        self._page_container.columnconfigure(0, weight=1)
        self._page_container.rowconfigure(0, weight=1)

        # ── Overview page (formerly Cores.XML) ─────────────────────────────────────
        self._overview_page = CoresXMLPage(self._page_container)
        self._overview_page.grid(row=0, column=0, sticky="nsew")

        # Start on Overview and start time updates
        self._navigate("Overview")
        self._update_time()

        self.update_idletasks()
        set_background(self._canvas, self.winfo_width(), self.winfo_height())

    # ── Page navigation ────────────────────────────────────────────────────────
    def _navigate(self, page: str):
        if page == "Overview":
            self._overview_page.lift()
        elif page == "C:\\Kaleidovision":
            self._open_kaleidovision()
        elif page == "Sound Device Setting":
            self._open_sound_device_setting()
        elif page == "Unlock Windows Shell":
            self._unlock_windows_shell()
        elif page == "Windows Reliability Reports":
            self._open_reliability_reports()
        elif page == "Windows Event Viewer":
            self._open_event_viewer()
    
    def _open_kaleidovision(self):
        """Launch C:\\Kaleidovision folder."""
        import subprocess
        try:
            subprocess.Popen(['explorer', 'C:\\Kaleidovision'], shell=True)
        except Exception as e:
            print(f"Error launching Kaleidovision folder: {e}")
    
    def _open_sound_device_setting(self):
        """Launch Sound Device Settings."""
        import subprocess
        try:
            subprocess.Popen(['C:\\Windows\\System32\\mmsys.cpl'], shell=True)
        except Exception as e:
            print(f"Error launching Sound Device Settings: {e}")
    
    def _unlock_windows_shell(self):
        """Launch Windows Explorer with confirmation dialog."""
        import subprocess
        
        # Create confirmation dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Unlock Windows Shell")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.configure(fg_color="#1A0F0A")
        
        # Center the dialog
        dialog.update_idletasks()
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        x = (sw - 400) // 2
        y = (sh - 200) // 2
        dialog.geometry(f"400x200+{x}+{y}")
        
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        
        # Content frame
        frame = ctk.CTkFrame(dialog, fg_color=CARD_BG, corner_radius=CORNER)
        frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        
        # Warning message
        ctk.CTkLabel(
            frame,
            text="⚠️ Unlock Windows Shell?",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ACCENT, anchor="center"
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            frame,
            text="This will launch Windows Explorer.\nDo you want to continue?",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_BRIGHT, anchor="center", justify="center"
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        # Button frame
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        
        def on_yes():
            try:
                subprocess.Popen(['C:\\Windows\\explorer.exe'])
            except Exception as e:
                print(f"Error launching Explorer: {e}")
            dialog.destroy()
        
        def on_no():
            dialog.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="Yes",
            font=ctk.CTkFont(size=12),
            fg_color=ACCENT,
            hover_color="#E8A87C",
            text_color="#1A0F0A",
            width=100,
            height=35,
            command=on_yes
        ).grid(row=0, column=0, sticky="e", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text="No",
            font=ctk.CTkFont(size=12),
            fg_color=DIVIDER,
            hover_color=ACCENT,
            text_color=TEXT_BRIGHT,
            width=100,
            height=35,
            command=on_no
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))
        
        dialog.grab_set()
        dialog.wait_window(dialog)
    
    def _open_reliability_reports(self):
        """Launch Windows Reliability Reports with confirmation."""
        import subprocess
        
        # Create confirmation dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Windows Reliability Reports")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.configure(fg_color="#1A0F0A")
        
        # Center the dialog
        dialog.update_idletasks()
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        x = (sw - 400) // 2
        y = (sh - 200) // 2
        dialog.geometry(f"400x200+{x}+{y}")
        
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        
        # Content frame
        frame = ctk.CTkFrame(dialog, fg_color=CARD_BG, corner_radius=CORNER)
        frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        
        # Warning message
        ctk.CTkLabel(
            frame,
            text="📊 Windows Reliability Reports?",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ACCENT, anchor="center"
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            frame,
            text="This will launch Windows Reliability Reports.\nDo you want to continue?",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_BRIGHT, anchor="center", justify="center"
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        # Button frame
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        
        def on_yes():
            try:
                subprocess.Popen(['perfmon', '/rel'], shell=True)
            except Exception as e:
                print(f"Error launching Reliability Reports: {e}")
            dialog.destroy()
        
        def on_no():
            dialog.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="Yes",
            font=ctk.CTkFont(size=12),
            fg_color=ACCENT,
            hover_color="#E8A87C",
            text_color="#1A0F0A",
            width=100,
            height=35,
            command=on_yes
        ).grid(row=0, column=0, sticky="e", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text="No",
            font=ctk.CTkFont(size=12),
            fg_color=DIVIDER,
            hover_color=ACCENT,
            text_color=TEXT_BRIGHT,
            width=100,
            height=35,
            command=on_no
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))
        
        dialog.grab_set()
        dialog.wait_window(dialog)
    
    def _open_event_viewer(self):
        """Launch Windows Event Viewer with confirmation."""
        import subprocess
        
        # Create confirmation dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Windows Event Viewer")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.configure(fg_color="#1A0F0A")
        
        # Center the dialog
        dialog.update_idletasks()
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        x = (sw - 400) // 2
        y = (sh - 200) // 2
        dialog.geometry(f"400x200+{x}+{y}")
        
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        
        # Content frame
        frame = ctk.CTkFrame(dialog, fg_color=CARD_BG, corner_radius=CORNER)
        frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        
        # Warning message
        ctk.CTkLabel(
            frame,
            text="📝 Windows Event Viewer?",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ACCENT, anchor="center"
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            frame,
            text="This will launch Windows Event Viewer.\nDo you want to continue?",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_BRIGHT, anchor="center", justify="center"
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        # Button frame
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        
        def on_yes():
            try:
                subprocess.Popen(['eventvwr.msc'], shell=True)
            except Exception as e:
                print(f"Error launching Event Viewer: {e}")
            dialog.destroy()
        
        def on_no():
            dialog.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="Yes",
            font=ctk.CTkFont(size=12),
            fg_color=ACCENT,
            hover_color="#E8A87C",
            text_color="#1A0F0A",
            width=100,
            height=35,
            command=on_yes
        ).grid(row=0, column=0, sticky="e", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text="No",
            font=ctk.CTkFont(size=12),
            fg_color=DIVIDER,
            hover_color=ACCENT,
            text_color=TEXT_BRIGHT,
            width=100,
            height=35,
            command=on_no
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))
        
        dialog.grab_set()
        dialog.wait_window(dialog)

    def _update_time(self):
        self._sidebar.update_time()
        self._time_after_id = self.after(1000, self._update_time)

    # ── Top Bar ────────────────────────────────────────────────────────────────
    def _build_topbar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        bar.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            bar, text="Support Dashboard",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_BRIGHT, anchor="w"
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            bar, text="Wednesday, February 19, 2026",
            font=ctk.CTkFont(size=12), text_color=TEXT_DIM, anchor="w"
        ).grid(row=1, column=0, sticky="w")

    # ── Stat Cards ─────────────────────────────────────────────────────────────
    def _build_stats(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=1, column=0, sticky="ew", padx=20, pady=8)
        for i in range(3):
            frame.columnconfigure(i, weight=1)

        for idx, (title, value, change, positive) in enumerate(self._STATS):
            card = StatCard(frame, title, value, change, positive)
            card.grid(row=idx // 3, column=idx % 3, sticky="ew",
                      padx=6, pady=6)

    # ── Middle Row: Shortcuts + Quick Note ────────────────────────────────────
    def _build_middle(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid(row=2, column=0, sticky="ew", padx=20, pady=8)
        row.columnconfigure(0, weight=2)
        row.columnconfigure(1, weight=1)

        # Important Shortcuts
        shortcuts_frame = ctk.CTkFrame(row, corner_radius=CORNER, fg_color=CARD_BG)
        shortcuts_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            shortcuts_frame, text="IMPORTANT SHORTCUTS",
            font=ctk.CTkFont(size=10), text_color=TEXT_DIM, anchor="w"
        ).pack(fill="x", padx=14, pady=(14, 8))

        grid = ctk.CTkFrame(shortcuts_frame, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=(0, 14))
        for i in range(4):
            grid.columnconfigure(i, weight=1)

        for idx, (label, icon) in enumerate(self._SHORTCUTS):
            ShortcutButton(grid, label=label, icon=icon).grid(
                row=idx // 4, column=idx % 4, padx=4, pady=4, sticky="ew"
            )

        # Quick Note
        note_frame = ctk.CTkFrame(row, corner_radius=CORNER, fg_color=CARD_BG)
        note_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(
            note_frame, text="QUICK NOTE",
            font=ctk.CTkFont(size=10), text_color=TEXT_DIM, anchor="w"
        ).pack(fill="x", padx=14, pady=(14, 6))

        note_box = ctk.CTkTextbox(
            note_frame, height=120, corner_radius=8,
            fg_color="#251818", text_color=TEXT_BRIGHT,
            font=ctk.CTkFont(size=12),
            border_color=DIVIDER, border_width=1,
        )
        note_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        note_box.insert("0.0", "Shift handover notes:\n- Check escalation queue\n- Follow up with Sara M.")

        ctk.CTkButton(
            note_frame, text="Save Note",
            fg_color=ACCENT, hover_color="#A06840",
            text_color="#1A0F0A", font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8, height=32,
        ).pack(fill="x", padx=10, pady=(0, 14))

    # ── Recent Activity ────────────────────────────────────────────────────────
    def _build_activity(self, parent):
        frame = ctk.CTkFrame(parent, corner_radius=CORNER, fg_color=CARD_BG)
        frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(8, 20))
        frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame, text="RECENT ACTIVITY",
            font=ctk.CTkFont(size=10), text_color=TEXT_DIM, anchor="w"
        ).pack(fill="x", padx=14, pady=(14, 4))

        # Header row
        header = ctk.CTkFrame(frame, fg_color=DIVIDER, corner_radius=6)
        header.pack(fill="x", padx=10, pady=(0, 4))
        header.columnconfigure((0, 1, 2, 3), weight=1)
        for col, text in enumerate(["Time", "Client", "Action", "Status"]):
            ctk.CTkLabel(
                header, text=text.upper(),
                font=ctk.CTkFont(size=10), text_color=TEXT_DIM, anchor="w"
            ).grid(row=0, column=col, sticky="ew", padx=8, pady=6)

        for time, client, action, status, ok in self._ACTIVITY:
            row = ActivityRow(frame, time, client, action, status, ok)
            row.pack(fill="x", padx=10)
            ctk.CTkFrame(frame, height=1, fg_color=DIVIDER).pack(fill="x", padx=10)

        # bottom padding
        ctk.CTkFrame(frame, height=8, fg_color="transparent").pack()

    # ── Resize handler ─────────────────────────────────────────────────────────
    def _on_resize(self, event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w > 1 and h > 1:
            set_background(self._canvas, w, h)


# ── Entry Point ────────────────────────────────────────────────────────────────
def _get_config_path() -> str:
    """Return the path to config.env next to the exe or script."""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "config.env")


def _get_edit_cores_password():
    """Load edit cores password from config.env file."""
    config_path = _get_config_path()
    password = "editcores"  # default
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            for line in f:
                if line.startswith("EDIT_CORES_PASSWORD="):
                    password = line.strip().split("=", 1)[1]
                    break
    return password


def check_password(root: ctk.CTk) -> bool:
    """Show password dialog on top of *root* and return True if correct."""
    config_path = _get_config_path()
    password = "dvpdvpdvp1"  # default
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            for line in f:
                if line.startswith("APP_PASSWORD="):
                    password = line.strip().split("=", 1)[1]
                    break

    # Hide the main root while the password dialog is shown
    root.withdraw()

    dialog = ctk.CTkToplevel(root)
    dialog.title("Authentication Required")
    dialog.configure(fg_color="#1A0F0A")
    dialog.resizable(False, False)

    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() - 400) // 2
    y = (dialog.winfo_screenheight() - 220) // 2
    dialog.geometry(f"400x220+{x}+{y}")

    dialog.columnconfigure(0, weight=1)
    dialog.rowconfigure(0, weight=1)

    frame = ctk.CTkFrame(dialog, fg_color="#251818", corner_radius=12)
    frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
    frame.columnconfigure(0, weight=1)

    ctk.CTkLabel(
        frame, text="🔒 Enter Password",
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color="#C1784A"
    ).grid(row=0, column=0, pady=(20, 10))

    error_label = ctk.CTkLabel(
        frame, text="",
        font=ctk.CTkFont(size=11),
        text_color="#E74C3C"
    )
    error_label.grid(row=1, column=0, pady=(0, 5))

    password_entry = ctk.CTkEntry(
        frame, show="●",
        font=ctk.CTkFont(size=14),
        fg_color="#150D0D",
        text_color="#F0E6DC",
        border_color="#5A4A3A",
        border_width=1,
        width=200
    )
    password_entry.grid(row=2, column=0, pady=(0, 15))
    password_entry.after(100, password_entry.focus)

    result = [False]

    def verify():
        if password_entry.get() == password:
            result[0] = True
            dialog.destroy()
        else:
            error_label.configure(text="Incorrect password. Please try again.")
            password_entry.delete(0, "end")

    password_entry.bind("<Return>", lambda e: verify())

    ctk.CTkButton(
        frame, text="Unlock",
        font=ctk.CTkFont(size=13, weight="bold"),
        fg_color="#C1784A",
        hover_color="#A06840",
        text_color="#1A0F0A",
        command=verify,
        width=120,
        height=35
    ).grid(row=3, column=0, pady=(0, 20))

    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    dialog.grab_set()
    root.wait_window(dialog)

    return result[0]


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    # Create the single CTk root up front; password dialog runs on top of it
    _root = DashboardApp.__new__(DashboardApp)
    ctk.CTk.__init__(_root)
    _root.withdraw()  # keep hidden until auth passes
    if check_password(_root):
        _root.deiconify()
        DashboardApp.__init__(_root)
        _root.update_idletasks()
        _root.update()
        
        # Maximize window after short delay to ensure proper window handle
        def do_maximize():
            try:
                import ctypes
                # Get window handle by title since GetForegroundWindow may return wrong window
                title = _root.title()
                hwnd = ctypes.windll.user32.FindWindowW(None, title)
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE = 3
                else:
                    _root.state('zoomed')
            except Exception:
                _root.state('zoomed')
        
        _root.after(100, do_maximize)
        
        # Add proper cleanup handler
        def on_main_closing():
            try:
                # Cancel all after callbacks
                if hasattr(_root, '_time_after_id'):
                    _root.after_cancel(_root._time_after_id)
                # Force close all child windows
                for widget in _root.winfo_children():
                    if isinstance(widget, ctk.CTkToplevel):
                        try:
                            widget.destroy()
                        except:
                            pass
            except Exception:
                pass
            _root.quit()
            _root.destroy()
            import os
            os._exit(0)
        
        _root.protocol("WM_DELETE_WINDOW", on_main_closing)
        _root.mainloop()
    else:
        _root.destroy()
        import os
        os._exit(0)
