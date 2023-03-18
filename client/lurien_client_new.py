import os, platform, subprocess, shutil, json, uuid, re, secrets, threading, queue, tempfile
import queue, time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import traceback



## TEXT CONSTANTS

USER_CONSENT_TEXT = """
╔═╗╦═╗╔═╗ ╦╔═╗╔═╗╔╦╗  ╦  ╦ ╦╦═╗╦╔═╗╔╗╔
╠═╝╠╦╝║ ║ ║║╣ ║   ║   ║  ║ ║╠╦╝║║╣ ║║║
╩  ╩╚═╚═╝╚╝╚═╝╚═╝ ╩   ╩═╝╚═╝╩╚═╩╚═╝╝╚╝

---

LURIEN CLIENT USER CONSENT

---

While the Lurien Client is running it will actively scan your HOLLOW KNIGHT and HOLLOW KNIGHT: SILKSONG save directories for updates. When save data updates are detected, it will automatically upload a copy of your save data to lurien.net to be a part of an anonymous dataset which we plan to release to the public for anyone to download and analyze. Our goal is to create an awesome data set that people can use to create cool infographics and insights.

If you have questions or concerns please email me with "LURIEN" in the topic.
luctowers@gmail.com

BY CLICKING THE BUTTON BELOW, YOU AGREE TO RELEASE ALL HOLLOW KNIGHT AND HOLLOW KNIGHT: SILKSONG SAVE DATA UPLOADED BY THIS CLIENT TO THE PUBLIC DOMAIN.
"""

AGREE_BUTTON_TEXT = "I AGREE, AND RELEASE MY SAVE DATA TO THE PUBLIC DOMAIN"



## ENTRY POINT

def main():
    App().mainloop()



#  MAIN APP

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Project Lurien")
        self.layout()
        self.state = PeristentState()
        if not self.state.data["consent"]:
            self.ensure_user_consent()
        elif self.register():
            self.start_worker()
        else:
            self.destroy()

    def layout(self):
        self.log_text = ScrolledText(self, padx=4, pady=4, wrap="word")
        self.log_text.config(state="disabled")
        self.log_text.pack()
    
    def ensure_user_consent(self):
        AgreementPopup(
            self,
            agree_callback=lambda: self.receive_user_consent(),
            decline_callback=lambda: self.destroy()
        )
        self.withdraw()
    
    def receive_user_consent(self):
        self.state.data["consent"] = True
        self.state.save()
        if self.register():
            self.deiconify()
            self.start_worker()
        else:
            self.destroy()
    
    def register(self):
        try:
            api_register(self.state.data["clientId"], self.state.data["clientSecret"])
            return True
        except Exception as e:
            self.withdraw()
            messagebox.showerror("Registration Exception", "Failed to register client: " + str(e))
            return False

    def start_worker(self):
        self.queue = queue.Queue()
        exit_event = threading.Event()
        def exit():
            exit_event.set()
            self.destroy()
        self.protocol("WM_DELETE_WINDOW", exit)
        worker_thread = threading.Thread(target=Worker(self.state, self.queue, exit_event))
        worker_thread.start()
        self.poll()
    
    def poll(self):
        try:
            while True:
                message = self.queue.get_nowait()
                self.log(message)
                self.queue.task_done()
        except queue.Empty:
            pass
        self.after(1000, self.poll)
    
    def log(self, text):
        timestamp = datetime.now().replace(microsecond=0).isoformat()
        self.log_text.configure(state="normal")
        self.log_text.insert("end", "[%s] %s\n" % (timestamp, text))
        self.log_text.configure(state="disabled")
        self.log_text.see("end")
        



# AUXILIARY WINDOWS

class AgreementPopup(tk.Toplevel):
    def __init__(self, parent, agree_callback=None, decline_callback=None):
        super().__init__(parent)
        self.title("Lurien Client: User Consent")
        self.resizable(False, False)
        text = ScrolledText(self, padx=24, pady=4, wrap="word")
        text.insert("end", USER_CONSENT_TEXT)
        text.config(state="disabled")
        text.pack()
        button = ttk.Button(self, text=AGREE_BUTTON_TEXT, padding=5)
        button.pack(padx=5, pady=5)
        self.bell()
        def agree():
            self.destroy()
            agree_callback()
        def decline():
            self.destroy()
            decline_callback()
        if agree_callback is not None:
            button.config(command=agree)
        if decline_callback is not None:
            self.protocol("WM_DELETE_WINDOW", decline)



# PERSISTENT STATE

class PeristentState:
    def __init__(self):
        if platform.system() == "Windows":
            dir = "~\\AppData\\LocalLow\\Lurien"
        elif platform.system() == "Darwin":
            dir = "~/Library/Application Support/net.lurien"
        else:
            raise UnsupportedPlatformException()
        dir = os.path.expanduser(dir)
        os.makedirs(dir, exist_ok=True)
        self.path = os.path.join(dir, "client.json")
        self.boostrap()
    
    def boostrap(self):
        self.data = self.read()
        if self.data is None:
            self.data = {
                "version": 1,
                "consent": False,
                "clientId": str(uuid.uuid4()),
                "clientSecret": secrets.token_urlsafe(32)
            }
            self.save()
    
    def read(self):
        try:
            with open(self.path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return None

    def save(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as file:
            json.dump(self.data, file, indent="\t")
        os.replace(file.name, self.path)



# WORKER



class Worker:

    def __init__(self, state: PeristentState, queue: queue.Queue, exit_event: threading.Event):
        self.state = state
        self.queue = queue
        self.exit_event = exit_event
        self.n = 0

    def __call__(self):
        self.run()

    def run(self):
        self.log("lurien is watching...")
        while True:
            self.n += 1
            self.log("yo%d" % self.n)
            if self.exit_event.wait(5):
                return
    
    def log(self, message):
        self.queue.put(message)



# API METHODS

def api_register(client_id, client_secret):
    print("API REGSITER id=%s secret=%s" % (client_id, client_secret))

def api_upload_save(client_id, client_secret, path, name):
    print("API UPLOAD id=%s secret=%s path=%s name=%s" % (client_id, client_secret, path, name))

def api_submit_survey(client_id, client_secret, survey):
    print("API UPLOAD id=%s secret=%s survey=%r" % (client_id, client_secret, survey))

def api_get_metadata():
    print("API GET METDATA")
    return {
        "games": {
            "hollowknight": {
                "include": [
                    r".+\.dat"
                ],
                "exclude": [
                    r".+_[0-9]+(\.[0-9]+)+\.dat"
                ]
            },
            "silksong": {
                "include": [
                    r".+\.dat"
                ],
                "exclude": [
                    r".+_[0-9]+(\.[0-9]+)+\.dat"
                ]
            }
        }
    }



# ERRORS

class UnsupportedPlatformException(Exception):
    def __init__(self):            
        super().__init__("unsupported platform '%s'" % platform.system())


if __name__ == "__main__":
    main()
