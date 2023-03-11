import os, platform, subprocess, shutil, json, uuid, re, secrets
from datetime import datetime
import tkinter as tk
from tkinter.scrolledtext import ScrolledText



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
        self.ensure_user_consent()
        self.state = PeristentState()
    
    def ensure_user_consent(self):
        consent_popup = AgreementPopup(
            self,
            agree_callback=lambda: self.deiconify(),
            decline_callback=lambda: self.destroy()
        )
        self.withdraw()



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
        button = tk.Button(self, text=AGREE_BUTTON_TEXT)
        button.pack(fill="x")
        def agree():
            agree_callback()
            self.destroy()
        if agree_callback is not None:
            button.config(command=agree)
        if decline_callback is not None:
            self.protocol("WM_DELETE_WINDOW", decline_callback)



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
        self.state = self.read()
        print(self.state, self.path)
        if self.state is None:
            self.state = {
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
        with open(self.path, "w") as file:
            json.dump(self.state, file, indent="\t")



# ERRORS

class UnsupportedPlatformException(Exception):
    def __init__(self):            
        super().__init__("unsupported platform '%s'" % platform.system())


if __name__ == "__main__":
    main()
