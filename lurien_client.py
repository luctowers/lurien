import os
import platform
import subprocess
import shutil
import json
import uuid
import re
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext

# TODO: make sure there is a way to disable the client from the server
# TODO: make sure nested dat is handled correctly
# TODO: improve robustness of staging

class UnsupportedPlatformException(Exception):
    def __init__(self):            
        super().__init__("unsupported platform '%s'" % platform.system())

ALL_SAVE_PATTERN = re.compile(r".*\.dat")
VERSIONED_SAVE_PATTERN = re.compile(r".*_[0-9]*\.[0-9]*(\.[0-9]*)*\.dat")
def is_regular_save_file(filename):
    return ALL_SAVE_PATTERN.fullmatch(filename) and not VERSIONED_SAVE_PATTERN.fullmatch(filename)

def shorten_save_file(save):
    return os.path.join("~hk", os.path.relpath(save, locate_hollow_knight_save_dir()))

def staged_save_file_name(save, mod_time, game_dir):
    savename = os.path.relpath(save, game_dir)[:-4].replace(os.sep, "--")
    timestamp = datetime.utcfromtimestamp(mod_time).strftime("%Y-%m-%d--%H-%M-%S")
    return "%s---%s.dat" % (savename, timestamp)

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
            if is_regular_save_file(name):
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

def ensure_lurien_staging_dir():
    staging_dir = os.path.join(ensure_lurien_persist_dir(), "staging")
    os.makedirs(staging_dir, exist_ok=True)
    return staging_dir

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
        launch_frame.grid(row=0, column=0, sticky="w")

        hk_button = tk.Button(launch_frame, text="Hollow Knight", command=launch_hollow_knight)
        ss_button = tk.Button(launch_frame, text="Silksong", command=launch_silksong)
        hk_button.pack(side="left")
        ss_button.pack(side="left")

        self.log_text = scrolledtext.ScrolledText(self)
        self.log_text.configure(state="disabled")
        self.log_text.grid(row=1, column=0, sticky="nswe")
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self.init_persist()
        self.log("starting lurien client id: %s" % self.persist["clientId"])
        self.log("hk save directory: %s" % locate_hollow_knight_save_dir())
        self.log("lurien is watching...")

        self.watch(first_watch=True)

    def init_persist(self):
        self.log("performing first time setup")
        self.persist = get_lurien_persist()
        if self.persist is None:
            self.persist = {}
            self.persist["clientId"] = str(uuid.uuid4())
            self.persist["saves"] = {}
            self.save_persist()
    
    def save_persist(self):
        save_lurien_persist(self.persist)

    def watch(self, first_watch=False):
        persist_updated = False
        for save in locate_saves(locate_hollow_knight_save_dir()):
            mod_time = int(os.path.getmtime(save))
            if save in self.persist["saves"]:
                persist_mod_time = self.persist["saves"][save]["mtime"]
                if persist_mod_time < mod_time:
                    self.log("save change detected: %s" % shorten_save_file(save))
                    self.stage(save, mod_time)
                if persist_mod_time != mod_time:
                    persist_updated = True
            else:
                persist_updated = True    
                self.persist["saves"][save] = {}
                if not first_watch:
                    self.log("new save detected: %s" % shorten_save_file(save))
                    self.stage(save, mod_time)
            self.persist["saves"][save]["mtime"] = mod_time
        if persist_updated:
            self.save_persist()
        self.after(1000, self.watch)
    
    def stage(self, save, mod_time):
        stagename = staged_save_file_name(save, mod_time, locate_hollow_knight_save_dir())
        self.log("staging file: %s" % stagename)
        stagedir = ensure_lurien_staging_dir()
        stagesave = os.path.join(stagedir, stagename)
        shutil.copyfile(save, stagesave)

    def log(self, text):
        timestamp = datetime.now().replace(microsecond=0).isoformat()
        self.log_text.configure(state="normal")
        self.log_text.insert("end", "[%s] %s\n" % (timestamp, text))
        self.log_text.configure(state="disabled")
        self.log_text.see("end")
        
def main():
    root = tk.Tk()
    root.title("Project Lurien")
    root.geometry("900x600")
    app = LurienApp(root)
    app.grid(row=0, column=0, sticky="nswe")
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    root.mainloop()

if __name__ == "__main__":
    main()
