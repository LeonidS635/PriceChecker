from concurrent.futures import Future, ThreadPoolExecutor
from Logic.data_file import DataClass
from GUI import captcha_window, passwords_window
from GUI.frames import Frames
from json import load
from os.path import exists
from typing import Callable


class Connector:
    def __init__(self, data: DataClass, frames: Frames, callback: Callable[[Future, int], None]):
        self.callback = callback
        self.data = data
        self.frames = frames

        self.captcha_form = None
        self.passwords_form = None

        self.passwords_file = "passwords.json"

    def connect(self):
        if not exists(self.passwords_file):
            if self.passwords_form is None or not self.passwords_form.winfo_exists():
                self.passwords_form = passwords_window.PasswordsWindow(self.data, self.passwords_file)
                self.passwords_form.grab_set()
            else:
                self.passwords_form.focus()
        else:
            self.connect_all()

    def reconnect(self):
        self.data.logged_in_websites = [False for _ in range(len(self.data.logged_in_websites))]
        self.frames.websites_list_frame.deselect_checkboxes()
        self.connect()

    def connect_all(self):
        with open(self.passwords_file, "r") as file:
            login_data = load(file)

        with ThreadPoolExecutor() as executor:
            for i, parser in enumerate(self.data.parsers):
                if not self.data.logged_in_websites[i]:
                    self.data.master.event_generate(f"<<StartProgressBar-{i}>>")

                    if self.data.websites_names[i] == "Dasi":
                        self.data.master.event_generate("<<LoginDasi>>")
                    else:
                        future = executor.submit(parser.login_function,
                                                 login_data[self.data.websites_names[i]]["login"],
                                                 login_data[self.data.websites_names[i]]["password"])
                        future.add_done_callback(lambda f, number=i: self.callback(f, number))

    def login_with_captcha(self, website_name):
        with open(self.passwords_file, "r") as file:
            login_data = load(file)

        login = login_data[website_name]["login"]
        password = login_data[website_name]["password"]
        website_index = self.data.websites_names.index(website_name)

        if self.captcha_form is None or not self.captcha_form.winfo_exists():
            self.captcha_form = captcha_window.CaptchaWindow(data=self.data, frames=self.frames,
                                                             website_index=website_index, login=login,
                                                             password=password)
            self.captcha_form.grab_set()
        else:
            self.captcha_form.focus()
