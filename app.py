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
        self._time_lbl = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_BRIGHT, anchor="w"
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
                text=f"  {icon}   {label}",
                font=ctk.CTkFont(size=13),
                fg_color="#2E1F1A" if is_active else "transparent",
                hover_color="#2E1F1A",
                text_color=ACCENT if is_active else TEXT_BRIGHT,
                anchor="w",
                corner_radius=8,
                height=40,
                command=lambda l=label: self._navigate(l),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._buttons[label] = btn

        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)
        ctk.CTkFrame(self, height=1, fg_color=DIVIDER).pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(
            self, text="👤  Agent: You",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM, anchor="w"
        ).pack(fill="x", padx=18, pady=(0, 22))

    def update_time(self):
        from datetime import datetime
        import time
        now = datetime.now()
        self._time_lbl.configure(text=now.strftime("%I:%M:%S %p").lstrip("0"))
        self._tz_lbl.configure(text=time.tzname[0] if time.daylight == 0 else time.tzname[1])

    def _navigate(self, label: str):
        for name, btn in self._buttons.items():
            if name == label:
                btn.configure(fg_color="#2E1F1A", text_color=ACCENT)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_BRIGHT)
        self._active = label
        self._on_navigate(label)


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
            btn_frame, text="📋 Copy Content",
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
        folder_name, xml_path = find_latest_xml_file("config.xml")

        if folder_name is None:
            self._source_lbl.configure(
                text=f"Base path not found: {KV_BASE}", text_color=TEXT_RED
            )
            self._set_textbox(self._readable_box,
                              f"[Directory not found]\n\nExpected base path:\n  {KV_BASE}\n\n"
                              "Please ensure Kaleidovision is installed and the config folder exists.")
            self._set_textbox(self._raw_box, "")
            return

        if not os.path.isfile(xml_path):
            self._source_lbl.configure(
                text=f"config.xml not found in: {folder_name}", text_color=TEXT_RED
            )
            self._set_textbox(self._readable_box,
                              f"[File not found]\n\nLooked for:\n  {xml_path}")
            self._set_textbox(self._raw_box, "")
            return

        dt = _folder_datetime(folder_name)
        if dt:
            ts = dt.strftime("%d %b %Y  %I:%M %p")
        else:
            ts = folder_name

        self._source_lbl.configure(
            text=f"Latest config folder: {folder_name}  ({ts})  —  {xml_path}",
            text_color=TEXT_DIM
        )

        readable, raw = pretty_xml(xml_path)
        self._set_textbox(self._readable_box, readable)
        self._set_textbox(self._raw_box, raw)
        self._switch_tab(self._active_tab)


# ── Cores.XML Page ─────────────────────────────────────────────────────────────
class CoresXMLPage(ctk.CTkFrame):
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
            btn_frame, text="📋 Copy Content",
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
        """Open the cores.xml file in Notepad."""
        import subprocess
        folder_name, xml_path = find_latest_cores_xml()
        if xml_path and os.path.isfile(xml_path):
            subprocess.Popen(["notepad.exe", xml_path])

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
        content_frame.columnconfigure(0, weight=1)  # Left panel
        content_frame.columnconfigure(1, weight=1)  # Right panel
        content_frame.rowconfigure(0, weight=1)     # Both fill full height
        self._readable_frame.rowconfigure(2, weight=1)
        self._readable_frame.columnconfigure(0, weight=1)

        # Left side: Channel boxes
        left_frame = ctk.CTkScrollableFrame(
            content_frame, fg_color="transparent",
            scrollbar_button_color=DIVIDER,
            scrollbar_button_hover_color=ACCENT,
            width=420
        )
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        # Force internal canvas to fill
        left_frame._parent_canvas.configure(height=800)

        # Store channel data and button references for toggle logic
        self._channel_buttons = {}
        self._current_channel = None
        self._current_menu = None

        for idx, channel in enumerate(channels, start=1):
            channel_box = self._create_channel_box(left_frame, idx, channel)
            channel_box.grid(row=idx - 1, column=0, sticky="ew", pady=8)

        # Right side: Details panel
        self._details_scroll_frame = ctk.CTkScrollableFrame(
            content_frame, fg_color=CARD_BG, corner_radius=CORNER,
            scrollbar_button_color=DIVIDER,
            scrollbar_button_hover_color=ACCENT,
        )
        self._details_scroll_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self._details_scroll_frame.columnconfigure(0, weight=1)
        # Force internal canvas to fill
        self._details_scroll_frame._parent_canvas.configure(height=800)

        # Details panel header
        self._details_header = ctk.CTkLabel(
            self._details_scroll_frame, text="Select a channel and menu",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_BRIGHT, anchor="w"
        )
        self._details_header.grid(row=0, column=0, sticky="w", padx=14, pady=14)

        # Details content area
        self._details_content = ctk.CTkFrame(self._details_scroll_frame, fg_color="transparent")
        self._details_content.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 14))
        self._details_content.columnconfigure(0, weight=1)

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

        tracking_text = f"Tracking: {channel['tracking_period'] if channel['tracking_period'] else 'N/A'}"
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

        for menu_name in ["Music Schedules", "Overriding Schedules", "Logs"]:
            btn = ctk.CTkButton(
                btn_frame, text=menu_name,
                fg_color="#2A1E1A", hover_color="#3D2B22",
                text_color=TEXT_BRIGHT, font=ctk.CTkFont(size=11),
                corner_radius=6, height=28, width=110,
                command=lambda cid=channel_id, ch=channel, m=menu_name: self._on_menu_click(cid, ch, m)
            )
            btn.pack(side="left", padx=(0, 6))
            menu_buttons[menu_name] = btn

        self._channel_buttons[channel_id] = {
            "channel": channel,
            "buttons": menu_buttons,
            "box": channel_box
        }

        return channel_box

    def _on_menu_click(self, channel_id: str, channel: dict, menu_name: str):
        """Handle menu button click - toggle display in details panel."""
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
        """Display Music Schedules content with extracted XML data."""
        # Extract music schedule data from the stored XML root
        schedule_data = self._extract_music_schedule(channel.get('entity_id', ''))

        if not schedule_data:
            ctk.CTkLabel(
                self._details_content, text="No Music Schedule data found for this channel.",
                font=ctk.CTkFont(size=12), text_color=TEXT_DIM, anchor="w"
            ).grid(row=0, column=0, sticky="w", pady=(0, 10))
            return

        # Day and Zone info header
        header_frame = ctk.CTkFrame(self._details_content, fg_color=CARD_BG, corner_radius=CORNER)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_frame, text=f"Day ID: {schedule_data.get('day_id', 'N/A')}  |  Zone ID: {schedule_data.get('zone_id', 'N/A')}",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=12, pady=10)

        # Properties grid
        properties = schedule_data.get('properties', {})
        if properties:
            props_frame = ctk.CTkFrame(self._details_content, fg_color="transparent")
            props_frame.grid(row=1, column=0, sticky="ew")
            props_frame.columnconfigure((0, 1), weight=1)

            row = 0
            for key, value in properties.items():
                # Key label
                ctk.CTkLabel(
                    props_frame, text=key,
                    font=ctk.CTkFont(size=11), text_color=TEXT_DIM, anchor="w"
                ).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)

                # Value label
                ctk.CTkLabel(
                    props_frame, text=str(value),
                    font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_BRIGHT, anchor="w"
                ).grid(row=row, column=1, sticky="w", pady=4)

                row += 1

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

    def _show_overriding_schedules(self, channel: dict):
        """Display Overriding Schedules content."""
        ctk.CTkLabel(
            self._details_content, text="Overriding Schedules",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT, anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        content = ctk.CTkTextbox(
            self._details_content, corner_radius=8,
            fg_color="#150D0D", text_color=TEXT_BRIGHT,
            font=ctk.CTkFont(family="Consolas", size=11),
            border_color=DIVIDER, border_width=1,
            wrap="word"
        )
        content.grid(row=1, column=0, sticky="nsew")
        content.insert("0.0", f"Overriding schedule data for {channel['name']}...")
        content.configure(state="disabled")

    def _show_logs(self, channel: dict):
        """Display Logs content."""
        ctk.CTkLabel(
            self._details_content, text="Logs",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT, anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        content = ctk.CTkTextbox(
            self._details_content, corner_radius=8,
            fg_color="#150D0D", text_color=TEXT_BRIGHT,
            font=ctk.CTkFont(family="Consolas", size=11),
            border_color=DIVIDER, border_width=1,
            wrap="word"
        )
        content.grid(row=1, column=0, sticky="nsew")
        content.insert("0.0", f"Log entries for {channel['name']}...")
        content.configure(state="disabled")

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
            ts = dt.strftime("%d %b %Y  %I:%M %p")
        else:
            ts = folder_name

        self._source_lbl.configure(
            text=f"Latest config folder: {folder_name}  ({ts})  —  {xml_path}",
            text_color=TEXT_DIM
        )

        readable, raw = pretty_xml(xml_path)
        self._build_readable_view(xml_path, readable)
        self._set_textbox(self._raw_box, raw)
        self._switch_tab(self._active_tab)


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

    def _update_time(self):
        self._sidebar.update_time()
        self.after(1000, self._update_time)

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
if __name__ == "__main__":
    app = DashboardApp()
    app.mainloop()
