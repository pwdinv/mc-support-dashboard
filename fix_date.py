import os

# Read the current app.py
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if already modified
if "📅" in content:
    print("Date badge already added!")
else:
    # Find and replace the date section
    old_section = '''        dt = _folder_datetime(folder_name)
        if dt:
            ts = dt.strftime("%d %b %Y  %I:%M %p")
        else:
            ts = folder_name

        self._source_lbl.configure(
            text=f"Latest config folder: {folder_name}  ({ts})  —  {xml_path}",
            text_color=TEXT_DIM
        )

        readable, raw = pretty_xml(xml_path)'''

    new_section = '''        dt = _folder_datetime(folder_name)
        if dt:
            # Stylish formatted date
            ts = dt.strftime("%d %b %Y at %I:%M %p")
        else:
            ts = folder_name

        self._source_lbl.configure(
            text=f"Latest config folder: {folder_name}  —  {xml_path}",
            text_color=TEXT_DIM
        )
        
        # Create stylish date badge
        if not hasattr(self, '_date_badge'):
            self._date_badge = ctk.CTkLabel(
                left_frame, text="",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=ACCENT,
                fg_color="#2A1E1A",
                corner_radius=6
            )
            self._date_badge.grid(row=2, column=0, sticky="w", pady=(6, 0))
        self._date_badge.configure(text=f"📅 {ts}" if dt else ts)

        readable, raw = pretty_xml(xml_path)'''

    if old_section in content:
        content = content.replace(old_section, new_section)
        print("✓ Updated date display")
    else:
        print("Could not find section to replace")
        exit(1)

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Changes applied!")
