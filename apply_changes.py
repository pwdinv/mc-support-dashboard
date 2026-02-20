import os
import sys

def main():
    # Read the file
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already modified
    if "📅" in content:
        print("Already modified!")
        return
    
    # Find and replace the date section - using the exact lines from the file
    old_date_line = 'ts = dt.strftime("%d %b %Y  %I:%M %p")'
    new_date_line = 'ts = dt.strftime("%d %b %Y at %I:%M %p")'
    
    if old_date_line in content:
        content = content.replace(old_date_line, new_date_line)
        print("✓ Updated date format")
    else:
        print("✗ Could not find date format line")
        return
    
    # Remove date from source label line
    old_source = 'text=f"Latest config folder: {folder_name}  ({ts})  —  {xml_path}",'
    new_source = 'text=f"Latest config folder: {folder_name}  —  {xml_path}",'
    
    if old_source in content:
        content = content.replace(old_source, new_source)
        print("✓ Updated source label")
    else:
        print("✗ Could not find source label line")
        return
    
    # Add date badge creation after the source label configure
    old_section = '''        self._source_lbl.configure(
            text=f"Latest config folder: {folder_name}  —  {xml_path}",
            text_color=TEXT_DIM
        )

        readable, raw = pretty_xml(xml_path)'''
    
    new_section = '''        self._source_lbl.configure(
            text=f"Latest config folder: {folder_name}  —  {xml_path}",
            text_color=TEXT_DIM
        )
        
        # Create or update stylish date badge
        if hasattr(self, '_date_badge'):
            self._date_badge.configure(text=f"📅 {ts}" if dt else ts)
        else:
            # Get reference to left_frame from title bar
            title_bar = self.winfo_children()[0]
            left_frame = title_bar.winfo_children()[0]
            # Create stylish date badge
            self._date_badge = ctk.CTkLabel(
                left_frame, text=f"📅 {ts}" if dt else ts,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=ACCENT,
                fg_color="#2A1E1A",
                corner_radius=6,
                padx=10, pady=4
            )
            self._date_badge.grid(row=2, column=0, sticky="w", pady=(6, 0))

        readable, raw = pretty_xml(xml_path)'''
    
    if old_section in content:
        content = content.replace(old_section, new_section)
        print("✓ Added stylish date badge")
    else:
        print("✗ Could not find section to add badge")
        return
    
    # Write back
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("All changes applied successfully!")

if __name__ == "__main__":
    main()
