import subprocess
import tkinter as tk
from tkinter import scrolledtext

def launch_steam_game(id):
    subprocess.call("C:\\Program Files (x86)\\Steam\\\Steam.exe -applaunch %s" % id)

def launch_hollow_knight():
    launch_steam_game("367520")

def launch_silksong():
    launch_steam_game("1030300")

class LurienApp(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent)

        launch_frame = tk.LabelFrame(self, text="steam launch")
        launch_frame.pack(anchor="w")

        hk_button = tk.Button(launch_frame, text="Hollow Knight", command=launch_hollow_knight)
        ss_button = tk.Button(launch_frame, text="Silksong", command=launch_silksong)
        hk_button.pack(side="left")
        ss_button.pack(side="left")

        self.log_text = scrolledtext.ScrolledText(self)
        self.log_text.configure(state="disabled")
        self.log_text.pack(anchor="w")

        self.watch()

    def watch(self):
        self.log("Lurien is watching...")
        self.after(1000, self.watch)

    def log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")
        
def main():
    root = tk.Tk()
    root.title("lurien")
    app = LurienApp(root)
    app.pack()
    root.mainloop()

if __name__ == "__main__":
    main()