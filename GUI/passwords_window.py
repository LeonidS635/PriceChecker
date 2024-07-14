import customtkinter
import ctypes
from json import dump, load
from Logic.data_file import DataClass
from os.path import exists


class PasswordsWindow(customtkinter.CTkToplevel):
    def __init__(self, data: DataClass, passwords_file: str):
        super().__init__(data.master)

        self.data = data
        self.passwords_file = passwords_file

        login_data = {}
        if exists(self.passwords_file):
            with open(self.passwords_file, "r") as file:
                login_data = load(file)

        self.title("Login data")
        self.geometry(f"600x{len(self.data.websites_names) * 40 + 55}")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.confirm)
        self.attributes("-topmost", "true")

        self.logins = []
        self.passwords = []

        login_label = customtkinter.CTkLabel(self, text="Login", justify=customtkinter.CENTER)
        login_label.grid(row=0, column=1, padx=(10, 10), pady=(5, 5), sticky="ew")

        password_label = customtkinter.CTkLabel(self, text="Password", justify=customtkinter.CENTER)
        password_label.grid(row=0, column=2, padx=(10, 10), pady=(5, 5), sticky="ew")

        for i, website_name in enumerate(self.data.websites_names):
            website_label = customtkinter.CTkLabel(self, text=website_name)
            website_label.grid(row=i + 1, column=0, padx=(10, 10), pady=(5, 5), sticky="w")

            if website_name in login_data.keys():
                login_input = customtkinter.CTkEntry(self, placeholder_text="login", width=220,
                                                     textvariable=customtkinter.StringVar(
                                                         self, value=login_data[website_name]["login"]))
                password_input = customtkinter.CTkEntry(self, placeholder_text="password", width=220,
                                                        textvariable=customtkinter.StringVar(
                                                            self, value=login_data[website_name]["password"]))
            else:
                login_input = customtkinter.CTkEntry(self, placeholder_text="login", width=220)
                password_input = customtkinter.CTkEntry(self, placeholder_text="password", width=220)

            login_input.grid(row=i + 1, column=1, padx=(10, 10), pady=(5, 5), sticky="nswe")
            login_input.bind("<Control-KeyPress>", self.keypress)

            password_input.grid(row=i + 1, column=2, padx=(10, 10), pady=(5, 5), sticky="nswe")
            password_input.bind("<Control-KeyPress>", self.keypress)

            self.logins.append(login_input)
            self.passwords.append(password_input)

        self.confirm_button = customtkinter.CTkButton(self, text="Confirm", command=self.confirm)
        self.confirm_button.grid(column=0, padx=(20, 20), pady=(10, 10), columnspan=3)

    @staticmethod
    def keypress(event):
        def is_ru_lang():
            user = ctypes.windll.LoadLibrary("user32.dll")
            return hex(getattr(user, "GetKeyboardLayout")(0)) == "0x4190419"

        if is_ru_lang():
            if event.keycode == 86:
                event.widget.event_generate("<<Paste>>")
            if event.keycode == 67:
                event.widget.event_generate("<<Copy>>")
            if event.keycode == 88:
                event.widget.event_generate("<<Cut>>")

    def confirm(self):
        data = {}
        for i, website_name in enumerate(self.data.websites_names):
            login = self.logins[i].get()
            password = self.passwords[i].get()
            data[website_name] = {"login": login, "password": password}

        with open(self.passwords_file, "w") as file:
            dump(data, file, indent=4)

        self.destroy()
