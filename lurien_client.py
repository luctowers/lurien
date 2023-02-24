import os
import platform
import subprocess
import json
import uuid
import tkinter as tk
from tkinter import scrolledtext

# TODO: make sure there is a way to disable the client from the server

class UnsupportedPlatformException(Exception):
    def __init__(self):            
        super().__init__("unsupported platform '%s'" % platform.system())

def launch_steam_game(id):
    # TODO: MAKE THIS MULTIPLATFORM
    if platform.system() == "Windows":
        subprocess.call(["start", "steam://run/%s" % id], shell=True)
    elif platform.system() == "Darwin":
        subprocess.call(["open", "steam://run/%s" % id])
    else:
        raise UnsupportedPlatformException()

def launch_hollow_knight():
    launch_steam_game("367520")

def launch_silksong():
    launch_steam_game("1030300")

def locate_hollow_knight_save_dir():
    # TODO: MAKE THIS MULTIPLATFORM https://store.steampowered.com/news/app/367520/view/3406429723545099871
    if platform.system() == "Windows":
        save_dir = "~\\AppData\\LocalLow\\Team Cherry\\Hollow Knight"
    if platform.system() == "Darwin":
        save_dir = "~/Library/Application Support/unity.Team Cherry.Hollow Knight"
    else:
        raise UnsupportedPlatformException()
    save_dir = os.path.expanduser(save_dir)
    return save_dir

def locate_saves(save_dir):
    # TODO: MAKE SURE THIS DOESN'T FAIL WHEN SAVE DIR DOESN'T EXIST
    for root, dirs, files in os.walk(save_dir, topdown=False):
        for name in files:
            if name.endswith(".dat"):
                yield os.path.join(root, name)

def ensure_lurien_persist_dir():
    # TODO: MAKE THIS MULTIPLATFORM
    if platform.system() == "Windows":
        save_dir = "~\\AppData\\LocalLow\\Lurien"
    if platform.system() == "Darwin":
        save_dir = "~/Library/Application Support/net.lurien"
    else:
        raise UnsupportedPlatformException()
    save_dir = os.path.expanduser(save_dir)
    os.makedirs(save_dir, exist_ok=True)
    return save_dir

def get_lurien_persist_file():
    save_dir = ensure_lurien_persist_dir()
    return os.path.join(save_dir, "lurien.json")

def save_lurien_persist(data):
    with open(get_lurien_persist_file(), "w") as file:
        json.dump(data, file, indent="\t")

def get_lurien_persist():
    # TODO: HANDLE INVALID PERSIST FILE
    try:
        with open(get_lurien_persist_file(), "r") as file:
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

        self.init_persist()
        self.log("starting lurien client id = %s" % self.persist["clientId"])

        self.watch(first_watch=True)

    def init_persist(self):
        self.persist = get_lurien_persist()
        if self.persist is None:
            self.persist = {}
            self.persist["saves"] = {}
            self.persist["clientId"] = str(uuid.uuid4())
            self.save_persist()
    
    def save_persist(self):
        save_lurien_persist(self.persist)

    def watch(self, first_watch=False):
        persist_updated = False
        for save in locate_saves(locate_hollow_knight_save_dir()):
            mod_time = os.path.getmtime(save)
            if save in self.persist["saves"]:
                persist_mod_time = self.persist["saves"][save]["mtime"]
                if persist_mod_time < mod_time:
                    print("CHANGED " + save)
                if persist_mod_time != mod_time:
                    persist_updated = True
            else:
                persist_updated = True    
                self.persist["saves"][save] = {}
                if not first_watch:
                    print("NEW " + save)
            self.persist["saves"][save]["mtime"] = mod_time
        if persist_updated:
            self.save_persist()
        self.after(1000, self.watch)

    def log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")
        
def main():
    root = tk.Tk()
    root.title("Project Lurien")
    app = LurienApp(root)
    app.pack()
    root.mainloop()
    # print(get_lurien_data())
    # save_lurien_data({"id":"123"})

if __name__ == "__main__":
    main()
