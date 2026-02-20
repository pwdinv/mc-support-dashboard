import customtkinter as ctk

print("Starting test...")
ctk.set_appearance_mode("dark")

print("Creating dialog...")
dialog = ctk.CTk()
dialog.title("Test Password")
dialog.geometry("400x200")

print("Adding widgets...")
label = ctk.CTkLabel(dialog, text="🔒 Enter Password", font=ctk.CTkFont(size=18, weight="bold"))
label.pack(pady=20)

entry = ctk.CTkEntry(dialog, show="●", width=200)
entry.pack(pady=10)

def verify():
    print(f"Entered: {entry.get()}")
    dialog.destroy()

btn = ctk.CTkButton(dialog, text="Unlock", command=verify)
btn.pack(pady=10)

print("Starting mainloop...")
dialog.mainloop()
print("Done!")
