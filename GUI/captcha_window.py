import customtkinter


class CaptchaWindow(customtkinter.CTkToplevel):
    def __init__(self, master, website, website_index, logged_in_websites, login, password):
        super().__init__()

        self.master = master
        self.website = website
        self.website_name = website.__class__.__name__
        self.website_index = website_index
        self.logged_in_websites = logged_in_websites

        self.login = login
        self.password = password

        self.title(self.website_name)
        self.geometry("320x160")
        self.resizable(False, False)

        self.attributes("-topmost", "true")

        captcha = self.website.download_captcha()
        self.captcha = customtkinter.CTkImage(light_image=captcha, size=captcha.size)

        self.captcha_label_text = customtkinter.CTkLabel(self, text="Enter captcha code:")
        self.captcha_label_text.grid(row=2, column=0, padx=(20, 0), pady=(10, 0), sticky="w")

        self.captcha_input = customtkinter.CTkEntry(self)
        self.captcha_input.grid(row=2, column=1, padx=(20, 20), pady=(10, 0), sticky="nswe")

        self.captcha_label_img = customtkinter.CTkLabel(self, image=self.captcha, text="")
        self.captcha_label_img.grid(row=3, column=0, padx=(20, 0), pady=(10, 10), columnspan=2)

        self.login_button = customtkinter.CTkButton(self, text="Log in", command=self.login_with_captcha)
        self.login_button.grid(column=0, padx=(20, 20), pady=(10, 10), columnspan=2)

    def login_with_captcha(self):
        captcha_code = self.captcha_input.get()
        status = self.website.login_function(self.login, self.password, captcha_code)

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
