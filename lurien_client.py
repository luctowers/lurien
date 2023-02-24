import os
import subprocess
import json
import tkinter as tk
from tkinter import scrolledtext

# TODO: make sure there is a way to disable the client from the server

def launch_steam_game(id):
    # TODO: MAKE THIS MULTIPLATFORM
    subprocess.call("C:\\Program Files (x86)\\Steam\\\Steam.exe -applaunch %s" % id)

def launch_hollow_knight():
    launch_steam_game("367520")

def launch_silksong():
    launch_steam_game("1030300")

def locate_hollow_knight_save_dir():
    # TODO: MAKE THIS MULTIPLATFORM https://store.steampowered.com/news/app/367520/view/3406429723545099871
    return os.path.join(os.environ["USERPROFILE"], "AppData\\LocalLow\\Team Cherry\\Hollow Knight")

def locate_saves(save_dir):
    # TODO: MAKE SURE THIS DOESN'T FAIL WHEN SAVE DIR DOESN'T EXIST
    for root, dirs, files in os.walk(save_dir, topdown=False):
        for name in files:
            if name.endswith(".dat"):
                yield os.path.join(root, name)

def ensure_lurien_save_dir():
    # TODO: MAKE THIS MULTIPLATFORM
    save_dir = os.path.join(os.environ["USERPROFILE"], "AppData\\LocalLow\\Lurien")
    os.makedirs(save_dir, exist_ok=True)
    return save_dir

def get_lurien_save_file():
    save_dir = ensure_lurien_save_dir()
    return os.path.join(save_dir, "lurien.json")

def save_lurien_data(data):
    with open(get_lurien_save_file(), "w") as file:
        json.dump(data, file)

def get_lurien_data():
    try:
        with open(get_lurien_save_file(), "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return None

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
    # print(get_lurien_data())
    # save_lurien_data({"id":"123"})

if __name__ == "__main__":
    main()