import customtkinter
from concurrent.futures import Future, ThreadPoolExecutor
from GUI.captcha_window import CaptchaWindow
from Logic.data_file import DataClass
from Logic.parser import Parser
from json import load
from os.path import exists
from typing import Callable


class Connector:
    def __init__(self, master, data: DataClass, callback: Callable[[Future, str], None]):
        self.callback = callback
        self.data = data
        self.master = master

        self.captcha_code = customtkinter.StringVar()
        self.captcha_form: CaptchaWindow | None = None

    def connect(self):
        if not exists(self.data.passwords_file):
            self.master.event_generate("<<CreatePasswordsForm>>")
        else:
            with open(self.data.passwords_file, "r") as file:
                login_data = load(file)

            for website in self.data.websites_names:
                if website not in login_data:
                    self.master.event_generate("<<CreatePasswordsForm>>")
                    break
            else:
                self.connect_all()

    def reconnect(self):
        for website in self.data.logged_in_websites.keys():
            self.data.logged_in_websites[website] = False
        for parser in self.data.parsers:
            parser.logged_in = False
        self.master.event_generate("<<DeselectAllCheckboxes>>")
        self.connect()

    def connect_all(self):
        with open(self.data.passwords_file, "r") as file:
            login_data = load(file)

        with ThreadPoolExecutor() as executor:
            for parser in self.data.parsers:
                website_name = parser.__class__.__name__
                if not self.data.logged_in_websites[website_name]:
                    self.master.event_generate(f"<<StartProgressBar-{website_name}>>")

                    if website_name in self.data.websites_names_with_captcha_for_login:
                        self.master.event_generate(f"<<CreateCaptchaForm-{website_name}>>")
                        future = executor.submit(self.login_with_captcha_code,
                                                 parser=parser,
                                                 login=login_data[website_name]["login"],
                                                 password=login_data[website_name]["password"])
                        future.add_done_callback(lambda f, website=website_name: self.callback(f, website))
                    else:
                        future = executor.submit(parser.login_function,
                                                 login=login_data[website_name]["login"],
                                                 password=login_data[website_name]["password"])
                        future.add_done_callback(lambda f, website=website_name: self.callback(f, website))

    def create_captcha_form(self, website_name: str):
        self.captcha_form = CaptchaWindow(master=self.master, master_x=self.master.winfo_x(),
                                          master_y=self.master.winfo_y(), data=self.data, website_name=website_name,
                                          captcha_code=self.captcha_code)
        self.captcha_form.wait_visibility()

    def login_with_captcha_code(self, parser: Parser, login: str, password: str):
        self.captcha_form.wait_variable(self.captcha_code)
        return parser.login_function(login=login, password=password, captcha_code=self.captcha_code.get())
