import customtkinter
import ctypes


class LoginWindow(customtkinter.CTkToplevel):
    def __init__(self, master, website, website_index, logged_in_websites, login, password):
        super().__init__()

        self.master = master
        self.website = website
        self.website_name = website.__class__.__name__
        self.website_index = website_index
        self.logged_in_websites = logged_in_websites

        self.title(self.website_name)
        self.geometry("400x220")
        self.resizable(False, False)

        self.attributes("-topmost", "true")

        self.login_label = customtkinter.CTkLabel(self, text="Enter login:")
        self.login_label.grid(row=0, column=0, padx=(20, 0), pady=(10, 0), sticky="w")

        self.login_input = customtkinter.CTkEntry(self, textvariable=customtkinter.StringVar(self, value=login),
                                                  width=220)
        self.login_input.grid(row=0, column=1, padx=(20, 20), pady=(10, 0), sticky="nswe")
        self.login_input.bind("<Control-KeyPress>", self.keypress)
        self.login_input.bind("<Return>", self.login)

        self.password_label = customtkinter.CTkLabel(self, text="Enter password:")
        self.password_label.grid(row=1, column=0, padx=(20, 0), pady=(10, 0), sticky="w")

        self.password_input = customtkinter.CTkEntry(self, textvariable=customtkinter.StringVar(self, value=password))
        self.password_input.grid(row=1, column=1, padx=(20, 20), pady=(10, 0), sticky="nswe")
        self.password_input.bind("<Control-KeyPress>", self.keypress)
        self.password_input.bind("<Return>", self.login)

        self.rowconfigure(3, weight=1)

        if self.website_name == "Dasi":
            captcha = self.website.download_captcha()
            self.captcha = customtkinter.CTkImage(light_image=captcha, size=captcha.size)

            self.captcha_label_text = customtkinter.CTkLabel(self, text="Enter captcha code:")
            self.captcha_label_text.grid(row=2, column=0, padx=(20, 0), pady=(10, 0), sticky="w")

            self.captcha_input = customtkinter.CTkEntry(self)
            self.captcha_input.grid(row=2, column=1, padx=(20, 20), pady=(10, 0), sticky="nswe")
            self.captcha_input.bind("<Control-KeyPress>", self.keypress)
            self.captcha_input.bind("<Return>", self.login)

            self.captcha_label_img = customtkinter.CTkLabel(self, image=self.captcha, text="")
            self.captcha_label_img.grid(row=3, column=0, padx=(20, 0), pady=(10, 10), columnspan=2)

        self.login_button = customtkinter.CTkButton(self, text="Log in", command=self.login)
        self.login_button.grid(column=0, padx=(20, 20), pady=(10, 10), columnspan=2)

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

    def login(self, _=None):
        login = self.login_input.get()
        password = self.password_input.get()

        if self.website_name == "Dasi":
            captcha_code = self.captcha_input.get()
            status = self.website.login_function(login, password, captcha_code)
        else:
            status = self.website.login_function(login, password)

        self.master.event_generate(f"<<StopProgressBar-{self.website_index}>>")

        if status == "OK":
            self.logged_in_websites[self.website_index] = True
            self.master.event_generate(f"<<SelectCheckBox-{self.website_index}>>")
            self.destroy()
        else:
            self.destroy()

            if status == "Time error":
                self.master.event_generate(f"<<ReportErrorTime-{self.website_name}>>")
            elif status == "Login error":
                self.master.event_generate(f"<<ReportErrorLogin-{self.website_name}>>")
            elif status == "Connection error":
                self.master.event_generate(f"<<ReportErrorConnection-{self.website_name}>>")
