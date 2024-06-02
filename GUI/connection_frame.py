from concurrent.futures import ThreadPoolExecutor
from GUI import login_window, passwords_window
from json import load
from os.path import exists
from threading import Thread


class ConnectionFrame:
    def __init__(self, master, websites_list_frame):
        self.master = master
        self.websites_list_frame = websites_list_frame

        self.login_buttons = []
        self.login_form = None
        self.passwords_form = None

        self.passwords_file = "passwords.json"

    def login(self, website, login, password):
        if self.login_form is None or not self.login_form.winfo_exists():
            self.login_form = login_window.LoginWindow(self.master, website,
                                                       self.websites_list_frame.websites.index(website),
                                                       self.websites_list_frame.logged_in_websites, login, password)
            self.login_form.grab_set()
        else:
            self.login_form.focus()

    def connect(self):
        if not exists(self.passwords_file):
            if self.passwords_form is None or not self.passwords_form.winfo_exists():
                self.passwords_form = passwords_window.PasswordsWindow(self.master,
                                                                       self.websites_list_frame.websites_names,
                                                                       self.passwords_file)
                self.passwords_form.grab_set()
            else:
                self.passwords_form.focus()

            self.master.event_generate("<<EnableConnectionButton>>")
        else:
            thread = Thread(target=self.connect_all, daemon=True)
            thread.start()

    def callback(self, future, number):
        self.master.event_generate(f"<<StopProgressBar-{number}>>")

        status = future.result()
        if status == "Time error":
            self.master.event_generate(f"<<ReportErrorTime-{self.websites_list_frame.websites_names[number]}>>")
        elif status == "Login error":
            self.master.event_generate(f"<<ReportErrorLogin-{self.websites_list_frame.websites_names[number]}>>")
        elif status == "Connection error":
            self.master.event_generate(f"<<ReportErrorConnection-{self.websites_list_frame.websites_names[number]}>>")
        else:
            self.websites_list_frame.logged_in_websites[number] = True
            self.master.event_generate(f"<<SelectCheckBox-{number}>>")

    def connect_all(self):
        with open(self.passwords_file, "r") as file:
            login_data = load(file)

        with ThreadPoolExecutor() as executor:
            for i, website in enumerate(self.websites_list_frame.websites):
                if not self.websites_list_frame.logged_in_websites[i]:
                    self.master.event_generate(f"<<StartProgressBar-{i}>>")

                    if website.__class__.__name__ == "Dasi":
                        self.master.event_generate("<<LoginDasi>>")
                    else:
                        future = executor.submit(website.login_function,
                                                 login_data[website.__class__.__name__]["login"],
                                                 login_data[website.__class__.__name__]["password"])
                        future.add_done_callback(lambda f, number=i: self.callback(f, number))

        self.master.event_generate("<<EnableConnectionButton>>")

    def reconnect(self):
        for i, website in enumerate(self.websites_list_frame.websites):
            if not self.websites_list_frame.logged_in_websites[i]:
                self.master.event_generate(f"<<StartProgressBar-{i}>>")
                self.login(website, login=self.websites_list_frame.login_data[website.__class__.__name__]["login"],
                           password=self.websites_list_frame.login_data[website.__class__.__name__]["password"])

        self.master.event_generate("<<EnableConnectionButton>>")
