"""
Music Concierge Support Dashboard
==================================
A customtkinter-based support dashboard with Fluent/Acrylic blur effect.
"""

import sys
import tkinter as tk
from tkinter import Canvas

import customtkinter as ctk

try:
    import pywinstyles
    HAS_PYWINSTYLES = True
except ImportError:
    HAS_PYWINSTYLES = False

# ── Theme ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Palette ────────────────────────────────────────────────────────────────────
GRAD_LEFT   = "#2D1B24"
GRAD_RIGHT  = "#7A4D2E"
CARD_BG     = "#1E1414"
SIDEBAR_BG  = "#180F0F"
ACCENT      = "#C8865A"
TEXT_DIM    = "#9A8A82"
TEXT_BRIGHT = "#F5EDE8"
TEXT_GREEN  = "#5DBB8A"
TEXT_RED    = "#E05C5C"
DIVIDER     = "#3A2A24"
CORNER      = 12
SIDEBAR_W   = 230


# ── Gradient Canvas ────────────────────────────────────────────────────────────
def _hex_lerp(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def draw_gradient(canvas: Canvas, w: int, h: int) -> None:
    canvas.delete("gradient")
    step = max(1, w // 300)
    for x in range(0, w, step):
        colour = _hex_lerp(GRAD_LEFT, GRAD_RIGHT, x / max(w - 1, 1))
        canvas.create_line(x, 0, x, h, fill=colour, tags="gradient")


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
        ("⌂", "Dashboard"),
        ("♪", "Requests"),
        ("✉", "Messages"),
        ("♟", "Playlists"),
        ("★", "Favourites"),
        ("⚙", "Settings"),
    ]

    def __init__(self, master, **kw):
        super().__init__(master, width=SIDEBAR_W, corner_radius=0,
                         fg_color=SIDEBAR_BG, **kw)
        self.pack_propagate(False)
        self._build()

    def _build(self):
        # Brand
        ctk.CTkLabel(
            self, text="🎵  MC Support",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ACCENT, anchor="w"
        ).pack(fill="x", padx=18, pady=(28, 8))

        ctk.CTkFrame(self, height=1, fg_color=DIVIDER).pack(fill="x", padx=12, pady=(0, 16))

        # Nav
        for icon, label in self._NAV:
            ctk.CTkButton(
                self,
                text=f"  {icon}   {label}",
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color="#2E1F1A",
                text_color=TEXT_BRIGHT,
                anchor="w",
                corner_radius=8,
                height=40,
            ).pack(fill="x", padx=10, pady=2)

        # Spacer
        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)

        ctk.CTkFrame(self, height=1, fg_color=DIVIDER).pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(
            self, text="👤  Agent: You",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM, anchor="w"
        ).pack(fill="x", padx=18, pady=(0, 22))


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

        # Apply Fluent/Acrylic blur (Windows only)
        if HAS_PYWINSTYLES and sys.platform == "win32":
            try:
                pywinstyles.apply_style(self, "acrylic")
            except Exception:
                pass

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
        # Root: gradient canvas fills everything
        self._canvas = Canvas(self, highlightthickness=0, bd=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Overlay frame (transparent) sits on top of canvas
        overlay = ctk.CTkFrame(self, fg_color="transparent")
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        overlay.columnconfigure(1, weight=1)
        overlay.rowconfigure(0, weight=1)

        # ── Sidebar ────────────────────────────────────────────────────────────
        sidebar = Sidebar(overlay)
        sidebar.grid(row=0, column=0, sticky="nsew")

        # ── Main content ───────────────────────────────────────────────────────
        main = ctk.CTkScrollableFrame(overlay, fg_color="transparent",
                                      scrollbar_button_color=DIVIDER,
                                      scrollbar_button_hover_color=ACCENT)
        main.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        main.columnconfigure(0, weight=1)

        self._build_topbar(main)
        self._build_stats(main)
        self._build_middle(main)
        self._build_activity(main)

        # Initial gradient draw
        self.update_idletasks()
        draw_gradient(self._canvas, self.winfo_width(), self.winfo_height())

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

        WeatherWidget(bar).grid(row=0, column=1, rowspan=2, sticky="e", padx=(10, 0))

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
            draw_gradient(self._canvas, w, h)


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = DashboardApp()
    app.mainloop()
