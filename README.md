# Music Concierge Support Dashboard

A modern support dashboard built with **customtkinter** and **pywinstyles**, featuring a Fluent/Acrylic blur effect and a warm dark gradient theme.

## Features

- **Fluent/Acrylic blur** via `pywinstyles` (Windows 10/11)
- **Horizontal gradient background** — `#2D1B24` → `#7A4D2E`
- **Stat Cards** — 6 KPI cards in a responsive 3-column grid
- **Sidebar navigation** with brand logo and agent info
- **Important Shortcuts** — 2×4 grid of quick-action buttons
- **Quick Note** — editable textbox with save button
- **Recent Activity** table with colour-coded statuses
- **Weather Widget** — McLean, VA display (top-right)
- Center-screen on launch, responsive on resize

## Requirements

- Python 3.9+
- Windows 10/11 (for Acrylic effect; runs on other OS without blur)

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

## Project Structure

```
mc-support-dashboard/
├── app.py            # Main application
├── requirements.txt  # Python dependencies
└── README.md
```
